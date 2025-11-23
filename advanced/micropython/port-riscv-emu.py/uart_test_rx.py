"""
Test UART RX register read using machine.mem32
"""

import machine

UART_TX = 0x10000000
UART_RX = 0x10000004

# Write a prompt
for c in "\r\nReading RX register...\r\n":
    machine.mem32[UART_TX] = ord(c)

# Read RX register with proper word-aligned access
rx_val = machine.mem32[UART_RX] & 0xFFFFFFFF

# Report the result
for c in "RX value: ":
    machine.mem32[UART_TX] = ord(c)

# Write the hex value
hex_str = hex(rx_val)
for c in hex_str:
    machine.mem32[UART_TX] = ord(c)

for c in "\r\n":
    machine.mem32[UART_TX] = ord(c)

# Check if empty bit is set
if rx_val & 0x80000000:
    for c in "Empty bit set (no data)\r\n":
        machine.mem32[UART_TX] = ord(c)
else:
    for c in "Data available!\r\n":
        machine.mem32[UART_TX] = ord(c)

# Loop forever
while True:
    pass
