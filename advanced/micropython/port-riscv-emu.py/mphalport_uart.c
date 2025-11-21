#include <stddef.h>
#include "py/mpconfig.h"

/*
 * UART via memory-mapped I/O
 * Base address: 0x10000000
 * REG_TX (0x00): Write byte to transmit
 * REG_RX (0x04): Read byte (bit 31 set if no data available)
 */

#define UART_BASE 0x10000000
#define UART_TX   (*(volatile unsigned int *)(UART_BASE + 0x00))
#define UART_RX   (*(volatile unsigned int *)(UART_BASE + 0x04))
#define UART_RX_EMPTY (1U << 31)

// Send string to UART
mp_uint_t mp_hal_stdout_tx_strn(const char *str, size_t len) {
    for (size_t i = 0; i < len; i++) {
        UART_TX = (unsigned char)str[i];
    }
    return len;
}

// Receive single character from UART (blocking)
int mp_hal_stdin_rx_chr(void) {
    unsigned int val;
    // Wait until data is available
    do {
        val = UART_RX;
    } while (val & UART_RX_EMPTY);

    return val & 0xFF;
}
