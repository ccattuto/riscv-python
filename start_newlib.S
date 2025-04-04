    .section .text
    .globl _start

_start:
    .option push
    .option norelax
    la sp, __stack_top          # initialize the stack pointer
    la gp, __global_pointer$    # initialize the global pointer
    .option pop

    # initialize newlib's reentrant structure
    la  a0, _impure_ptr
    lw  a0, 0(a0)
    la  t0, __sinit
    jalr ra, t0, 0

    jal ra, main        # jump to main

halt:
    mv a0, a0           # main's return value already in a0
    li a7, 93           # syscall ID for exit (newlib/Linux-style)
    ecall
# unreachable
1:
    j 1b

#    ebreak              # breakpoint after main returns
#    j halt              # infinite loop after main returns
