    .section .text
    .globl _write
    .globl _read
    .globl _exit

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
