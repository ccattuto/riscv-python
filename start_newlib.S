    .section .text
    .globl _start

_start:
    .option push
    .option norelax
    la sp, __stack_top          # initialize the stack pointer
    la gp, __global_pointer$    # initialize the global pointer
    .option pop

    call __sinit    # initialize Newlib

    call main

halt:
    mv a0, a0           # main's return value already in a0
    li a7, 93           # syscall ID for exit (newlib/Linux-style)
    ecall
# unreachable
1:
    j 1b
