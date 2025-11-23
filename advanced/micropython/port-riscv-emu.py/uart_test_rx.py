"""
Test UART RX register read
"""

import uctypes

UART_TX = 0x10000000
UART_RX = 0x10000004

# Create structs for both registers
tx_reg = uctypes.struct(UART_TX, {"val": uctypes.UINT32 | 0}, uctypes.LITTLE_ENDIAN)
rx_reg = uctypes.struct(UART_RX, {"val": uctypes.UINT32 | 0}, uctypes.LITTLE_ENDIAN)

# Write a prompt
for c in "\r\nReading RX register...\r\n":
    tx_reg.val = ord(c)

# Try to read RX register (this is where it might fail with byte access)
rx_val = rx_reg.val

# Report the result
for c in "RX value: ":
    tx_reg.val = ord(c)

# Write the hex value
hex_str = hex(rx_val)
for c in hex_str:
    tx_reg.val = ord(c)

for c in "\r\n":
    tx_reg.val = ord(c)

# Check if empty bit is set
if rx_val & 0x80000000:
    for c in "Empty bit set (no data)\r\n":
        tx_reg.val = ord(c)
else:
    for c in "Data available!\r\n":
        tx_reg.val = ord(c)

# Loop forever
while True:
    pass
