# syscall stubs
    .section .text
    .globl _write
    .globl _read
    .globl _exit
    .globl _sbrk
    .globl _open
    .globl _openat
    .globl _close
    .globl _fstat
    .globl _isatty
    .globl _lseek
    .globl _kill
    .globl _getpid
    .globl umask
    .globl _mkdirat
    .globl _mkdir
    .globl _unlinkat
    .globl _unlink
    .globl _rmdir

    .align 2

# ssize_t _write(int fd, const char *buf, size_t count)
_write:
    li a7, 64           # syscall ID for write
    ecall
    ret

# ssize_t _read(int fd, char *buf, size_t count)
_read:
    li a7, 63           # syscall ID for read
    ecall
    ret

# void _exit(int code)
_exit:
    li a7, 93           # syscall ID for exit
    ecall
    # unreachable
1:
    j 1b

# void *_sbrk(int incr)
_sbrk:
    # a0 = increment
    li      a7, 214     # syscall ID for sbrk (Newlib expects this)
    ecall
    ret

# int _open(const char *pathname, int flags, ...)
_open:
    mv a3, a2           # mode
    mv a2, a1           # flags
    mv a1, a0           # pathname
    li a0, -100         # AT_FDCWD
    li a7, 1024         # syscall ID for openat
    ecall
    ret

_openat:                # syscall ID for openat
    li a7, 1024
    ecall
    ret

_close:
    li a7, 57           # syscall ID for close
    ecall
    ret

# int fstat(int fd, struct stat *buf)
_fstat:
    li a7, 80           # syscall ID for fstat
    ecall
    ret

_isatty:
    li a7, 89           # syscall ID for isatty
    ecall
    ret

_lseek:
    li a7, 62           # syscall ID for lseek
    ecall
    ret

_kill:
    li a7, 129          # syscall ID for kill
    ecall
    ret

_getpid:
    li a7, 172          # syscall ID for getpid
    ecall
    ret

umask:
    li a7, 60           # syscall number for umask
    ecall
    ret

_unlinkat:
    li a7, 35           # syscall ID for unlinkat
    ecall
    ret

_mkdirat:
    li a7, 34           # syscall ID for mkdirat
    ecall
    ret

_mkdir:
    mv a2, a1           # a2 = mode
    mv a1, a0           # a1 = pathname
    li a0, -100         # a0 = AT_FDCWD
    li a7, 34           # syscall ID for mkdirat
    ecall
    ret

_unlink:
    li a2, 0            # flags=0 for unlink
    mv a1, a0           # pathname
    li a0, -100         # AT_FDCWD
    li a7, 35           # _unlinkat
    ecall
    ret

_rmdir:
    li a2, 0x200        # flags=AT_REMOVEDIR for rmdir
    mv a1, a0           # pathname
    li a0, -100         # AT_FDCWD
    li a7, 35           # unlinkat
    ecall
    ret
