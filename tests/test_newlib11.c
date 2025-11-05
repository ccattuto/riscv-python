// This example implements timer-based round-robin preemptive scheduling for two tasks.
// Use "--timer=csr" to run it.

#include <stdint.h>
#include <stdio.h>
#include "riscv-py.h"

// Task context type
typedef struct {
    uint32_t ra;
    uint32_t sp;
    uint32_t s[12];   // s0–s11
    uint32_t a[8];    // a0–a7
    uint32_t mepc;
    uint32_t mstatus;
} context_t;

// Task contexts
context_t ctx1, ctx2;
context_t *task_current, *task_next;

// Task-specific stacks
#define STACK_SIZE 512
uint8_t stack1[STACK_SIZE];
uint8_t stack2[STACK_SIZE];


__asm__ (
".globl start_first_task\n"
".globl trap_handler\n"

// trampoline: launch first task (set up SP, mepc, mstatus)
"start_first_task:\n"
"    lw sp, 4(a0)\n"
"    lw ra, 0(a0)\n"
"    lw t0, 88(a0)\n"
"    csrw mepc, t0\n"
"    lw t0, 92(a0)\n"
"    csrw mstatus, t0\n"
"    mret\n"

// trap handler
".align 4\n"  // Ensure 4-byte alignment for mtvec (RISC-V spec requirement)
"trap_handler:\n"
     // save current state
"    la t0, task_current\n"
"    lw t1, 0(t0)\n"
"    sw ra, 0(t1)\n"
"    sw sp, 4(t1)\n"
"    sw s0, 8(t1)\n"
"    sw s1, 12(t1)\n"
"    sw s2, 16(t1)\n"
"    sw s3, 20(t1)\n"
"    sw s4, 24(t1)\n"
"    sw s5, 28(t1)\n"
"    sw s6, 32(t1)\n"
"    sw s7, 36(t1)\n"
"    sw s8, 40(t1)\n"
"    sw s9, 44(t1)\n"
"    sw s10, 48(t1)\n"
"    sw s11, 52(t1)\n"
"    sw a0, 56(t1)\n"
"    sw a1, 60(t1)\n"
"    sw a2, 64(t1)\n"
"    sw a3, 68(t1)\n"
"    sw a4, 72(t1)\n"
"    sw a5, 76(t1)\n"
"    sw a6, 80(t1)\n"
"    sw a7, 84(t1)\n"
"    csrr t2, mepc\n"
"    sw t2, 88(t1)\n"
"    csrr t2, mstatus\n"
"    sw t2, 92(t1)\n"

     // increment mtimecmp by 100000
"    li   t0, 100000\n"
"    csrr t1, 0x7C2\n"
"    csrr t2, 0x7C3\n"
"    add  t1, t1, t0\n"
"    sltu t3, t1, t0\n"
"    add  t2, t2, t3\n"
"    csrw 0x7C2, t1\n"
"    csrw 0x7C3, t2\n"

     // swap current and suspended tasks
"    la t0, task_current\n"
"    la t1, task_next\n"
"    lw t2, 0(t0)\n"
"    lw t3, 0(t1)\n"
"    sw t3, 0(t0)\n"
"    sw t2, 0(t1)\n"

     // restore state of next task
"    mv t1, t3\n"
"    lw ra, 0(t1)\n"
"    lw sp, 4(t1)\n"
"    lw s0, 8(t1)\n"
"    lw s1, 12(t1)\n"
"    lw s2, 16(t1)\n"
"    lw s3, 20(t1)\n"
"    lw s4, 24(t1)\n"
"    lw s5, 28(t1)\n"
"    lw s6, 32(t1)\n"
"    lw s7, 36(t1)\n"
"    lw s8, 40(t1)\n"
"    lw s9, 44(t1)\n"
"    lw s10, 48(t1)\n"
"    lw s11, 52(t1)\n"
"    lw a0, 56(t1)\n"
"    lw a1, 60(t1)\n"
"    lw a2, 64(t1)\n"
"    lw a3, 68(t1)\n"
"    lw a4, 72(t1)\n"
"    lw a5, 76(t1)\n"
"    lw a6, 80(t1)\n"
"    lw a7, 84(t1)\n"
"    lw t2, 88(t1)\n"
"    csrw mepc, t2\n"
"    lw t2, 92(t1)\n"
"    csrw mstatus, t2\n"

"    mret\n"
);
extern void trap_handler(void);
extern void start_first_task(context_t*);

// Set up task context
void init_context(context_t *ctx, void (*func)(void), uint8_t *stack_top) {
    ctx->ra = (uint32_t)func;
    ctx->sp = (uint32_t)stack_top;
    for (int i = 0; i < 12; i++) ctx->s[i] = 0;
    for (int i = 0; i < 8; i++) ctx->a[i] = 0;
    ctx->mepc = (uint32_t) func;
    ctx->mstatus = 1 << 7;  // MIEP = 1
}

// TASK 1
void task1(void) {
    volatile int cnt = 0;
    EMU_LOG_STR("TASK 1 starting");
    while (1) {
        if ((cnt & 0xFFFF) == 0) {
            EMU_LOG_INT(cnt);
        }
        cnt++;
    }
}

// TASK 2
void task2(void) {
    volatile int cnt = 0xFFFFFFFF;
    EMU_LOG_STR("TASK 2 starting");
    while (1) {
        if ((cnt & 0xFFFF) == 0) {
            EMU_LOG_INT(cnt);
        }
        cnt--;
    }
}

int main(void) {
    // set up tasks
    init_context(&ctx1, task1, stack1 + STACK_SIZE);
    init_context(&ctx2, task2, stack2 + STACK_SIZE);

    task_current = &ctx1;  // Current task
    task_next = &ctx2;

    // Set mtimecmp <- mtime + 100000
    uint64_t mtime  = (((uint64_t) READ_CSR(0x7C1)) << 32) | READ_CSR(0x7C0);  // (no risk mtime_lo will wrap)
    mtime += 100000;
    WRITE_CSR(0x7C2, (uint32_t) (mtime & 0xFFFFFFFF));  // mtimecmp lo
    WRITE_CSR(0x7C3, (uint32_t) (mtime >> 32));         // mtimecmp hi

    // Install trap handler and enable timer interrupt
    WRITE_CSR(mtvec, (uint32_t) trap_handler);
    SET_CSR(mie, 1 << 7);
    SET_CSR(mstatus, 1 << 3);

    EMU_LOG_STR("Starting preemptive task scheduler");
    start_first_task(task_current);  // trampoline

    while (1);  // never reached
}
