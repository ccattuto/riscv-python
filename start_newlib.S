    .section .text
    .globl _start

_start:
    .option push
    .option norelax
    la sp, __stack_top          # initialize the stack pointer
    la gp, __global_pointer$    # initialize the global pointer
    .option pop

    # save a0 and a1: they are used to pass arguments to main()
    mv s0, a0
    mv s1, a1

    # initialize Newlib
    la   a0, _impure_ptr
    lw   a0, 0(a0)
    call __sinit

    # restore a0 and a1
    mv a0, s0
    mv a1, s1

    call main

halt:
    mv a0, a0           # main's return value already in a0
    li a7, 93           # syscall ID for exit (newlib/Linux-style)
    ecall
# unreachable
1:
    j 1b
