#include <stdio.h>
#include <stdint.h>
#include "riscv-py.h"

// CSR-based timer access

static inline void write_mtimecmp(uint64_t value) {
    uint32_t hi = value >> 32;
    uint32_t lo = value & 0xFFFFFFFF;

    __asm__ volatile ("csrw 0x7C2, %0" :: "r"(lo));
    __asm__ volatile ("csrw 0x7C3, %0" :: "r"(hi));
}

static inline uint64_t read_mtime(void) {
    uint32_t hi1, lo, hi2;
    do {
        __asm__ volatile ("csrr %0, 0x7C1" : "=r"(hi1));
        __asm__ volatile ("csrr %0, 0x7C0" : "=r"(lo));
        __asm__ volatile ("csrr %0, 0x7C1" : "=r"(hi2));
    } while (hi1 != hi2);

    return ((uint64_t) hi2 << 32) | lo;
}

static inline uint32_t read_mtime_lo(void) {
    uint32_t lo;
    __asm__ volatile ("csrr %0, 0x7C0" : "=r"(lo));

    return lo;
}

// timer interrupt setup

void vPortSetupTimerInterrupt(void)
{
    EMU_LOG_STR("vPortSetupTimerInterrupt()");

    // initialize mtimecmp <- mtime + 1000
    uint64_t mtime  = read_mtime();
    write_mtimecmp(mtime + 1000);

    // enable MTI
    SET_CSR(mie, 1 << 7);       // MTIE = 1
    SET_CSR(mstatus, 1 << 3);   // MIE = 1
}

void vConfigureTimerForRunTimeStats(void)
{
    EMU_LOG_STR("vConfigureTimerForRunTimeStats()");
}

uint32_t ulGetRunTimeCounterValue(void)
{
    return read_mtime_lo();
}

void vApplicationTickHook(void)
{
    EMU_LOG_STR("TICK");
}

// void vApplicationStackOverflowHook(TaskHandle_t xTask, char *pcTaskName)
// {
//     EMU_LOG_STR("Stack overflow detected!");
//     EMU_LOG_INT((uint32_t) xTask);
//     EMU_LOG_STR(pcTaskName);

//     for(;;);  // Hang the system
// }
