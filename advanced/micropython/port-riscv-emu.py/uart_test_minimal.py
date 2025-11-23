"""
Absolute minimal UART test - direct memory write without struct or functions
"""

import uctypes

UART_TX = 0x10000000

# Create a single UINT32 at the TX address
tx_reg = uctypes.struct(UART_TX, {"val": uctypes.UINT32 | 0}, uctypes.LITTLE_ENDIAN)

# Write message byte by byte
tx_reg.val = ord('\r')
tx_reg.val = ord('\n')
tx_reg.val = ord('*')
tx_reg.val = ord('*')
tx_reg.val = ord('*')
tx_reg.val = ord(' ')
tx_reg.val = ord('T')
tx_reg.val = ord('E')
tx_reg.val = ord('S')
tx_reg.val = ord('T')
tx_reg.val = ord('\r')
tx_reg.val = ord('\n')

# Loop forever
while True:
    pass
