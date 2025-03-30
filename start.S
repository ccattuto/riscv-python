    .section .text
    .globl _start

_start:
    lui sp, 0x00100      # initialize SP at 0x00100000 (1MB)
    addi sp, sp, 0       # SP = 0x00100000 exactly

    .option push
    .option norelax
    la gp, __global_pointer$
    .option pop

    jal ra, main         # jump to main
halt:
    ebreak
#    j halt               # infinite loop after main returns
