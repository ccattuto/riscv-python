/*
 * Port-specific machine module implementation for RISC-V emulator
 * This file is included by extmod/modmachine.c via MICROPY_PY_MACHINE_INCLUDEFILE
 */

// Provide mp_machine_idle implementation
// This fulfills the forward declaration in extmod/modmachine.c
static void mp_machine_idle(void) {
    // In a real embedded system, this would execute WFI (Wait For Interrupt)
    // For the emulator, we just return immediately
}
