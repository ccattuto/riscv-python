/*
 * Port-specific machine module implementations
 */

#ifndef MICROPY_INCLUDED_RISCVEMU_MODMACHINE_H
#define MICROPY_INCLUDED_RISCVEMU_MODMACHINE_H

#include "py/obj.h"

// Minimal idle implementation - does nothing in emulator
static void mp_machine_idle(void) {
    // In a real embedded system, this would put the CPU in low-power mode
    // For the emulator, we just return
}

#endif // MICROPY_INCLUDED_RISCVEMU_MODMACHINE_H
