/*
 * Port-specific machine module implementation for RISC-V emulator
 */

#ifndef MICROPY_INCLUDED_RISCVEMU_MODMACHINE_H
#define MICROPY_INCLUDED_RISCVEMU_MODMACHINE_H

#include "py/obj.h"

// Minimal idle implementation - does nothing in emulator
// Must be static inline because extmod/modmachine.c declares it as static
static inline void mp_machine_idle(void) {
    // In a real embedded system, this would execute WFI (Wait For Interrupt)
    // For the emulator, we just return immediately
}

#endif // MICROPY_INCLUDED_RISCVEMU_MODMACHINE_H
