#include <unistd.h>
#include <stddef.h>
#include "py/mpconfig.h"

mp_uint_t mp_hal_stdout_tx_strn(const char *str, size_t len) {
    return write(1, str, len);
}

int mp_hal_stdin_rx_chr(void) {
    unsigned char c;
    // Blocking read from stdin (fd = 0)
    if (read(0, &c, 1) == 1) {
        return c;
    } else {
        return -1; // or handle error
    }
}
