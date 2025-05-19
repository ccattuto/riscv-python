// This example tests machine timer interrupt handling (mtime / mtimecmp).
// Use "--timer=csr" to run it.

#include <stdint.h>
#include <stdio.h>

// CSR helpers
#define read_csr(reg) ({ unsigned int __tmp; \
    asm volatile ("csrr %0, " #reg : "=r"(__tmp)); \
    __tmp; })

#define write_csr(reg, val) ({ \
    asm volatile ("csrw " #reg ", %0" :: "rK"(val)); })

#define set_csr(reg, bitmask) ({ unsigned int __tmp; \
    asm volatile ("csrrs %0, " #reg ", %1" : "=r"(__tmp) : "rK"(bitmask)); \
    __tmp; })

#define clear_csr(reg, bitmask) ({ unsigned int __tmp; \
    asm volatile ("csrrc %0, " #reg ", %1" : "=r"(__tmp) : "rK"(bitmask)); \
    __tmp; })


volatile int tick_counter = 0;  // interrupt counter

// Trap (interrupt) handler
__asm__ (
".globl trap_entry\n"

"trap_entry:\n"
     // save state
"    addi sp, sp, -16\n"
"    sw ra, 12(sp)\n"
"    sw s0, 8(sp)\n"
"    sw s1, 4(sp)\n"

     // increment mtimecmp by 100000
"    li   t0, 100000\n"
"    csrr t1, 0x7C2\n"
"    csrr t2, 0x7C3\n"
"    add  t1, t1, t0\n"
"    sltu t3, t1, t0\n"
"    add  t2, t2, t3\n"
"    csrw 0x7C2, t1\n"
"    csrw 0x7C3, t2\n"

     // increment tick counter
"    lui   t0, %hi(tick_counter)\n"
"    lw    t1, %lo(tick_counter)(t0)\n"
"    addi  t1, t1, 1\n"
"    sw    t1, %lo(tick_counter)(t0)\n"

     // restore state
"    lw ra, 12(sp)\n"
"    lw s0, 8(sp)\n"
"    lw s1, 4(sp)\n"
"    addi sp, sp, 16\n"

"    mret\n"
);
extern void trap_entry(void);


int main(void) {
    // initialize mtimecmp <- mtime + 100000
    uint64_t mtime  = (((uint64_t) read_csr(0x7C1)) << 32) | read_csr(0x7C0);
    mtime += 100000;
    write_csr(0x7C2, (uint32_t) (mtime & 0xFFFFFFFF));  // mtimecmp lo
    write_csr(0x7C3, (uint32_t) (mtime >> 32));         // mtimecmp hi
    printf("mtime    = 0x %08X %08X\n", read_csr(0x7C1), read_csr(0x7C0));
    printf("mtimecmp = 0x %08X %08X\n", read_csr(0x7C3), read_csr(0x7C2));

    // install timer trap handler
    write_csr(mtvec, (uintptr_t) trap_entry);

    // enable traps
    set_csr(mie, 1 << 7);       // MTIE = 1
    set_csr(mstatus, 1 << 3);   // MIE = 1

    // IDLE LOOP (timer interrupt will fire while while this is running)
    volatile int counter = 0;
    for (int i=0; i<500000; i++) {
        counter += 1;
    }

    // disable  traps
    clear_csr(mie, 1 << 7);     // MTIE = 0
    clear_csr(mstatus, 1 << 3); // MIE = 0

    // set trap vector to 0, which will hand trap handling back to the emulator
    write_csr(mtvec, 0);

    // print counters
    printf("\nloop counter = %d\n", counter);
    printf("timer interrupt has fired %d times\n\n", tick_counter);

    printf("mtime    = 0x %08X %08X\n", read_csr(0x7C1), read_csr(0x7C0));
    printf("mtimecmp = 0x %08X %08X\n", read_csr(0x7C3), read_csr(0x7C2));

    return 0;
}
