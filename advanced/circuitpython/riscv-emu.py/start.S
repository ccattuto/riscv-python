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

    # initialize .bss
    la   a0, __bss_start
    la   a1, __bss_end
z_bss:
    sw   zero, 0(a0)
    addi a0, a0, 4
    blt  a0, a1, z_bss

    # initialize .sbss
    la   a0, __sbss_start
    la   a1, __sbss_end
z_sbss:
    sw   zero, 0(a0)
    addi a0, a0, 4
    blt  a0, a1, z_sbss

    # initialize Newlib
    la   a0, _impure_ptr
    lw   a0, 0(a0)
    call __sinit

    # restore a0 and a1
    mv a0, s0
    mv a1, s1

    call main			# MAIN

halt:
    mv a0, a0
    li a7, 93           # syscall ID for exit (newlib/Linux-style)
    ecall
# unreachable
1:
    j 1b
