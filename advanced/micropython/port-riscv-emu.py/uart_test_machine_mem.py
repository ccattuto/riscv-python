"""
Test UART using machine.mem32 (word-aligned MMIO access)
"""

import machine

UART_TX = 0x10000000
UART_RX = 0x10000004

# Write a message using machine.mem32
for c in "\r\n*** Testing machine.mem32 ***\r\n":
    machine.mem32[UART_TX] = ord(c)

# Try to read RX register
rx_val = machine.mem32[UART_RX]

# Report the result
for c in "RX register: 0x":
    machine.mem32[UART_TX] = ord(c)

# Write hex value
hex_str = f"{rx_val:08X}"
for c in hex_str:
    machine.mem32[UART_TX] = ord(c)

for c in "\r\n":
    machine.mem32[UART_TX] = ord(c)

# Check empty bit
if rx_val & 0x80000000:
    for c in "No data (empty bit set)\r\n":
        machine.mem32[UART_TX] = ord(c)
else:
    byte_val = rx_val & 0xFF
    for c in f"Got byte: 0x{byte_val:02X}\r\n":
        machine.mem32[UART_TX] = ord(c)

for c in "\r\nTest completed!\r\n":
    machine.mem32[UART_TX] = ord(c)

# Loop forever
while True:
    pass
