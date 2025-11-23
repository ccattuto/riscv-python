// Imported via MICROPY_PY_MACHINE_INCLUDEFILE in mpconfigport.h

// Provide mp_machine_idle implementation
static void mp_machine_idle(void) {
    // In a real embedded system, this would execute WFI (Wait For Interrupt)
    // For the emulator, we just return immediately
}
