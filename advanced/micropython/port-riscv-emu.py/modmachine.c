/*
 * This file is part of the MicroPython project, http://micropython.org/
 *
 * Port-specific machine module implementation for RISC-V emulator
 */

#include "py/runtime.h"

// Minimal idle implementation - does nothing in emulator
static void mp_machine_idle(void) {
    // In a real embedded system, this would put the CPU in low-power mode (WFI instruction)
    // For the emulator, we just return immediately
}
