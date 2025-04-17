#!/usr/bin/env python3

# Copyright (2025) Ciro Cattuto <ciro.cattuto@gmail.com>
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

import sys, os, stat, errno, struct
from elftools.elf.elffile import ELFFile

class MachineError(Exception):
    pass
class ConfigError(MachineError):
    pass
class InvalidSyscallError(MachineError):
    pass
class InvariantViolationError(MachineError):
    pass

class Machine:
    def __init__(self, cpu, ram, logger=None, raw_tty=False, trace_syscalls=False, check_start=None):
        self.cpu = cpu
        self.ram = ram

        self.logger = logger
        self.raw_tty = raw_tty
        self.trace_syscalls = trace_syscalls
        self.check_start = check_start
        self.check_enable = False

        # text, stack and heap boundaries
        self.stack_top = None
        self.stack_bottom = None
        self.heap_end = None
        self.text_start = None
        self.text_end = None

        # file descriptor mapping
        self.fd_map = {
            0: sys.stdin.fileno(),
            1: sys.stdout.fileno(),
            2: sys.stderr.fileno(),
        }
        self.next_fd = 3
        self.umask = 0o022  # default umask

        # text segment snapshot
        self.text_snapshot = None

        # symbol dictionary for syscall tracing
        self.symbol_dict = {}
        self.main_addr = None

    # setup argv[] strings in the heap
    def setup_argv(self, argv_list):
        argv_pointers = []
        for arg in argv_list:
            addr = self.heap_end
            self.ram.store_binary(addr, arg.encode() + b'\0')
            argv_pointers.append(addr)
            self.heap_end += len(arg) + 1
            self.heap_end = (self.heap_end + 3) & ~3  # ensure 4-byte alignment

        argv_table_addr = self.heap_end
        for ptr in argv_pointers + [0]:
            self.ram.store_word(self.heap_end, ptr)
            self.heap_end += 4

        self.heap_end = (self.heap_end + 7) & ~7  # ensure 8-byte alignment

        self.cpu.registers[10] = len(argv_list)   # a0
        self.cpu.registers[11] = argv_table_addr  # a1

    # load a flat binary executable into RAM
    def load_flatbinary(self, fname):
        with open(fname, 'rb') as f:
            binary = f.read()
            self.ram.store_binary(0, binary)
            self.cpu.pc = 0  # entry point at start of the binary
            if self.check_start == 'main':
                raise ConfigError("check_start=main is unsupported for flat binary executables")
            if self.check_start is None or self.check_start == 'default':
                self.check_start = 'first-call'

    # load an ELF executable into RAM
    def load_elf(self, fname, load_symbols=False, check_text=False):
        with open(fname, 'rb') as f:
            elf = ELFFile(f)

            # load all segments
            for segment in elf.iter_segments():
                if segment['p_type'] == 'PT_LOAD':
                    addr = segment['p_paddr']
                    data = segment.data()
                    self.ram.store_binary(addr, data)

            # set entry point
            self.cpu.pc = elf.header.e_entry

            # extract text / stack / heap boundaries
            symtab = elf.get_section_by_name(".symtab")
            if symtab:
                for sym in symtab.iter_symbols():
                    if sym.name == "__heap_start":
                        self.heap_end = sym["st_value"]
                    elif sym.name == "__stack_top":
                        self.stack_top = sym["st_value"]
                    elif sym.name == "__stack_bottom":
                        self.stack_bottom = sym["st_value"]
                    elif sym.name == "main":
                        self.main_addr = sym["st_value"]

                # load symbols for tracing
                if load_symbols:
                    for sym in symtab.iter_symbols():
                        name = sym.name
                        if not name:
                            continue
                        if sym['st_info']['type'] == 'STT_FUNC':
                            addr = sym['st_value']
                            self.symbol_dict[addr] = name

            # get boundaries of the text segment
            text_section = elf.get_section_by_name(".text")
            if text_section:
                self.text_start = text_section['sh_addr']
                self.text_end = self.text_start + text_section['sh_size']
                # if checking for text segment integrity, take a snapshot
                if check_text:
                    self.text_snapshot = self.ram.memory[self.text_start:self.text_end]

        if self.check_start is None or self.check_start == 'default':
            self.check_start = 'main'
        if self.check_start == 'main' and self.main_addr is None:
            self.logger.warning("No symbol found for main() — invariants checks disabled")

    # Syscall handling
    def handle_ecall(self):
        cpu = self.cpu
        syscall_id = cpu.registers[17]  # a7

        # _exit syscall (Newlib standard)
        if syscall_id == 93:  # _exit syscall
            exit_code = cpu.registers[10]  # a0
            if exit_code >= 0x80000000:
                exit_code -= 0x100000000
            if self.logger is not None:
                self.logger.info(f"SYSCALL _exit: exit code={exit_code}")
            return False

        # _sbrk syscall (Newlib standard)
        elif syscall_id == 214:
            if self.stack_bottom is None:
                raise InvalidSyscallError("SYSCALL _sbrk: stack bottom not set")

            increment = cpu.registers[10]
            old_heap_end = self.heap_end
            new_heap_end = old_heap_end + increment

            if new_heap_end >= self.stack_bottom:
                cpu.registers[10] = 0xFFFFFFFF  # -1 = failure
            else:
                self.heap_end = new_heap_end
                cpu.registers[10] = old_heap_end  # return old break
            if self.logger is not None and self.trace_syscalls:
                self.logger.debug(f"SYSCALL _sbrk: increment={increment}, old_heap_end={old_heap_end:08x}, new_heap_end={new_heap_end:08x}")
            return True
        
        # _write syscall (Newlib standard)
        elif syscall_id == 64:
            fd = cpu.registers[10]      # a0
            addr = cpu.registers[11]    # a1
            count = cpu.registers[12]   # a2
            if self.logger is not None and self.trace_syscalls:
                self.logger.debug(f"SYSCALL _write: fd={fd}, addr={addr:08x}, count={count}")
            data = self.ram.load_binary(addr, count)
            if fd == 1 or fd == 2:  # stdout or stderr
                if not self.raw_tty:
                    print(data.decode(), end='')
                else:
                    sys.stdout.buffer.write(data)
                    sys.stdout.flush()
                cpu.registers[10] = count  # number of bytes written
            else:
                if fd in self.fd_map:
                    try:
                        count = os.write(self.fd_map[fd], data)
                        cpu.registers[10] = count
                    except OSError as e:
                        cpu.registers[10] = -e.errno
                        self.logger.warning(f"SYSCALL _write: error {-e.errno} writing fd={fd}")
                else:
                    cpu.registers[10] = -errno.EBADF
                    self.logger.warning(f"SYSCALL _write: unknown fd={fd}")
            return True
        
        # _read syscall (Newlib standard)
        elif syscall_id == 63:
            fd = cpu.registers[10]      # a0
            addr = cpu.registers[11]    # a1
            count = cpu.registers[12]   # a2
            if self.logger is not None and self.trace_syscalls:
                self.logger.debug(f"SYSCALL _read: fd={fd}, addr=0x{addr:08x}, count={count}")
            if fd == 0:  # stdin
                if not self.raw_tty:
                    try:  # normal (cooked) terminal mode
                        # Blocking read from stdin
                        input_text = input() + "\n"  # Simulate ENTER key
                        data = input_text.encode()[:count]
                    except EOFError:
                        data = b''
                    self.ram.store_binary(addr, data)
                    cpu.registers[10] = len(data)
                else:  # raw terminal mode
                    ch = sys.stdin.read(1)  # blocks for a single char
                    if ch == '\x03':        # handle CTRL+C
                        raise KeyboardInterrupt
                    self.ram.store_byte(addr, ord(ch))
                    cpu.registers[10] = 1
            elif fd in self.fd_map:
                data = os.read(self.fd_map[fd], count)
                self.ram.store_binary(addr, data)
                cpu.registers[10] = len(data)
            else:
                cpu.registers[10] = -errno.EBADF
                self.logger.warning(f"SYSCALL _read: unknown fd={fd}")
            return True
        
        # _openat syscall (Newlib standard)
        if syscall_id == 1024:
            dirfd = cpu.registers[10]  # a0 (signed)
            if dirfd >= 0x80000000:
                dirfd -= 0x100000000
            if dirfd != -100:
                self.logger.warning(f"SYSCALL _openat: dirfd={dirfd} is not supported")
                cpu.registers[10] = -errno.ENOTSUP
                return True
            pathname_ptr = cpu.registers[11]    # a1
            flags = cpu.registers[12]           # a2
            mode = cpu.registers[13]            # a3
            pathname = self.ram.load_cstring(pathname_ptr)
            if self.logger is not None and self.trace_syscalls:
                self.logger.debug(f"SYSCALL _openat: dirfd={dirfd}, path=\"{pathname}\", flags={flags:#x}, mode={mode:#o}")
            
            try:
                old_umask = os.umask(0)
                host_fd = os.open(path=pathname, flags=flags, mode=mode & ~self.umask)
                emu_fd = self.next_fd
                self.fd_map[emu_fd] = host_fd
                self.next_fd += 1
                cpu.registers[10] = emu_fd
            except OSError as e:
                cpu.registers[10] = -e.errno
            finally:
                os.umask(old_umask)
            
            return True
        
        # _close syscall (Newlib standard)
        elif syscall_id == 57:
            fd = cpu.registers[10]  # a0
            if self.logger and self.trace_syscalls:
                self.logger.debug(f"SYSCALL _close: fd={fd}")
            if fd in self.fd_map:
                try:
                    os.close(self.fd_map[fd])
                    del self.fd_map[fd]
                    cpu.registers[10] = 0  # success
                except OSError as e:
                    cpu.registers[10] = -e.errno
                    self.logger.warning(f"SYSCALL _close: error {-e.errno} for fd={fd}")
            else:
                cpu.registers[10] = -errno.EBADF
                self.logger.warning(f"SYSCALL _close: unknown fd={fd}")
            return True
        
        # _lseek syscall (Newlib standard)
        elif syscall_id == 62:
            fd = cpu.registers[10]      # a0
            offset = cpu.registers[11]  # a1
            whence = cpu.registers[12]  # a2 (0=SEEK_SET, 1=SEEK_CUR, 2=SEEK_END)
            if self.logger and self.trace_syscalls:
                self.logger.debug(f"SYSCALL _lseek: fd={fd}, offset={offset}, whence={whence}")

            if fd not in self.fd_map:
                cpu.registers[10] = -errno.EBADF
                self.logger.warning(f"SYSCALL _lseek: unknown fd={fd}")
                return True

            try:
                result = os.lseek(self.fd_map[fd], offset, whence)
                cpu.registers[10] = result
            except OSError as e:
                cpu.registers[10] = -e.errno
                self.logger.warning(f"SYSCALL _lseek: error {-e.errno} seeking fd={fd}")
            return True

        # _fstat syscall (Newlib standard)
        elif syscall_id == 80:
            fd = cpu.registers[10]       # a0
            buf_ptr = cpu.registers[11]  # a1
            if self.logger and self.trace_syscalls:
                self.logger.debug(f"SYSCALL _fstat: fd={fd}, buf_ptr=0x{buf_ptr:08x}")

            if fd == 0 or fd == 1 or fd == 2:  # pretend it's a tty
                mode = stat.S_IFCHR | 0o666
                size = 0
            elif fd in self.fd_map:
                try:
                    st = os.fstat(self.fd_map[fd])
                    mode = st.st_mode
                    size = st.st_size
                except OSError as e:
                    cpu.registers[10] = -e.errno
                    self.logger.warning(f"SYSCALL _fstat: error {-e.errno} on fd={fd}")
                    return True
            else:
                cpu.registers[10] = -errno.EBADF
                self.logger.warning(f"SYSCALL _fstat: unknown fd={fd}")
                return True

            # Fill stat data structure (st_mode and st_size only)
            stat_buf = bytearray(88)
            struct.pack_into("<I", stat_buf, 4, mode)   # st_mode at offset 4
            struct.pack_into("<Q", stat_buf, 16, size)  # st_size at offset 16
            self.ram.store_binary(buf_ptr, stat_buf)

            cpu.registers[10] = 0  # success
            return True
        
        # _isatty syscall (Newlib standard)
        elif syscall_id == 89:
            fd = cpu.registers[10]  # a0
            if self.logger and self.trace_syscalls:
                self.logger.debug(f"SYSCALL _isatty: fd={fd}")
            if fd == 0 or fd == 1 or fd == 2:
                cpu.registers[10] = 1  # is a TTY
            elif fd in self.fd_map:
                cpu.registers[10] = 0  # not a TTY
            else:
                cpu.registers[10] = -errno.EBADF
                self.logger.warning(f"SYSCALL _isatty: unknown fd={fd}")
            return True
        
        # _kill syscall (Newlib standard)
        elif syscall_id == 129:
            pid = cpu.registers[10]  # a0
            sig = cpu.registers[11]  # a1
            if self.logger and self.trace_syscalls:
                self.logger.warning(f"SYSCALL _kill (UNIMPLEMENTED): pid={pid}, sig={sig}")
            cpu.registers[10] = -errno.ENOSYS
            return True
        
        # _getpid syscall (Newlib standard)
        elif syscall_id == 172:
            if self.logger and self.trace_syscalls:
                self.logger.debug("SYSCALL _getpid: returning 1")
            cpu.registers[10] = 1  # always return PID=1
            return True
        
        # umask syscall (Newlib standard)
        elif syscall_id == 60:
            new_mask = cpu.registers[10]  # a0
            old_mask = self.umask
            if self.logger and self.trace_syscalls:
                self.logger.debug("SYSCALL umask: old_mask={old_mask:#o}, new_mask={new_mask:#o}")
            self.umask = new_mask & 0o777
            cpu.registers[10] = old_mask
            return True
        
        # unhandled syscall
        else:
            raise InvalidSyscallError(f"SYSCALL {syscall_id} UNKNOWN")
    
    # Invariant check trigger
    def trigger_check(self):
        cpu = self.cpu
        if self.check_start == 'early':
            return True
        elif self.check_start == 'main':
            return cpu.pc == self.main_addr
        elif self.check_start == 'first-call':
            inst = self.ram.load_word(cpu.pc)
            opcode = inst & 0x7F
            return opcode in (0x6F, 0x67)
        else:
            try:
                value = int(self.check_start, 0) & 0xFFFFFFFF
                return self.pc == value
            except ValueError:
                raise ConfigError(f"Invalid --start-check value: {self.check_start}")

    # Invariants check
    def check_invariants(self):
        cpu = self.cpu

        # trigger checks
        if not self.check_enable:
            self.check_enable = self.trigger_check()
            if not self.check_enable:
                return
            else:
                self.logger.debug(f"Invariants checking started ({self.check_start})")

        # x0 = 0
        if not (cpu.registers[0] == 0):
            raise InvariantViolationError("x0 register should always be 0")

        # PC within memory bounds
        if not(0 <= cpu.pc < self.ram.size):
            raise InvariantViolationError(f"PC out of bounds: PC=0x{cpu.pc}")

        # SP below stack top
        if self.stack_top is not None and cpu.registers[3] != 0:
            if not(cpu.registers[2] <= self.stack_top):
                raise InvariantViolationError(f"SP above stack top: SP=0x{cpu.registers[2]:08x} > 0x{self.stack_top:08x}")

        # SP above stack bottom (stack overflow check)
        if self.stack_bottom is not None and cpu.registers[3] != 0:
            if not(cpu.registers[2] >= self.stack_bottom):
                raise InvariantViolationError(f"SP below stack bottom (stack overlow): SP=0x{cpu.registers[2]:08x} < 0x{self.stack_bottom:08x}")

        # Stack and heap separation
        MIN_GAP = 256
        if self.heap_end is not None and self.stack_bottom is not None:
            if not (self.heap_end + MIN_GAP <= self.stack_bottom):
                raise InvariantViolationError(f"Heap too close to stack: heap_end=0x{self.heap_end:08x}, stack_bottom=0x{self.stack_bottom:08x}")

        # SP word alignment
        if not(cpu.registers[2] % 4 == 0):
            raise InvariantViolationError(f"SP not aligned: SP=0x{cpu.registers[2]:08x}")

        # Heap end word alignment
        if self.heap_end is not None:
            if not(self.heap_end % 4 == 0):
                raise InvariantViolationError(f"Heap end not aligned: 0x{self.heap_end:08x}")
            
        # Text segment integrity check
        if self.text_snapshot is not None and \
            self.ram.memory[self.text_start:self.text_end] != self.text_snapshot:
                raise InvariantViolationError("Text segment has been modified!")

