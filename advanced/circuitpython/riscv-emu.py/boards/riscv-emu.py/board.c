#include <stdint.h>
#include "supervisor/board.h"
#include "common-hal/busio/UART.h"
#include "shared-bindings/busio/UART.h"
#include "supervisor/shared/serial.h"
#include "supervisor/background_callback.h"
#include "shared/runtime/interrupt_char.h"
#include "py/mphal.h"
#include "py/runtime.h"
#include "supervisor/internal_flash.h"

#include "riscv-py.h"

extern busio_uart_obj_t console_uart;
extern void setup_timer_interrupt(void);
void kbd_interrupt_background_task(void *data);
background_callback_t kbd_interrupt_background_cb;

static uint32_t counter = 0;

void kbd_interrupt_background_task(void *data) {
    unsigned char c;

    if ((++counter & 0xFF) == 0) {
        if (common_hal_busio_uart_rx_characters_available(&console_uart)) {
            common_hal_busio_uart_read(&console_uart, &c, 1, NULL);
            if ((c == mp_interrupt_char) && !mp_hal_is_interrupted()) {
                mp_sched_keyboard_interrupt();
                mp_handle_pending(true);
            }
        }
   	}
 
    background_callback_add_core(&kbd_interrupt_background_cb);
}       

void board_init(void) {
    //mp_hal_set_interrupt_char(0x03);
    kbd_interrupt_background_cb.fun = &kbd_interrupt_background_task;
    kbd_interrupt_background_cb.data = NULL;
    background_callback_add_core(&kbd_interrupt_background_cb);

    setup_timer_interrupt();
}

void board_serial_write_substring(const char *text, uint32_t len) {
    int errcode;
    common_hal_busio_uart_write(&console_uart, (const uint8_t *)text, len, &errcode);
}

