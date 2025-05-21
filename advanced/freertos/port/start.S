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

    # initialize Newlib -- uncomment these if your FreeRTOS application needs Newlib-nano
#    la   a0, _impure_ptr
#    lw   a0, 0(a0)
#    call __sinit

    # install trap handler for FreeRTOS
#if defined(MTIMER_MMIO) && MTIMER_MMIO == 1
    la a0, freertos_risc_v_trap_handler
#else
    la a0, freertos_risc_v_trap_handler_riscvpy
#endif
    csrw mtvec, a0

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
