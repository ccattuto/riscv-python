/*
Copyright (2025) Ciro Cattuto <ciro.cattuto@gmail.com>

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
*/

#ifndef __RISCV_EMU__
#define __RISCV_EMU__

#include <stdint.h>


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


// logging helpers
// (they used the bypass syscalls > 0xFFFF0000 and do not need Newlib)

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

#define EMU_LOG_STR_XINT(ptr, value) do {                   \
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
// (disable_traps also sets mtvec=0 so that syscalls are handled by the emulator)

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
