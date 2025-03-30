    .section .text
    .globl _start

_start:
    lui sp, 0x00100      # initialize SP at 0x00100000 (1MB)
    addi sp, sp, 0       # SP = 0x00100000 exactly

    # initialize the global pointer
    .option push
    .option norelax
    la gp, __global_pointer$
    .option pop

    jal ra, main         # jump to main

halt:
    mv a0, a0            # main's return value already in a0
    li a7, 93            # syscall ID for exit (newlib/Linux-style)
    ecall

#    ebreak               # breakpoint after main returns
#    j halt               # infinite loop after main returns
