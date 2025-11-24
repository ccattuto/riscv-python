/*
 * HAL implementation for HEADLESS mode
 * Provides no-op stdio functions (print/input have no effect)
 */

#include "py/mphal.h"

// stdin: Always return immediately with 0
int mp_hal_stdin_rx_chr(void) {
    return 0;
}

// stdout: Discard all output
mp_uint_t mp_hal_stdout_tx_strn(const char *str, size_t len) {
    (void)str;
    (void)len;
    return len;  // Pretend we wrote everything
}

void mp_hal_delay_ms(mp_uint_t ms) {
    // No-op for headless mode
    (void)ms;
}
