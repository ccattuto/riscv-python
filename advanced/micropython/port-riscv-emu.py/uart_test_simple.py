"""
Minimal UART test - just write to UART using machine.mem32, no REPL
"""

import machine

# UART memory-mapped registers at 0x10000000
UART_TX = 0x10000000
UART_RX = 0x10000004

def uart_putc(c):
    """Write a character to UART"""
    machine.mem32[UART_TX] = ord(c)

def uart_write(s):
    """Write a string to UART"""
    for c in s:
        uart_putc(c)

# Simple test - just write and loop forever
uart_write("\r\n=== UART Test Starting ===\r\n")
uart_write("If you see this, machine.mem32 UART works!\r\n")
uart_write("Entering infinite loop...\r\n")

count = 0
while True:
    count += 1
    if count % 100000 == 0:
        uart_write("Alive: ")
        uart_write(str(count))
        uart_write("\r\n")
