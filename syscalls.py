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

from machine import MachineError, ExecutionTerminated
import sys, os, stat, errno, struct
from enum import IntEnum

# syscall IDs (Newlib standard)
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

class SyscallHandler:
    def __init__(self, cpu, ram, machine, logger=None, raw_tty=False, trace_syscalls=False):
        self.cpu = cpu
        self.ram = ram
        self.machine = machine
        self.logger = logger
        self.raw_tty = raw_tty
        self.trace_syscalls = trace_syscalls

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

         # file descriptor mapping
        self.fd_map = {
            0: sys.stdin.fileno(),
            1: sys.stdout.fileno(),
            2: sys.stderr.fileno(),
        }
        self.next_fd = 3
        self.umask = 0o022  # default umask

    # main syscall dispatch
    def handle(self):
        syscall_id = self.cpu.registers[17]  # a7
        handler = self.syscall_handlers[syscall_id]
        if handler:
            return handler()
        else:        
            # unhandled syscall
            raise InvalidSyscallError(f"SYSCALL {syscall_id} UNKNOWN")

    # _exit syscall (Newlib standard)
    def handle_exit(self):
        self.cpu.pc = self.cpu.next_pc      # advance PC
        exit_code = self.cpu.registers[10]  # a0
        if exit_code >= 0x80000000: exit_code -= 0x100000000
        if self.logger is not None and self.trace_syscalls:
            self.logger.debug(f"SYSCALL _exit: exit code={exit_code}")
        raise ExecutionTerminated(f"exit code = {exit_code}")

    # _sbrk syscall (Newlib standard)
    def handle_sbrk(self):
        if self.machine.stack_bottom is None:
            raise InvalidSyscallError("SYSCALL _sbrk: stack bottom not set")

        increment = self.cpu.registers[10]
        old_heap_end = self.machine.heap_end
        new_heap_end = old_heap_end + increment

        if new_heap_end >= self.machine.stack_bottom:
            self.cpu.registers[10] = 0xFFFFFFFF  # -1 = failure
        else:
            self.machine.heap_end = new_heap_end
            self.cpu.registers[10] = old_heap_end  # return old break
        if self.logger is not None and self.trace_syscalls:
            self.logger.debug(f"SYSCALL _sbrk: increment={increment}, old_heap_end={old_heap_end:08X}, new_heap_end={new_heap_end:08X}")
        return True
        
    # _write syscall (Newlib standard)
    def handle_write(self):
        fd = self.cpu.registers[10]      # a0
        addr = self.cpu.registers[11]    # a1
        count = self.cpu.registers[12]   # a2
        if self.logger is not None and self.trace_syscalls:
            self.logger.debug(f"SYSCALL _write: fd={fd}, addr={addr:08X}, count={count}")
        data = self.ram.load_binary(addr, count)
        if fd == 1 or fd == 2:  # stdout or stderr
            if not self.raw_tty:
                print(data.decode(), end='')
            else:
                sys.stdout.buffer.write(data)
                sys.stdout.flush()
            self.cpu.registers[10] = count  # number of bytes written
        else:
            if fd in self.fd_map:
                try:
                    count = os.write(self.fd_map[fd], data)
                    self.cpu.registers[10] = count
                except OSError as e:
                    self.cpu.registers[10] = -e.errno
                    self.logger.warning(f"SYSCALL _write: error {-e.errno} writing fd={fd}")
            else:
                self.cpu.registers[10] = -errno.EBADF
                self.logger.warning(f"SYSCALL _write: unknown fd={fd}")
        return True
        
    # _read syscall (Newlib standard)
    def handle_read(self):
        fd = self.cpu.registers[10]      # a0
        addr = self.cpu.registers[11]    # a1
        count = self.cpu.registers[12]   # a2
        if self.logger is not None and self.trace_syscalls:
            self.logger.debug(f"SYSCALL _read: fd={fd}, addr=0x{addr:08X}, count={count}")
        if fd == 0:  # stdin
            if not self.raw_tty:
                try:  # normal (cooked) terminal mode
                    # Blocking read from stdin
                    input_text = input() + "\n"  # Simulate ENTER key
                    data = input_text.encode()[:count]
                except EOFError:
                    data = b''
                self.ram.store_binary(addr, data)
                self.cpu.registers[10] = len(data)
            else:  # raw terminal mode
                ch = sys.stdin.read(1)  # blocks for a single char
                if ch == '\x03':        # handle CTRL+C
                    raise KeyboardInterrupt
                self.ram.store_byte(addr, ord(ch))
                self.cpu.registers[10] = 1
        elif fd in self.fd_map:
            data = os.read(self.fd_map[fd], count)
            self.ram.store_binary(addr, data)
            self.cpu.registers[10] = len(data)
        else:
            self.fd_mapcpu.registers[10] = -errno.EBADF
            self.logger.warning(f"SYSCALL _read: unknown fd={fd}")
        return True
        
    # _openat syscall (Newlib standard)
    def handle_openat(self):
        dirfd = self.cpu.registers[10]  # a0 (signed)
        if dirfd >= 0x80000000:
            dirfd -= 0x100000000
        if dirfd != -100:  # not AT_FDCWD
            self.logger.warning(f"SYSCALL _openat: dirfd={dirfd} is not supported")
            self.cpu.registers[10] = -errno.ENOTSUP
            return True
        
        pathname_ptr = self.cpu.registers[11]   # a1
        flags = self.cpu.registers[12]          # a2
        mode = self.cpu.registers[13]           # a3
        pathname = self.ram.load_cstring(pathname_ptr)
        if self.logger is not None and self.trace_syscalls:
            self.logger.debug(f"SYSCALL _openat: dirfd={dirfd}, path=\"{pathname}\", flags={flags:#x}, mode={mode:#o}")
        
        try:
            old_umask = os.umask(0)
            host_fd = os.open(path=pathname, flags=flags, mode=mode & ~self.umask)
            emu_fd = self.next_fd
            self.fd_map[emu_fd] = host_fd
            self.next_fd += 1
            self.cpu.registers[10] = emu_fd
        except OSError as e:
            self.cpu.registers[10] = -e.errno
        finally:
            os.umask(old_umask)
        return True
        
    # _close syscall (Newlib standard)
    def handle_close(self):
        fd = self.cpu.registers[10]  # a0
        if self.logger and self.trace_syscalls:
            self.logger.debug(f"SYSCALL _close: fd={fd}")
        if fd in self.fd_map:
            try:
                os.close(self.fd_map[fd])
                del self.fd_map[fd]
                self.cpu.registers[10] = 0  # success
            except OSError as e:
                self.cpu.registers[10] = -e.errno
                self.logger.warning(f"SYSCALL _close: error {-e.errno} for fd={fd}")
        else:
            self.cpu.registers[10] = -errno.EBADF
            self.logger.warning(f"SYSCALL _close: unknown fd={fd}")
        return True
        
    # _lseek syscall (Newlib standard)
    def handle_lseek(self):
        fd = self.cpu.registers[10]         # a0
        offset = self.cpu.registers[11]     # a1
        whence = self.cpu.registers[12]     # a2 (0=SEEK_SET, 1=SEEK_CUR, 2=SEEK_END)
        if self.logger and self.trace_syscalls:
            self.logger.debug(f"SYSCALL _lseek: fd={fd}, offset={offset}, whence={whence}")
        if fd not in self.fd_map:
            self.cpu.registers[10] = -errno.EBADF
            self.logger.warning(f"SYSCALL _lseek: unknown fd={fd}")
            return True

        try:
            result = os.lseek(self.fd_map[fd], offset, whence)
            self.cpu.registers[10] = result
        except OSError as e:
            self.cpu.registers[10] = -e.errno
            self.logger.warning(f"SYSCALL _lseek: error {-e.errno} seeking fd={fd}")
        return True

    # _fstat syscall (Newlib standard)
    def handle_fstat(self):
        fd = self.cpu.registers[10]         # a0
        buf_ptr = self.cpu.registers[11]    # a1
        if self.logger and self.trace_syscalls:
            self.logger.debug(f"SYSCALL _fstat: fd={fd}, buf_ptr=0x{buf_ptr:08X}")

        if fd == 0 or fd == 1 or fd == 2:  # pretend it's a tty
            mode = stat.S_IFCHR | 0o666
            size = 0
        elif fd in self.fd_map:
            try:
                st = os.fstat(self.fd_map[fd])
                mode = st.st_mode
                size = st.st_size
            except OSError as e:
                self.cpu.registers[10] = -e.errno
                self.logger.warning(f"SYSCALL _fstat: error {-e.errno} on fd={fd}")
                return True
        else:
            self.cpu.registers[10] = -errno.EBADF
            self.logger.warning(f"SYSCALL _fstat: unknown fd={fd}")
            return True

        # Fill stat data structure (st_mode and st_size only)
        stat_buf = bytearray(88)
        struct.pack_into("<I", stat_buf, 4, mode)   # st_mode at offset 4
        struct.pack_into("<Q", stat_buf, 16, size)  # st_size at offset 16
        self.ram.store_binary(buf_ptr, stat_buf)
        self.cpu.registers[10] = 0  # success
        return True
    
    # _isatty syscall (Newlib standard)
    def handle_isatty(self):
        fd = self.cpu.registers[10]  # a0
        if self.logger and self.trace_syscalls:
            self.logger.debug(f"SYSCALL _isatty: fd={fd}")
        if fd == 0 or fd == 1 or fd == 2:
            self.cpu.registers[10] = 1  # is a TTY
        elif fd in self.fd_map:
            self.cpu.registers[10] = 0  # not a TTY
        else:
            self.cpu.registers[10] = -errno.EBADF
            self.logger.warning(f"SYSCALL _isatty: unknown fd={fd}")
        return True
        
    # _kill syscall (Newlib standard)
    def handle_kill(self):
        pid = self.cpu.registers[10]    # a0
        sig = self.cpu.registers[11]    # a1
        if self.logger and self.trace_syscalls:
            self.logger.warning(f"SYSCALL _kill (UNIMPLEMENTED): pid={pid}, sig={sig}")
        self.cpu.registers[10] = -errno.ENOSYS
        return True
        
    # _getpid syscall (Newlib standard)
    def handle_getpid(self):
        if self.logger and self.trace_syscalls:
            self.logger.debug("SYSCALL _getpid: returning 1")
        self.cpu.registers[10] = 1  # always return PID=1
        return True
        
    # umask syscall (Newlib standard)
    def handle_umask(self):
        new_mask = self.cpu.registers[10]  # a0
        old_mask = self.umask
        if self.logger and self.trace_syscalls:
            self.logger.debug("SYSCALL umask: old_mask={old_mask:#o}, new_mask={new_mask:#o}")
        self.umask = new_mask & 0o777
        self.cpu.registers[10] = old_mask
        return True
    
    # _mkdirat syscall (Newlib standard)
    def handle_mkdirat(self):
        dirfd = self.cpu.registers[10]
        if dirfd >= 0x80000000:
            dirfd -= 0x100000000
        if dirfd != -100:  # not AT_FDCWD
            self.logger.warning(f"SYSCALL _openat: dirfd={dirfd} is not supported")
            self.cpu.registers[10] = -errno.ENOTSUP
            return True
        
        pathname_ptr = self.cpu.registers[11]
        mode = self.cpu.registers[12]
        pathname = self.ram.load_cstring(pathname_ptr)
        if self.logger and self.trace_syscalls:
            self.logger.debug(f"SYSCALL _mkdirat: dirfd={dirfd}, path={pathname!r}, mode=0o{mode:o}")

        try:
            os.mkdir(pathname, mode & ~self.umask)
            self.cpu.registers[10] = 0
        except FileExistsError:
            self.cpu.registers[10] = -errno.EEXIST
        except PermissionError:
            self.cpu.registers[10] = -errno.EPERM
        except Exception:
            self.cpu.registers[10] = -errno.EIO
        return True
    
    # _unlinkat syscall (Newlib standard)
    def handle_unlinkat(self):
        dirfd = self.cpu.registers[10]          # a0
        if dirfd >= 0x80000000:
            dirfd -= 0x100000000
        if dirfd != -100:  # not AT_FDCWD
            self.logger.warning(f"SYSCALL _openat: dirfd={dirfd} is not supported")
            self.cpu.registers[10] = -errno.ENOTSUP
            return True
        
        pathname_ptr = self.cpu.registers[11]   # a1
        flags = self.cpu.registers[12]          # a2
        pathname = self.ram.load_cstring(pathname_ptr)
        if self.logger and self.trace_syscalls:
            self.logger.debug(f"SYSCALL unlinkat: dirfd={dirfd}, path={pathname!r}, flags=0x{flags:x}")

        try:
            if flags & 0x200:  # AT_REMOVEDIR
                os.rmdir(pathname)
            else:
                os.unlink(pathname)
            self.cpu.registers[10] = 0  # success
        except FileNotFoundError:
            self.cpu.registers[10] = -errno.ENOENT
        except IsADirectoryError:
            self.cpu.registers[10] = -errno.EISDIR
        except PermissionError:
            self.cpu.registers[10] = -errno.EPERM
        except Exception as e:
            self.cpu.registers[10] = -errno.EIO
        return True
