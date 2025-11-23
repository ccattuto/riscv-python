"""
Absolute minimal UART test - direct memory write using machine.mem32
"""

import machine

UART_TX = 0x10000000

# Write message byte by byte
machine.mem32[UART_TX] = ord('\r')
machine.mem32[UART_TX] = ord('\n')
machine.mem32[UART_TX] = ord('*')
machine.mem32[UART_TX] = ord('*')
machine.mem32[UART_TX] = ord('*')
machine.mem32[UART_TX] = ord(' ')
machine.mem32[UART_TX] = ord('T')
machine.mem32[UART_TX] = ord('E')
machine.mem32[UART_TX] = ord('S')
machine.mem32[UART_TX] = ord('T')
machine.mem32[UART_TX] = ord('\r')
machine.mem32[UART_TX] = ord('\n')

# Loop forever
while True:
    pass
