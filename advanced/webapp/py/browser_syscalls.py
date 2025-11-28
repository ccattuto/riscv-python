"""
Browser Syscall Handler - Adapted for browser environment
Uses callbacks for I/O instead of direct file operations
"""

from machine import MachineError, ExecutionTerminated
import errno, struct
from enum import IntEnum

# Syscall IDs (Newlib standard)
class Syscall(IntEnum):
    EXIT        = 93
    SBRK        = 214
    WRITE       = 64
    READ        = 63
    OPENAT      = 1024
    CLOSE       = 57
    LSEEK       = 62
    FSTAT       = 80
    ISATTY      = 89
    KILL        = 129
    GETPID      = 172
    UMASK       = 60
    MKDIRAT     = 34
    UNLINKAT    = 35

class InvalidSyscallError(MachineError):
    pass

class BrowserSyscallHandler:
    """
    Syscall handler adapted for browser environment.
    Uses callbacks for I/O instead of direct file operations.
    """

    def __init__(self, cpu, ram, machine, logger=None, trace_syscalls=False,
                 write_callback=None, read_callback=None):
        self.cpu = cpu
        self.ram = ram
        self.machine = machine
        self.logger = logger
        self.trace_syscalls = trace_syscalls

        # Callbacks to JavaScript for I/O
        self.write_callback = write_callback  # write(data: bytes) -> None
        self.read_callback = read_callback    # async read(count: int) -> bytes

        self.syscall_handlers = {
            Syscall.EXIT:       self.handle_exit,
            Syscall.SBRK:       self.handle_sbrk,
            Syscall.WRITE:      self.handle_write,
            Syscall.READ:       self.handle_read,
            Syscall.OPENAT:     self.handle_openat,
            Syscall.CLOSE:      self.handle_close,
            Syscall.LSEEK:      self.handle_lseek,
            Syscall.FSTAT:      self.handle_fstat,
            Syscall.ISATTY:     self.handle_isatty,
            Syscall.KILL:       self.handle_kill,
            Syscall.GETPID:     self.handle_getpid,
            Syscall.UMASK:      self.handle_umask,
            Syscall.MKDIRAT:    self.handle_mkdirat,
            Syscall.UNLINKAT:   self.handle_unlinkat
        }

        self.umask = 0o022  # default umask

    def handle(self):
        """Main syscall dispatch"""
        syscall_id = self.cpu.registers[17]  # a7
        handler = self.syscall_handlers.get(syscall_id)

        if handler:
            return handler()
        else:
            # Unknown syscall - log warning and return -ENOSYS
            if self.logger:
                self.logger.warning(f"Unknown syscall {syscall_id}")
            self.cpu.registers[10] = -errno.ENOSYS
            return True

    def handle_exit(self):
        """
        _exit syscall - terminate execution.
        Raises ExecutionTerminated which will be caught by run_chunk(),
        which will set should_reset_pc=True so next run() restarts from entry point.
        """
        self.cpu.pc = self.cpu.next_pc
        exit_code = self.cpu.registers[10]  # a0
        if exit_code >= 0x80000000:
            exit_code -= 0x100000000

        if self.logger and self.trace_syscalls:
            self.logger.debug(f"SYSCALL exit: code={exit_code}")

        # This exception is caught in run_chunk() which sets should_reset_pc=True
        raise ExecutionTerminated(f"exit code = {exit_code}")

    def handle_sbrk(self):
        """_sbrk syscall - heap expansion"""
        if self.machine.stack_bottom is None:
            raise InvalidSyscallError("SYSCALL sbrk: stack bottom not set")

        increment = self.cpu.registers[10]  # a0
        old_heap_end = self.machine.heap_end
        new_heap_end = old_heap_end + increment

        if new_heap_end >= self.machine.stack_bottom:
            self.cpu.registers[10] = 0xFFFFFFFF  # -1 = failure
        else:
            self.machine.heap_end = new_heap_end
            self.cpu.registers[10] = old_heap_end

        if self.logger and self.trace_syscalls:
            self.logger.debug(f"SYSCALL sbrk: increment={increment}, "
                            f"old={old_heap_end:08X}, new={new_heap_end:08X}")
        return True

    def handle_write(self):
        """_write syscall - write to file descriptor"""
        fd = self.cpu.registers[10]      # a0
        addr = self.cpu.registers[11]    # a1
        count = self.cpu.registers[12]   # a2

        # Load data from emulated RAM
        data = self.ram.load_binary(addr, count)

        if self.logger and self.trace_syscalls:
            self.logger.debug(f"SYSCALL write: fd={fd}, addr={addr:08X}, count={count}, data={data[:50]}")

        if fd == 1 or fd == 2:  # stdout or stderr
            # Call JavaScript callback to write to terminal
            if self.write_callback:
                try:
                    # Convert Python bytes to JavaScript Uint8Array
                    import js
                    from pyodide.ffi import to_js

                    # Convert bytes to memoryview then to JS
                    js_array = to_js(memoryview(data))
                    self.write_callback(js_array)

                    self.cpu.registers[10] = count
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Write callback error: {e}")
                        import traceback
                        self.logger.error(traceback.format_exc())
                    self.cpu.registers[10] = -errno.EIO
            else:
                # No callback - just return success
                self.cpu.registers[10] = count
        else:
            # Other file descriptors not supported in pilot
            self.cpu.registers[10] = -errno.EBADF
            if self.logger and self.trace_syscalls:
                self.logger.warning(f"SYSCALL write: unsupported fd={fd}")

        return True

    def handle_read(self):
        """_read syscall - read from file descriptor"""
        fd = self.cpu.registers[10]      # a0
        addr = self.cpu.registers[11]    # a1
        count = self.cpu.registers[12]   # a2

        if self.logger and self.trace_syscalls:
            self.logger.debug(f"SYSCALL read: fd={fd}, addr={addr:08X}, count={count}")

        if fd == 0:  # stdin
            # Read from terminal input buffer
            if self.read_callback:
                try:
                    import js

                    # Get available data count from JavaScript
                    available = js.window.emulatorTerminal.inputBuffer.length

                    if available == 0:
                        # No data available - return EAGAIN to indicate would block
                        # This will cause the program to retry
                        self.cpu.registers[10] = -errno.EAGAIN
                    else:
                        # Data is available - read it
                        bytes_to_read = min(count, available)

                        # Read from the input buffer
                        data_list = []
                        for i in range(bytes_to_read):
                            byte_val = js.window.emulatorTerminal.inputBuffer.shift()
                            data_list.append(byte_val)

                        data_bytes = bytes(data_list)

                        # Store in emulated RAM
                        self.ram.store_binary(addr, data_bytes)
                        self.cpu.registers[10] = len(data_bytes)

                        if self.logger and self.trace_syscalls:
                            self.logger.debug(f"SYSCALL read: returned {len(data_bytes)} bytes: {data_bytes}")

                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Read callback error: {e}")
                        import traceback
                        self.logger.error(traceback.format_exc())
                    self.cpu.registers[10] = -errno.EIO
            else:
                # No callback - return EOF
                self.cpu.registers[10] = 0
        else:
            # Other file descriptors not supported
            self.cpu.registers[10] = -errno.EBADF
            if self.logger and self.trace_syscalls:
                self.logger.warning(f"SYSCALL read: unsupported fd={fd}")

        return True

    def handle_fstat(self):
        """_fstat syscall - get file status"""
        fd = self.cpu.registers[10]   # a0
        buf_ptr = self.cpu.registers[11]  # a1

        if self.logger and self.trace_syscalls:
            self.logger.debug(f"SYSCALL fstat: fd={fd}, buf={buf_ptr:08X}")

        if fd == 0 or fd == 1 or fd == 2:
            # stdin, stdout, stderr - pretend it's a tty
            # Match original implementation exactly
            S_IFCHR = 0x2000
            mode = S_IFCHR | 0o666
            size = 0
        else:
            self.cpu.registers[10] = -errno.EBADF
            return True

        # Fill stat data structure (matching original implementation)
        # st_mode at offset 4, st_size at offset 16
        stat_buf = bytearray(88)
        struct.pack_into("<I", stat_buf, 4, mode)   # st_mode at offset 4
        struct.pack_into("<Q", stat_buf, 16, size)  # st_size at offset 16
        self.ram.store_binary(buf_ptr, stat_buf)
        self.cpu.registers[10] = 0  # success
        return True

    def handle_isatty(self):
        """_isatty syscall - check if fd is a terminal"""
        fd = self.cpu.registers[10]  # a0

        if self.logger and self.trace_syscalls:
            self.logger.debug(f"SYSCALL isatty: fd={fd}")

        # stdin, stdout, stderr are terminals
        if fd == 0 or fd == 1 or fd == 2:
            self.cpu.registers[10] = 1  # yes, it's a tty
        else:
            self.cpu.registers[10] = 0

        return True

    def handle_getpid(self):
        """_getpid syscall - get process ID"""
        if self.logger and self.trace_syscalls:
            self.logger.debug("SYSCALL getpid")

        self.cpu.registers[10] = 1  # return fake PID
        return True

    def handle_umask(self):
        """_umask syscall - set file creation mask"""
        new_mask = self.cpu.registers[10]  # a0

        if self.logger and self.trace_syscalls:
            self.logger.debug(f"SYSCALL umask: new_mask={new_mask:03o}")

        old_mask = self.umask
        self.umask = new_mask
        self.cpu.registers[10] = old_mask
        return True

    # File operations - stubbed for pilot (return -ENOSYS)

    def handle_openat(self):
        """_openat syscall - STUBBED"""
        if self.logger and self.trace_syscalls:
            self.logger.debug("SYSCALL openat: STUBBED (-ENOSYS)")
        self.cpu.registers[10] = -errno.ENOSYS
        return True

    def handle_close(self):
        """_close syscall - STUBBED"""
        if self.logger and self.trace_syscalls:
            self.logger.debug("SYSCALL close: STUBBED (-ENOSYS)")
        self.cpu.registers[10] = -errno.ENOSYS
        return True

    def handle_lseek(self):
        """_lseek syscall - STUBBED"""
        if self.logger and self.trace_syscalls:
            self.logger.debug("SYSCALL lseek: STUBBED (-ENOSYS)")
        self.cpu.registers[10] = -errno.ENOSYS
        return True

    def handle_kill(self):
        """_kill syscall - STUBBED"""
        if self.logger and self.trace_syscalls:
            self.logger.debug("SYSCALL kill: STUBBED (-ENOSYS)")
        self.cpu.registers[10] = -errno.ENOSYS
        return True

    def handle_mkdirat(self):
        """_mkdirat syscall - STUBBED"""
        if self.logger and self.trace_syscalls:
            self.logger.debug("SYSCALL mkdirat: STUBBED (-ENOSYS)")
        self.cpu.registers[10] = -errno.ENOSYS
        return True

    def handle_unlinkat(self):
        """_unlinkat syscall - STUBBED"""
        if self.logger and self.trace_syscalls:
            self.logger.debug("SYSCALL unlinkat: STUBBED (-ENOSYS)")
        self.cpu.registers[10] = -errno.ENOSYS
        return True
