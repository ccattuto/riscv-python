    .section .text
    .globl _start

_start:
    .option push
    .option norelax
    la sp, __stack_top  # initialize the stack pointer
    .option pop

    call main

halt:
    ebreak              # breakpoint, return value in a0
# unreachable
1:
    j 1b
