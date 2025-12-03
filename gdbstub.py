#!/usr/bin/env python3
"""
GDB Remote Serial Protocol (RSP) stub for RISC-V Python emulator.

This module implements a GDB remote stub that allows debugging RISC-V
programs using the GDB debugger over a TCP connection.

The implementation follows the GDB Remote Serial Protocol specification:
https://sourceware.org/gdb/current/onlinedocs/gdb/Remote-Protocol.html
"""

import socket
import logging
from typing import Optional


class GDBPacket:
    """Helper class for GDB packet parsing and formatting.

    GDB RSP uses packet format: $packet-data#checksum
    where checksum is 2 hex digits representing sum of packet-data bytes & 0xFF.
    """

    @staticmethod
    def checksum(data: str) -> int:
        """Calculate GDB packet checksum.

        Args:
            data: Packet data string

        Returns:
            Checksum as integer (0-255)
        """
        return sum(ord(c) for c in data) & 0xFF

    @staticmethod
    def escape(data: str) -> str:
        """Escape special characters in GDB packet.

        Characters #, $, }, * are escaped by prepending } and XORing with 0x20.

        Args:
            data: Data to escape

        Returns:
            Escaped data string
        """
        result = ""
        for c in data:
            if c in ['#', '$', '}', '*']:
                result += '}' + chr(ord(c) ^ 0x20)
            else:
                result += c
        return result

    @staticmethod
    def unescape(data: str) -> str:
        """Unescape special characters in GDB packet.

        Characters escaped with } are XORed with 0x20 to get original.

        Args:
            data: Data to unescape

        Returns:
            Unescaped data string
        """
        result = ""
        i = 0
        while i < len(data):
            if data[i] == '}' and i + 1 < len(data):
                # Next character is escaped - XOR with 0x20
                result += chr(ord(data[i + 1]) ^ 0x20)
                i += 2
            else:
                result += data[i]
                i += 1
        return result

    @staticmethod
    def encode(data: str) -> str:
        """Encode data into GDB packet format: $data#checksum

        Escapes special characters before calculating checksum.

        Args:
            data: Data to encode

        Returns:
            Formatted packet string with escaped data
        """
        escaped = GDBPacket.escape(data)
        cs = GDBPacket.checksum(escaped)
        return f"${escaped}#{cs:02x}"

    @staticmethod
    def decode(packet: str) -> Optional[str]:
        """Decode GDB packet, return data or None if invalid.

        Args:
            packet: Raw packet string

        Returns:
            Unescaped packet data if valid, None otherwise
        """
        if not packet.startswith('$'):
            return None
        if '#' not in packet:
            return None

        try:
            data, checksum_str = packet[1:].split('#', 1)
            expected_cs = int(checksum_str[:2], 16)
            actual_cs = GDBPacket.checksum(data)

            if expected_cs != actual_cs:
                return None
            # Unescape the data after checksum validation
            return GDBPacket.unescape(data)
        except (ValueError, IndexError):
            return None


class GDBSignals:
    """GDB signal numbers for stop replies."""

    SIGINT = 2   # Interrupt (Ctrl+C)
    SIGILL = 4   # Illegal instruction
    SIGTRAP = 5  # Breakpoint/single-step
    SIGSEGV = 11 # Segmentation fault

    @staticmethod
    def from_trap_cause(cause: int) -> int:
        """Map RISC-V trap cause to GDB signal number.

        Args:
            cause: RISC-V mcause value

        Returns:
            GDB signal number
        """
        if cause == 2:  # Illegal instruction
            return GDBSignals.SIGILL
        elif cause == 3:  # Breakpoint (EBREAK)
            return GDBSignals.SIGTRAP
        elif cause in [0, 1, 5, 7]:  # Access faults
            return GDBSignals.SIGSEGV
        else:
            return GDBSignals.SIGTRAP  # Default


