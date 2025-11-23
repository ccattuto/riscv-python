"""
Minimal UART test - just write to UART, no REPL
"""

import uctypes

# UART memory-mapped registers at 0x10000000
UART_BASE = 0x10000000

# Define UART register layout
uart_layout = {
    "TX": uctypes.UINT32 | 0x00,
    "RX": uctypes.UINT32 | 0x04,
}

# Create UART structure
uart = uctypes.struct(UART_BASE, uart_layout, uctypes.LITTLE_ENDIAN)

def uart_putc(c):
    """Write a character to UART"""
    uart.TX = ord(c) if isinstance(c, str) else c

def uart_write(s):
    """Write a string to UART"""
    for c in s:
        uart_putc(c)

# Simple test - just write and loop forever
uart_write("\r\n*** UART Test Starting ***\r\n")
uart_write("If you see this, uctypes UART works!\r\n")
uart_write("Entering infinite loop...\r\n")

count = 0
while True:
    count += 1
    if count % 100000 == 0:
        uart_write(f"Alive: {count}\r\n")
