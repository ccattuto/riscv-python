#ifndef PORTMACRO_H
#define PORTMACRO_H

#include <stdio.h>
#include <stdint.h>

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

#endif // PORTMACRO_H
