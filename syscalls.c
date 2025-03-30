int _write(int fd, const char *buf, int count) {
    register int a0 asm("a0") = fd;
    register const char *a1 asm("a1") = buf;
    register int a2 asm("a2") = count;
    register int a7 asm("a7") = 64;  // _write syscall ID

    asm volatile("ecall"
                 : "+r"(a0)
                 : "r"(a1), "r"(a2), "r"(a7)
                 : "memory");
    return a0;  // return number of bytes written
}

int _read(int fd, char *buf, int count) {
    register int a0 asm("a0") = fd;
    register char *a1 asm("a1") = buf;
    register int a2 asm("a2") = count;
    register int a7 asm("a7") = 63;  // syscall ID for read

    asm volatile("ecall"
                 : "+r"(a0)              // return value in a0
                 : "r"(a1), "r"(a2), "r"(a7)
                 : "memory");

    return a0;  // return number of bytes read, or -1 on error
}

void _exit(int exit_code) {
    register int a0 asm("a0") = exit_code;
    register int a7 asm("a7") = 93;  // _exit syscall ID
    asm volatile("ecall"
                 :
                 : "r"(a0), "r"(a7)
                 : "memory");
    __builtin_unreachable();
}
