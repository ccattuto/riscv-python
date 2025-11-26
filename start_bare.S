    .section .init
    .globl _start

_start:
    .option push
    .option norelax
    la sp, __stack_top  # initialize the stack pointer
    .option pop

    call main

halt:
#    ebreak              # breakpoint, return value in a0
    li a7, 93           # syscall ID for exit (newlib/Linux-style)
    ecall
# unreachable
1:
    j 1b
