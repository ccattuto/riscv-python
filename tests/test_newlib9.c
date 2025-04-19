// This example tests trap handling for EBREAK, ECALL and illegal instructions.
// Notice: the emulator actually supports misaligned loads/stores,
// so it is correct that it doesn't trap on those attempts.

#include <stdint.h>
#include <stdio.h>

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


// Trap handler
__asm__ (
".globl trap_entry\n"
"trap_entry:\n"
"    addi sp, sp, -16\n"
"    sw ra, 12(sp)\n"
"    sw s0, 8(sp)\n"
"    sw s1, 4(sp)\n"

"    csrr s0, mcause\n"
"    csrr s1, mepc\n"

"    lui t0, %hi(trap_mcause)\n"
"    sw s0, %lo(trap_mcause)(t0)\n"

"    lui t0, %hi(trap_mepc)\n"
"    sw s1, %lo(trap_mepc)(t0)\n"

"    lui t0, %hi(trap_entered)\n"
"    li  t1, 1\n"
"    sw  t1, %lo(trap_entered)(t0)\n"

"    addi s1, s1, 4\n"
"    csrw mepc, s1\n"

"    lw ra, 12(sp)\n"
"    lw s0, 8(sp)\n"
"    lw s1, 4(sp)\n"
"    addi sp, sp, 16\n"
"    mret\n"
);
extern void trap_entry(void);

// Globals for monitoring trap status
volatile int trap_entered = 0;
volatile uint32_t trap_mcause = 0;
volatile uint32_t trap_mepc = 0;

// Type for trap test functions
typedef void (*trap_trigger_fn)(void);

// Generic trap test wrapper
void test_trap(const char* name, trap_trigger_fn trigger) {
    trap_entered = 0;
    printf("[TEST] Triggering: %s\n", name);

    write_csr(mtvec, (uintptr_t) trap_entry); // install trap handler
    trigger();
    write_csr(mtvec, 0); // restore emulated trap handler

    // check
    if (trap_entered) {
        printf("[PASS] Trap handled.\n");
        printf("       mcause = 0x%08x\n", trap_mcause);
        printf("       mepc   = 0x%08x\n", trap_mepc);
    } else {
        printf("[FAIL] Trap was NOT handled!\n");
    }
    printf("\n");
}

// Trap triggers

// EBREAK
void trigger_ebreak(void) {
    __asm__ volatile("ebreak");
}

// ECALL
void trigger_ecall(void) {
    __asm__ volatile("ecall");
}

// Illegal instruction
void trigger_illegal(void) {
    __asm__ volatile(".word 0xFFFFFFFF");
}

// Load from a misaligned address
void trigger_misaligned_load(void) {
    volatile uint8_t data[8] = {0xAA, 0xBB, 0xCC, 0xDD, 0x11, 0x22, 0x33, 0x44};
    volatile int result;
    uintptr_t addr = (uintptr_t)&data[1];  // misaligned by 1
    __asm__ volatile("lw %0, 0(%1)" : "=r"(result) : "r"(addr));
}

// Store to a misaligned address
void trigger_misaligned_store(void) {
    volatile uint8_t data[8];
    uintptr_t addr = (uintptr_t)&data[3];  // misaligned by 3
    __asm__ volatile("sw zero, 0(%0)" :: "r"(addr));
}

// Write to a read-only CSR
void trigger_invalid_csr(void) {
    register uint32_t value = 0xFFFFFFFF;
    __asm__ volatile("csrw misa, %0" :: "r"(value));
}


int main(void) {
    printf("Minimal M-mode Trap Test Starting...\n\n");

    // Baseline CSR reads
    uint32_t mstatus = read_csr(mstatus);
    printf("Initial mstatus: 0x%08x\n", mstatus);

    write_csr(mscratch, 0xDEADBEEF);
    printf("mscratch:        0x%08x\n", read_csr(mscratch));
    printf("mtvec (before):  0x%08x\n\n", read_csr(mtvec));

    // Run trap tests
    test_trap("EBREAK (mcause = 3)", trigger_ebreak);
    test_trap("ECALL  (mcause = 11)", trigger_ecall);
    test_trap("Illegal instruction (mcause = 2)", trigger_illegal);
    test_trap("Misaligned LOAD (mcause = 4)", trigger_misaligned_load);
    test_trap("Misaligned STORE (mcause = 6)", trigger_misaligned_store);
    test_trap("Invalid CSR write (mcause = 2)", trigger_invalid_csr);

    printf("All trap tests complete.\n");
    return 0;
}
