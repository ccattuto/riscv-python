/*
 * Port-specific machine module functions
 */

#include "py/runtime.h"

// Minimal idle implementation - does nothing in emulator
void mp_machine_idle(void) {
    // In a real embedded system, this would put the CPU in low-power mode
    // For the emulator, we just return
}
