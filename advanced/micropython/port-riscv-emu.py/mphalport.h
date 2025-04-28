#ifndef MICROPY_INCLUDED_MPHALPORT_H
#define MICROPY_INCLUDED_MPHALPORT_H

#include "py/mpconfig.h"

mp_uint_t mp_hal_stdout_tx_strn(const char *str, size_t len);

int mp_hal_stdin_rx_chr(void);

static inline mp_uint_t mp_hal_ticks_ms(void) {
    return 0;
}

static inline void mp_hal_set_interrupt_char(char c) {
}

#endif
