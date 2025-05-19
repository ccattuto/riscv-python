#include "shared-bindings/busio/UART.h"
#include "serial.h"

// extern busio_uart_obj_t *default_uart_ptr;

/*
void board_serial_write_substring(const char *str, uint32_t length) {
    common_hal_busio_uart_write(default_uart_ptr, (const uint8_t *) str, length, NULL);
}

bool board_serial_bytes_available(void) {
	return common_hal_busio_uart_rx_characters_available(default_uart_ptr);
}

int board_serial_read_char(void) {
    uint8_t c;
    int errcode;
    if (common_hal_busio_uart_read(default_uart_ptr, &c, 1, &errcode) == 0) {
        return -1;
    }
    return c;
}
*/
