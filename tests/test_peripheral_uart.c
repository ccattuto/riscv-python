// UART example

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

#define UART_BASE 0x10000000
#define TXDATA (*(volatile uint32_t *)(UART_BASE + 0))
#define RXDATA (*(volatile uint32_t *)(UART_BASE + 4))

void uart_putchar(char c) { while (TXDATA & 0x80000000); TXDATA = c; }
char uart_getchar(void) { while (RXDATA & 0x80000000); return RXDATA & 0xFF; }

int main(void) {
    const char msg[] = "Hello UART!\r\n";
    char *s;
    volatile char ch;

    while (1) {
        // print message
        s = (char *) msg;
        while (*s) uart_putchar(*s++);

        // read char
        ch = uart_getchar();
    }

    return 0;
}
