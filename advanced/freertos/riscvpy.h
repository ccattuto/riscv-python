#ifndef __RISCV_EMU__
#define __RISCV_EMU__

// CSR helpers

#define READ_CSR(reg) ({ unsigned int __tmp; \
    asm volatile ("csrr %0, " #reg : "=r"(__tmp)); \
    __tmp; })

#define WRITE_CSR(reg, val) ({ \
    asm volatile ("csrw " #reg ", %0" :: "rK"(val)); })

#define SET_CSR(reg, bitmask) ({ unsigned int __tmp; \
    asm volatile ("csrrs %0, " #reg ", %1" : "=r"(__tmp) : "rK"(bitmask)); \
    __tmp; })

#define CLEAR_CSR(reg, bitmask) ({ unsigned int __tmp; \
    asm volatile ("csrrc %0, " #reg ", %1" : "=r"(__tmp) : "rK"(bitmask)); \
    __tmp; })


// logging helpers (they used the bypass syscalls >= 0xFFFF0000)

#define EMU_LOG_INT(value) do {                             \
    asm volatile (                                          \
        "lui a7, 0xFFFF0\n"                                 \
        "addi a7, a7, 1\n"                                  \
        "mv a0, %0\n"                                       \
        "ebreak\n"                                          \
        :: "r"(value) : "a0", "a7");                        \
} while (0)

#define EMU_LOG_STR(ptr) do {                               \
    asm volatile (                                          \
        "lui a7, 0xFFFF0\n"                                 \
        "addi a7, a7, 2\n"                                  \
        "mv a0, %0\n"                                       \
        "ebreak\n"                                          \
        :: "r"(ptr) : "a0", "a7");                          \
} while (0)

#define EMU_LOG_STR_INT(ptr, value) do {                    \
    asm volatile (                                          \
        "lui a7, 0xFFFF0\n"                                 \
        "addi a7, a7, 3\n"                                  \
        "mv a0, %0\n"                                       \
        "mv a1, %1\n"                                       \
        "ebreak\n"                                          \
        :: "r"(ptr), "r"(value) : "a0", "a1", "a7");        \
} while (0)

#define EMU_LOG_STR_XINT(ptr, value) do {                    \
    asm volatile (                                          \
        "lui a7, 0xFFFF0\n"                                 \
        "addi a7, a7, 4\n"                                  \
        "mv a0, %0\n"                                       \
        "mv a1, %1\n"                                       \
        "ebreak\n"                                          \
        :: "r"(ptr), "r"(value) : "a0", "a1", "a7");        \
} while (0)

#define EMU_LOG_REGS() do {                                 \
    asm volatile (                                          \
        "lui a7, 0xFFFF0\n"                                 \
        "addi a7, a7, 0\n"                                  \
        "ebreak\n"                                          \
        ::  : "a7");                                        \
} while (0)


// suspend/restore traps

#define disable_traps(mstatus_mask) do {                    \
    clear_csr(mie, 1 << 7);                                 \
    clear_csr(mstatus, mstatus_mask);                       \
    write_csr(mtvec, 0);                                    \
} while (0)

#define enable_traps(trap_handler_addr, mstatus_mask) do {  \
    write_csr(mtvec, (uintptr_t)(trap_handler_addr));       \
    set_csr(mie, 1 << 7);                                   \
    set_csr(mstatus, mstatus_mask);                         \
} while (0)

#endif /* __RISCV_EMU__ */
