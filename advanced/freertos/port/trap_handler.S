/*
This is almost identical to the trap handler in FreeRTOS-Kernel/portable/GCC/RISC-V/portASM.S ,
the only different is that this updates mtimecmp via CSR registers (0x7C2/0x7C3) instead of using memory-mapped access.
*/

#include "portContext.h"

.global freertos_risc_v_trap_handler_riscvpy

.extern vTaskSwitchContext
.extern xTaskIncrementTick
.extern uxTimerIncrementsForOneTick /* size_t type so 32-bit on 32-bit core and 64-bits on 64-bit core. */

.macro portUPDATE_MTIMER_COMPARE_REGISTER
    lw   t0, uxTimerIncrementsForOneTick  /* load mtimcmp increment */
    csrr t1, 0x7C2  /* load mtimecmp */
    csrr t2, 0x7C3
    add  t1, t1, t0  /* add increment */
    sltu t3, t1, t0
    add  t2, t2, t3
    csrw 0x7C2, t1  /* update mtimecmp (atomic update on 2nd write) */
    csrw 0x7C3, t2
    .endm

/*-----------------------------------------------------------*/

.section .text.freertos_risc_v_interrupt_handler
freertos_risc_v_interrupt_handler:
    portcontextSAVE_INTERRUPT_CONTEXT
    call freertos_risc_v_application_interrupt_handler
    portcontextRESTORE_CONTEXT
/*-----------------------------------------------------------*/

.section .text.freertos_risc_v_mtimer_interrupt_handler
freertos_risc_v_mtimer_interrupt_handler:
    portcontextSAVE_INTERRUPT_CONTEXT
    portUPDATE_MTIMER_COMPARE_REGISTER
    call xTaskIncrementTick
    beqz a0, exit_without_context_switch    /* Don't switch context if incrementing tick didn't unblock a task. */
    call vTaskSwitchContext
exit_without_context_switch:
    portcontextRESTORE_CONTEXT
/*-----------------------------------------------------------*/

.section .text.freertos_risc_v_trap_handler_riscvpy
.align 8
freertos_risc_v_trap_handler_riscvpy:
    portcontextSAVE_CONTEXT_INTERNAL

    csrr a0, mcause
    csrr a1, mepc

    bge a0, x0, synchronous_exception

asynchronous_interrupt:
    store_x a1, 0( sp )                 /* Asynchronous interrupt so save unmodified exception return address. */
    load_x sp, xISRStackTop             /* Switch to ISR stack. */
    j handle_interrupt

synchronous_exception:
    addi a1, a1, 4                      /* Synchronous so update exception return address to the instruction after the instruction that generated the exeption. */
    store_x a1, 0( sp )                 /* Save updated exception return address. */
    load_x sp, xISRStackTop             /* Switch to ISR stack. */
    j handle_exception

handle_interrupt:
    li t1, 0x80000007  # Machine Timer Interrupt
    bne a0, t1, application_interrupt_handler

    portUPDATE_MTIMER_COMPARE_REGISTER
    call xTaskIncrementTick
    beqz a0, processed_source       /* Don't switch context if incrementing tick didn't unblock a task. */
    call vTaskSwitchContext
    j processed_source

application_interrupt_handler:
    call freertos_risc_v_application_interrupt_handler
    j processed_source

handle_exception:
    /* a0 contains mcause. */
    li t0, 11                                   /* 11 == environment call. */
    bne a0, t0, application_exception_handler   /* Not an M environment call, so some other exception. */
    call vTaskSwitchContext
    j processed_source

application_exception_handler:
    call freertos_risc_v_application_exception_handler
    j processed_source                  /* No other exceptions handled yet. */

processed_source:
    portcontextRESTORE_CONTEXT
