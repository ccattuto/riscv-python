#include <stddef.h>
#include "py/mpconfig.h"

/*
 * Silent I/O mode - no hardware interaction
 * For embedded scripts that don't need I/O
 */

// Discard all output
mp_uint_t mp_hal_stdout_tx_strn(const char *str, size_t len) {
    (void)str;
    (void)len;
    return len;  // Pretend we wrote everything
}

// No input available
int mp_hal_stdin_rx_chr(void) {
    return -1;  // Always return "no data"
}
