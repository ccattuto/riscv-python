    .section .text
    .globl _write
    .globl _read
    .globl _exit
    .globl _sbrk
    .globl _close
    .globl _fstat
    .globl _isatty
    .globl _lseek
    .globl _kill
    .globl _getpid

    .align 2

# ssize_t _write(int fd, const char *buf, size_t count)
_write:
    li a7, 64          # syscall number for write
    ecall
    ret

# ssize_t _read(int fd, char *buf, size_t count)
_read:
    li a7, 63          # syscall number for read
    ecall
    ret

# void _exit(int code)
_exit:
    li a7, 93          # syscall number for exit
    ecall
    # unreachable
1:
    j 1b

# void *_sbrk(int incr)
_sbrk:
    # a0 = increment
    li      a7, 214        # syscall number for sbrk (newlib expects this)
    ecall
    ret

_close:
    li a0, -1
    ret

_fstat:
    li a0, -1
    ret

_isatty:
    li a0, 1
    ret

_lseek:
    li a0, -1
    ret

_kill:
    li a0, -1
    ret

_getpid:
    li a0, 1
    ret
