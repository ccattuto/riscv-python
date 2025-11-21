"""
Simple demo of uctypes for memory-mapped UART access
For use in EMBEDDED_SILENT mode
"""

import uctypes

# UART memory-mapped registers at 0x10000000
UART_BASE = 0x10000000

# Define UART register layout
uart_layout = {
    "TX": uctypes.UINT32 | 0x00,  # Transmit register
    "RX": uctypes.UINT32 | 0x04,  # Receive register
}

# Create UART structure
uart = uctypes.struct(UART_BASE, uart_layout, uctypes.LITTLE_ENDIAN)

def uart_print(s):
    """Print string to UART using uctypes"""
    for c in s:
        uart.TX = ord(c)

# Demo
uart_print("\r\n")
uart_print("=" * 50 + "\r\n")
uart_print("uctypes UART Demo\r\n")
uart_print("=" * 50 + "\r\n")
uart_print("\r\n")

# Show direct register access
uart_print("Direct UART register access:\r\n")
uart_print(f"  UART base address: 0x{UART_BASE:08X}\r\n")
uart_print(f"  TX register offset: 0x00\r\n")
uart_print(f"  RX register offset: 0x04\r\n")
uart_print("\r\n")

# Demonstrate writing to TX register
uart_print("Writing bytes directly to TX register:\r\n")
for i, char in enumerate("Hello UART!"):
    uart.TX = ord(char)
    if i < len("Hello UART!") - 1:
        uart_print(", ")
uart_print("\r\n\r\n")

# Show memory layout
uart_print("UART struct layout:\r\n")
uart_print(f"  struct address: {id(uart)}\r\n")
uart_print(f"  TX field: uctypes.UINT32 @ +0x00\r\n")
uart_print(f"  RX field: uctypes.UINT32 @ +0x04\r\n")
uart_print("\r\n")

# Demonstrate reading RX register
uart_print("Reading RX register (non-blocking):\r\n")
rx_val = uart.RX
if rx_val & 0x80000000:
    uart_print("  No data available (bit 31 set)\r\n")
else:
    uart_print(f"  Received byte: 0x{rx_val & 0xFF:02X}\r\n")
uart_print("\r\n")

# Integer array demo
uart_print("Integer array operations (no floats):\r\n")
data = [i * i for i in range(10)]
uart_print(f"  Squares: {data}\r\n")
uart_print(f"  Sum: {sum(data)}\r\n")
uart_print("\r\n")

# Struct packing demo
import struct
packed = struct.pack('HHL', 0xABCD, 0x1234, 0xDEADBEEF)
uart_print("Struct packing demo:\r\n")
uart_print(f"  Packed: {' '.join(f'{b:02X}' for b in packed)}\r\n")
unpacked = struct.unpack('HHL', packed)
uart_print(f"  Unpacked: {unpacked}\r\n")
uart_print("\r\n")

uart_print("=" * 50 + "\r\n")
uart_print("Demo completed successfully!\r\n")
uart_print("=" * 50 + "\r\n")
