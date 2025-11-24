import machine

# UART memory-mapped registers at 0x10000000
UART_TX = 0x10000000
UART_RX = 0x10000004

# UART I/O functions
def uart_putc(c):
    """Write a character to UART"""
    machine.mem32[UART_TX] = ord(c) if isinstance(c, str) else c

def uart_getc():
    """Read a character from UART (blocking)"""
    while True:
        val = machine.mem32[UART_RX] & 0xFFFFFFFF
        if not (val & 0x80000000):  # Check empty bit
            return val & 0xFF

uart_getc()

while True:
	pass
