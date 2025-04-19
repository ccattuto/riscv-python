# Startup code + return value
# Returns 42 in register a0

    .section .text
    .globl _start
    .globl main

_start:
    lui sp, 0x00100      # initialize SP at 0x00100000 (1MB)
    addi sp, sp, 0       # SP = 0x00100000 exactly

    call main

halt:
#    ebreak               # breakpoint, return value in a0
    li a7, 93           # syscall ID for exit (newlib/Linux-style)
    ecall
# unreachable
1:
    j 1b

main:
    li a0, 42  # load return value
    ret