class GDBStub:
    """GDB Remote Serial Protocol handler for RISC-V emulator.

    This class implements the GDB remote protocol, handling commands from
    GDB to control execution, inspect and modify registers/memory, and
    manage breakpoints.

    Attributes:
        cpu: CPU instance
        ram: RAM instance
        machine: Machine instance
        logger: Optional logger
        sw_breakpoints: Set of software breakpoint addresses
        running: Whether execution is active
        single_step: Whether in single-step mode
        last_signal: Last signal number for stop reply
    """

    def __init__(self, cpu, ram, machine=None, logger=None, debug_protocol=False):
        """Initialize GDB stub.

        Args:
            cpu: CPU instance
            ram: RAM instance
            machine: Optional Machine instance
            logger: Optional logger
            debug_protocol: If True, log all GDB packet exchanges (verbose)
        """
        self.cpu = cpu
        self.ram = ram
        self.machine = machine
        self.logger = logger or logging.getLogger(__name__)
        self.debug_protocol = debug_protocol

        # Connection management
        self.socket: Optional[socket.socket] = None
        self.client_socket: Optional[socket.socket] = None
        self.client_addr = None

        # Execution state
        self.running = False
        self.single_step = False
        self.last_signal = GDBSignals.SIGTRAP

        # Breakpoint management
        self.sw_breakpoints = set()  # Software breakpoint addresses

        # GDB register order for RISC-V
        # 0-31: x0-x31 (GPRs)
        # 32: PC
        # 65-4160: CSRs (65 + CSR_address)
        # For example: mstatus (0x300) = register 65 + 0x300 = 833
        self.num_regs = 33
        self.csr_base = 65  # CSR registers start at GDB register 65

        # Map of important CSR addresses for quick access
        self.important_csrs = {
            0x300: 'mstatus',
            0x301: 'misa',
            0x304: 'mie',
            0x305: 'mtvec',
            0x340: 'mscratch',
            0x341: 'mepc',
            0x342: 'mcause',
            0x343: 'mtval',
            0x344: 'mip',
            0x7C0: 'mtime_low',
            0x7C1: 'mtime_high',
            0x7C2: 'mtimecmp_low',
            0x7C3: 'mtimecmp_high',
        }

    def listen(self, port: int = 1234, host: str = 'localhost'):
        """Start TCP server and wait for GDB connection.

        Args:
            port: TCP port to listen on
            host: Host address to bind to
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((host, port))
        self.socket.listen(1)

        self.logger.info(f"GDB stub listening on {host}:{port}")

        self.client_socket, self.client_addr = self.socket.accept()
        self.logger.info(f"GDB connected from {self.client_addr}")

        # Set socket to blocking mode for simplicity
        self.client_socket.setblocking(True)

    def close(self):
        """Close GDB connection and server socket."""
        if self.client_socket:
            self.client_socket.close()
            self.client_socket = None
        if self.socket:
            self.socket.close()
            self.socket = None

    def send_packet(self, data: str):
        """Send GDB packet to client.

        Args:
            data: Packet data to send
        """
        packet = GDBPacket.encode(data)
        if self.debug_protocol:
            self.logger.debug(f"GDB >> {packet}")
        self.client_socket.sendall(packet.encode('ascii'))

    def check_for_interrupt(self) -> bool:
        """Check if interrupt (Ctrl+C) has been received from GDB.

        Uses non-blocking check to see if 0x03 byte is available.

        Returns:
            True if interrupt received, False otherwise
        """
        import select
        import socket as sock_module

        try:
            # Check if data is available without blocking (0 second timeout)
            ready, _, _ = select.select([self.client_socket], [], [], 0)
            if ready:
                # Set socket to non-blocking temporarily
                old_blocking = self.client_socket.gettimeout()
                self.client_socket.settimeout(0.0)

                try:
                    # Peek at the next byte
                    data = self.client_socket.recv(1, sock_module.MSG_PEEK)
                    if data and data[0] == 0x03:  # 0x03 is Ctrl+C (ETX)
                        # Consume the interrupt byte
                        self.client_socket.recv(1)
                        self.logger.info("GDB interrupt received (Ctrl+C)")
                        return True
                except BlockingIOError:
                    # No data available
                    pass
                except socket.error:
                    pass
                finally:
                    # Restore original timeout
                    if old_blocking is None:
                        self.client_socket.setblocking(True)
                    else:
                        self.client_socket.settimeout(old_blocking)
        except Exception as e:
            self.logger.warning(f"Error checking for interrupt: {e}")

        return False

    def recv_packet(self) -> Optional[str]:
        """Receive and parse GDB packet from client.

        Returns:
            Packet data if valid, 'interrupt' for Ctrl+C, None on connection close
        """
        buffer = ""
        in_packet = False
        while True:
            try:
                char = self.client_socket.recv(1).decode('ascii')
            except (ConnectionResetError, BrokenPipeError):
                return None

            if not char:
                return None

            # Handle interrupt (Ctrl+C)
            if char == '\x03':
                self.logger.debug("GDB received interrupt (Ctrl+C)")
                return 'interrupt'

            # Skip ACK/NACK characters only when NOT inside a packet
            # (they can be valid data characters inside packets)
            if not in_packet and char in ['+', '-']:
                continue

            # Start of packet
            if char == '$':
                in_packet = True
                buffer = char
                continue

            # Accumulate packet data
            if in_packet:
                buffer += char

                if char == '#':
                    # Read 2-char checksum
                    try:
                        buffer += self.client_socket.recv(2).decode('ascii')
                    except (ConnectionResetError, BrokenPipeError):
                        return None

                    data = GDBPacket.decode(buffer)

                    if data is not None:
                        if self.debug_protocol:
                            self.logger.debug(f"GDB << {buffer}")
                        # Send ACK
                        self.client_socket.sendall(b'+')
                        in_packet = False
                        return data
                    else:
                        self.logger.warning(f"GDB packet checksum error: {buffer}")
                        # Send NACK
                        self.client_socket.sendall(b'-')
                        buffer = ""
                        in_packet = False

    def handle_command(self, cmd: str) -> Optional[str]:
        """Process GDB command and return response.

        Args:
            cmd: Command string from GDB

        Returns:
            Response string, or None if command starts execution
        """
        # '?' - Get halt reason
        if cmd == '?':
            return self.cmd_halt_reason()

        # 'g' - Read all registers
        elif cmd == 'g':
            return self.cmd_read_registers()

        # 'G<hex>' - Write all registers
        elif cmd.startswith('G'):
            return self.cmd_write_registers(cmd[1:])

        # 'p<n>' - Read register n
        elif cmd.startswith('p'):
            return self.cmd_read_register(cmd[1:])

        # 'P<n>=<hex>' - Write register n
        elif cmd.startswith('P'):
            return self.cmd_write_register(cmd[1:])

        # 'm<addr>,<len>' - Read memory
        elif cmd.startswith('m'):
            return self.cmd_read_memory(cmd[1:])

        # 'M<addr>,<len>:<hex>' - Write memory
        elif cmd.startswith('M'):
            return self.cmd_write_memory(cmd[1:])

        # 'c' or 'c<addr>' - Continue
        elif cmd.startswith('c'):
            return self.cmd_continue(cmd[1:] if len(cmd) > 1 else None)

        # 's' or 's<addr>' - Single step
        elif cmd.startswith('s'):
            return self.cmd_step(cmd[1:] if len(cmd) > 1 else None)

        # 'Z0,<addr>,<kind>' - Insert software breakpoint
        elif cmd.startswith('Z0,'):
            return self.cmd_insert_breakpoint(cmd[3:])

        # 'z0,<addr>,<kind>' - Remove software breakpoint
        elif cmd.startswith('z0,'):
            return self.cmd_remove_breakpoint(cmd[3:])

        # 'qSupported' - Feature negotiation
        elif cmd.startswith('qSupported'):
            return self.cmd_supported(cmd)

        # 'qAttached' - Query if attached to existing process
        elif cmd == 'qAttached':
            return '1'  # We're attached

        # 'qC' - Query current thread ID
        elif cmd == 'qC':
            return 'QC0'  # Thread 0 (single-threaded)

        # 'qfThreadInfo' - Query thread info (first)
        elif cmd == 'qfThreadInfo':
            return 'm0'  # One thread: ID 0

        # 'qsThreadInfo' - Query thread info (subsequent)
        elif cmd == 'qsThreadInfo':
            return 'l'  # End of list

        # 'qOffsets' - Query section offsets
        elif cmd == 'qOffsets':
            return 'Text=0;Data=0;Bss=0'

        # 'qRcmd,<hex>' - Monitor command
        elif cmd.startswith('qRcmd,'):
            return self.cmd_monitor(cmd[6:])

        # 'vCont?' - Query vCont support
        elif cmd == 'vCont?':
            return 'vCont;c;s'  # Support continue and step

        # 'vCont;c' - Continue (extended)
        elif cmd == 'vCont;c' or cmd == 'vCont;c:0':
            return self.cmd_continue(None)

        # 'vCont;s' - Step (extended)
        elif cmd == 'vCont;s' or cmd == 'vCont;s:0':
            return self.cmd_step(None)

        # 'k' - Kill
        elif cmd == 'k':
            self.logger.info("GDB requested kill")
            from machine import ExecutionTerminated
            raise ExecutionTerminated("Killed by GDB")

        # 'D' - Detach
        elif cmd == 'D':
            self.logger.info("GDB detached")
            return 'OK'

        # Unknown command - return empty response
        else:
            if self.debug_protocol:
                self.logger.debug(f"GDB unknown command: {cmd}")
            return ''

    # Command implementations

    def cmd_halt_reason(self) -> str:
        """Return last halt reason as stop reply packet."""
        return f"S{self.last_signal:02x}"

    def cmd_read_registers(self) -> str:
        """Read all 33 registers (x0-x31 + PC) in GDB order.

        Returns:
            Hex string with all register values (little-endian byte order)
            For RV32, sends 32-bit values (4 bytes each)
        """
        result = ""
        # x0-x31
        for i in range(32):
            val = self.cpu.registers[i] & 0xFFFFFFFF
            # Little-endian byte encoding: encode each byte LSB first
            # 32-bit value = 4 bytes = 8 hex chars
            result += f"{val & 0xFF:02x}{(val >> 8) & 0xFF:02x}{(val >> 16) & 0xFF:02x}{(val >> 24) & 0xFF:02x}"
        # PC (register 32)
        pc = self.cpu.pc & 0xFFFFFFFF
        result += f"{pc & 0xFF:02x}{(pc >> 8) & 0xFF:02x}{(pc >> 16) & 0xFF:02x}{(pc >> 24) & 0xFF:02x}"
        return result

    def cmd_write_registers(self, hex_data: str) -> str:
        """Write all registers from hex string.

        Args:
            hex_data: Hex string with register values (little-endian byte order)
                     For RV32: 32-bit values (8 hex chars per register)

        Returns:
            'OK' on success, error code on failure
        """
        try:
            # Each register is 8 hex chars (4 bytes, little-endian) for RV32
            reg_size = 8

            for i in range(32):
                offset = i * reg_size
                # Parse little-endian bytes (32 bits)
                b0 = int(hex_data[offset:offset+2], 16)
                b1 = int(hex_data[offset+2:offset+4], 16)
                b2 = int(hex_data[offset+4:offset+6], 16)
                b3 = int(hex_data[offset+6:offset+8], 16)
                val = b0 | (b1 << 8) | (b2 << 16) | (b3 << 24)
                if i != 0:  # x0 is hardwired to zero
                    self.cpu.registers[i] = val & 0xFFFFFFFF

            # PC (little-endian, 32 bits)
            offset = 32 * reg_size
            b0 = int(hex_data[offset:offset+2], 16)
            b1 = int(hex_data[offset+2:offset+4], 16)
            b2 = int(hex_data[offset+4:offset+6], 16)
            b3 = int(hex_data[offset+6:offset+8], 16)
            pc = b0 | (b1 << 8) | (b2 << 16) | (b3 << 24)
            self.cpu.pc = pc & 0xFFFFFFFF
            self.cpu.next_pc = self.cpu.pc

            return 'OK'
        except (ValueError, IndexError):
            return 'E01'

    def cmd_read_register(self, reg_num_str: str) -> str:
        """Read single register.

        Args:
            reg_num_str: Register number as hex string

        Returns:
            Register value as hex string (little-endian byte order), or error code
            For RV32: 32-bit value (4 bytes = 8 hex chars)
        """
        try:
            reg_num = int(reg_num_str, 16)
            if reg_num < 32:
                # General purpose registers
                val = self.cpu.registers[reg_num] & 0xFFFFFFFF
            elif reg_num == 32:
                # Program counter
                val = self.cpu.pc & 0xFFFFFFFF
            elif reg_num >= self.csr_base:
                # CSR registers: reg_num = 65 + CSR_address
                csr_addr = reg_num - self.csr_base
                if csr_addr < 4096:
                    val = self.cpu.csrs[csr_addr] & 0xFFFFFFFF
                    self.logger.debug(f"Read CSR 0x{csr_addr:03x} = 0x{val:08x}")
                else:
                    return 'E01'
            else:
                return 'E01'
            # Little-endian byte encoding (32-bit for RV32)
            result = f"{val & 0xFF:02x}{(val >> 8) & 0xFF:02x}{(val >> 16) & 0xFF:02x}{(val >> 24) & 0xFF:02x}"
            return result
        except ValueError:
            return 'E01'

    def cmd_write_register(self, params: str) -> str:
        """Write single register.

        Args:
            params: Register number and value (format: n=value, little-endian byte order)
                   For riscv64-gdb: 64-bit value (lower 32 bits used for RV32)

        Returns:
            'OK' on success, error code on failure
        """
        try:
            reg_num_str, val_str = params.split('=')
            reg_num = int(reg_num_str, 16)

            # Parse value as little-endian bytes (lower 32 bits only for RV32)
            if len(val_str) >= 8:
                b0 = int(val_str[0:2], 16)
                b1 = int(val_str[2:4], 16)
                b2 = int(val_str[4:6], 16)
                b3 = int(val_str[6:8], 16)
                val = b0 | (b1 << 8) | (b2 << 16) | (b3 << 24)
            else:
                # Handle shorter values
                val = int(val_str, 16)

            if reg_num == 0:
                return 'OK'  # x0 is hardwired to zero
            elif reg_num < 32:
                self.cpu.registers[reg_num] = val & 0xFFFFFFFF
            elif reg_num == 32:
                self.cpu.pc = val & 0xFFFFFFFF
                self.cpu.next_pc = self.cpu.pc
            elif reg_num >= self.csr_base:
                # CSR registers: reg_num = 65 + CSR_address
                csr_addr = reg_num - self.csr_base
                if csr_addr < 4096:
                    # Check if CSR is read-only
                    if hasattr(self.cpu, 'CSR_RO') and csr_addr in self.cpu.CSR_RO:
                        self.logger.warning(f"Attempted write to read-only CSR 0x{csr_addr:03x}")
                        return 'E02'  # Error: read-only register
                    self.cpu.csrs[csr_addr] = val & 0xFFFFFFFF
                    self.logger.debug(f"Write CSR 0x{csr_addr:03x} = 0x{val:08x}")
                else:
                    return 'E01'
            else:
                return 'E01'
            return 'OK'
        except (ValueError, IndexError):
            return 'E01'

    def cmd_read_memory(self, params: str) -> str:
        """Read memory: m<addr>,<len>

        Args:
            params: Address and length (format: addr,len)

        Returns:
            Memory contents as hex string, or error code
        """
        try:
            addr_str, len_str = params.split(',')
            addr = int(addr_str, 16)
            length = int(len_str, 16)

            result = ""
            for i in range(length):
                byte = self.ram.load_byte(addr + i, signed=False)
                result += f"{byte:02x}"
            return result
        except Exception as e:
            self.logger.warning(f"Memory read failed: {e}")
            return 'E01'

    def cmd_write_memory(self, params: str) -> str:
        """Write memory: M<addr>,<len>:<hex>

        Args:
            params: Address, length, and data (format: addr,len:data)

        Returns:
            'OK' on success, error code on failure
        """
        try:
            addr_len, hex_data = params.split(':')
            addr_str, len_str = addr_len.split(',')
            addr = int(addr_str, 16)
            length = int(len_str, 16)

            if len(hex_data) < length * 2:
                return 'E01'

            for i in range(length):
                byte_str = hex_data[i*2:(i+1)*2]
                byte = int(byte_str, 16)
                self.ram.store_byte(addr + i, byte)

            return 'OK'
        except Exception as e:
            self.logger.warning(f"Memory write failed: {e}")
            return 'E01'

    def cmd_continue(self, addr_str: Optional[str]) -> Optional[str]:
        """Continue execution (optionally from specified address).

        Args:
            addr_str: Optional address to continue from

        Returns:
            None (will return stop reply after execution)
        """
        if addr_str:
            try:
                addr = int(addr_str, 16)
                self.cpu.pc = addr & 0xFFFFFFFF
                self.cpu.next_pc = self.cpu.pc
            except ValueError:
                return 'E01'

        self.running = True
        self.single_step = False
        return None  # Will return stop reply after execution

    def cmd_step(self, addr_str: Optional[str]) -> Optional[str]:
        """Single step (optionally from specified address).

        Args:
            addr_str: Optional address to step from

        Returns:
            None (will return stop reply after single step)
        """
        if addr_str:
            try:
                addr = int(addr_str, 16)
                self.cpu.pc = addr & 0xFFFFFFFF
                self.cpu.next_pc = self.cpu.pc
            except ValueError:
                return 'E01'

        self.running = True
        self.single_step = True
        return None  # Will return stop reply after single step

    def cmd_insert_breakpoint(self, params: str) -> str:
        """Insert software breakpoint: Z0,<addr>,<kind>

        Args:
            params: Address and kind (format: addr,kind)

        Returns:
            'OK' on success, error code on failure
        """
        try:
            parts = params.split(',')
            addr = int(parts[0], 16)
            # kind is ignored for RISC-V (instruction length determined by inst)

            self.sw_breakpoints.add(addr)
            self.logger.info(f"Breakpoint inserted at 0x{addr:08x}")
            return 'OK'
        except (ValueError, IndexError):
            return 'E01'

    def cmd_remove_breakpoint(self, params: str) -> str:
        """Remove software breakpoint: z0,<addr>,<kind>

        Args:
            params: Address and kind (format: addr,kind)

        Returns:
            'OK' on success, error code on failure
        """
        try:
            parts = params.split(',')
            addr = int(parts[0], 16)

            self.sw_breakpoints.discard(addr)
            self.logger.info(f"Breakpoint removed at 0x{addr:08x}")
            return 'OK'
        except (ValueError, IndexError):
            return 'E01'

    def cmd_supported(self, cmd: str) -> str:
        """Feature negotiation.

        Args:
            cmd: qSupported command with client features

        Returns:
            Server features string
        """
        # Report basic features
        features = [
            'PacketSize=4096',
            'swbreak+',  # Software breakpoints supported
            'hwbreak-',  # Hardware breakpoints not supported
            'qRelocInsn-',
            'vContSupported+'
        ]
        return ';'.join(features)

    def is_breakpoint(self, addr: int) -> bool:
        """Check if address has a breakpoint.

        Args:
            addr: Address to check

        Returns:
            True if breakpoint exists at address
        """
        return addr in self.sw_breakpoints

    def stop_reply(self, signal: int) -> str:
        """Format stop reply packet.

        Args:
            signal: GDB signal number

        Returns:
            Stop reply packet string
        """
        self.last_signal = signal
        return f"S{signal:02x}"

    def cmd_monitor(self, hex_cmd: str) -> str:
        """Handle monitor commands from GDB.

        Args:
            hex_cmd: Command string encoded in hex

        Returns:
            Response string (hex-encoded output)
        """
        try:
            # Decode hex command
            cmd = bytes.fromhex(hex_cmd).decode('ascii').strip()
            self.logger.debug(f"Monitor command: {cmd}")

            parts = cmd.split()
            if not parts:
                return self._encode_hex("Unknown command\n")

            # Handle CSR commands
            if parts[0] == 'csr':
                if len(parts) < 2:
                    output = "Usage: csr <name|0xADDR> [value]\n"
                    output += "CSRs: mstatus misa mie mtvec mscratch mepc mcause mtval mip\n"
                    return self._encode_hex(output)

                # Parse CSR address/name
                csr_arg = parts[1]
                if csr_arg.startswith('0x'):
                    csr_addr = int(csr_arg, 16)
                else:
                    # Look up by name
                    csr_name_to_addr = {v: k for k, v in self.important_csrs.items()}
                    if csr_arg not in csr_name_to_addr:
                        return self._encode_hex(f"Unknown CSR: {csr_arg}\n")
                    csr_addr = csr_name_to_addr[csr_arg]

                if csr_addr >= 4096:
                    return self._encode_hex("CSR address out of range\n")

                # Read or write
                if len(parts) == 2:
                    # Read CSR
                    val = self.cpu.csrs[csr_addr] & 0xFFFFFFFF
                    csr_name = self.important_csrs.get(csr_addr, f"0x{csr_addr:03x}")
                    output = f"{csr_name}: 0x{val:08x}\n"
                else:
                    # Write CSR
                    val = int(parts[2], 0)
                    self.cpu.csrs[csr_addr] = val & 0xFFFFFFFF
                    csr_name = self.important_csrs.get(csr_addr, f"0x{csr_addr:03x}")
                    output = f"{csr_name} = 0x{val:08x}\n"

                return self._encode_hex(output)

            elif parts[0] == 'help':
                output = "Available commands:\n"
                output += "  csr <name|0xADDR> [value]  - Read/write CSR\n"
                output += "  help                       - Show this help\n"
                return self._encode_hex(output)

            else:
                return self._encode_hex(f"Unknown command: {parts[0]}\n")

        except Exception as e:
            self.logger.error(f"Monitor command error: {e}")
            return self._encode_hex(f"Error: {e}\n")

    def _encode_hex(self, text: str) -> str:
        """Encode text to hex for GDB output.

        Args:
            text: Text to encode

        Returns:
            Hex-encoded string
        """
        return text.encode('ascii').hex()
