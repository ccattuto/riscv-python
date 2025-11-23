"""
Simple UART example using machine.mem32 for word-aligned MMIO access
Demonstrates printing strings and reading characters
"""

import machine

# UART memory-mapped registers
UART_TX = 0x10000000
UART_RX = 0x10000004
UART_RX_EMPTY = 0x80000000  # Bit 31 indicates no data available


def putchar(c):
    """Write a single character to UART"""
    machine.mem32[UART_TX] = ord(c) if isinstance(c, str) else c


def print_string(s):
    """Print a string to UART"""
    for c in s:
        putchar(c)


def getchar():
    """Read a single character from UART (blocking)"""
    while True:
        val = machine.mem32[UART_RX]
        if not (val & UART_RX_EMPTY):  # Check if data is available
            return val & 0xFF  # Return lower 8 bits


# Example usage
print_string("Hello from MicroPython!\r\n")
print_string("Using machine.mem32 for word-aligned MMIO access\r\n")
print_string("\r\nType a character: ")

# Read one character and echo it back
c = getchar()
putchar(c)
print_string("\r\n")

print_string("You typed: 0x")
# Print hex value
hex_str = "%02X" % c
print_string(hex_str)
print_string("\r\n")

print_string("Done!\r\n")

# Loop forever
while True:
    pass
