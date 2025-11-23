"""
Python REPL using uctypes to access memory-mapped UART
For use in EMBEDDED_SILENT mode - demonstrates pure Python hardware control
"""

import uctypes

# UART memory-mapped registers at 0x10000000
UART_BASE = 0x10000000

# Define UART register layout
UART_LAYOUT = {
    "TX": uctypes.UINT32 | 0x00,  # Transmit register
    "RX": uctypes.UINT32 | 0x04,  # Receive register (bit 31 = empty)
}

# Create UART structure
uart = uctypes.struct(UART_BASE, UART_LAYOUT, uctypes.LITTLE_ENDIAN)

# UART I/O functions
def uart_putc(c):
    """Write a character to UART"""
    uart.TX = ord(c) if isinstance(c, str) else c

def uart_getc():
    """Read a character from UART (blocking)"""
    while True:
        val = uart.RX
        if not (val & 0x80000000):  # Check empty bit
            return val & 0xFF

def uart_write(s):
    """Write a string to UART"""
    for c in s:
        uart_putc(c)

def uart_readline():
    """Read a line from UART (until newline)"""
    line = []
    while True:
        c = uart_getc()
        if c == 0x0D or c == 0x0A:  # CR or LF
            uart_write('\r\n')
            break
        elif c == 0x7F or c == 0x08:  # Backspace or DEL
            if line:
                line.pop()
                uart_write('\b \b')  # Erase character on terminal
        elif c >= 0x20 and c < 0x7F:  # Printable character
            line.append(chr(c))
            uart_putc(c)  # Echo
    return ''.join(line)

# Simple REPL implementation
def repl():
    """Python REPL using UART via uctypes"""
    uart_write('\r\n')
    uart_write('=' * 50 + '\r\n')
    uart_write('Python REPL via uctypes UART\r\n')
    uart_write('MicroPython on RISC-V (EMBEDDED_SILENT mode)\r\n')
    uart_write('=' * 50 + '\r\n')
    uart_write('\r\n')

    # Global namespace for REPL
    repl_globals = {'__name__': '__main__'}

    # Add useful modules to namespace
    repl_globals['uctypes'] = uctypes
    repl_globals['uart'] = uart
    repl_globals['uart_write'] = uart_write

    while True:
        try:
            # Prompt
            uart_write('>>> ')

            # Read input
            line = uart_readline()

            if not line:
                continue

            # Handle special commands
            if line == 'exit':
                uart_write('Exiting REPL...\r\n')
                break
            elif line == 'help':
                uart_write('Available: uctypes, uart, uart_write\r\n')
                uart_write('Type exit to quit\r\n')
                continue

            # Try to evaluate as expression first
            try:
                result = eval(line, repl_globals)
                if result is not None:
                    uart_write(repr(result) + '\r\n')
            except SyntaxError:
                # If eval fails, try exec
                exec(line, repl_globals)

        except Exception as e:
            uart_write('Error: ' + str(e) + '\r\n')

# Demo functions accessible from REPL
def demo_uart():
    """Demonstrate direct UART register access"""
    uart_write('\r\nDirect UART register access:\r\n')
    uart_write(f'UART_BASE: 0x{UART_BASE:08X}\r\n')
    uart_write(f'TX register: 0x{UART_BASE:08X}\r\n')
    uart_write(f'RX register: 0x{UART_BASE+4:08X}\r\n')

def demo_memory():
    """Demonstrate uctypes memory access"""
    # Read some memory
    uart_write('\r\nMemory access demo:\r\n')
    mem = uctypes.struct(0x1000, {"value": uctypes.UINT32 | 0}, uctypes.LITTLE_ENDIAN)
    uart_write(f'Value at 0x1000: 0x{mem.value:08X}\r\n')

# Main entry point - execute immediately when frozen
# Run REPL
repl()

uart_write('\r\nREPL exited. System halted.\r\n')
