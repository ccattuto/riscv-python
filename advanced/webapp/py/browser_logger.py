"""
Browser Logger - Logging interface for browser environment
Outputs to JavaScript console and optionally to terminal with ANSI colors
"""

import js

# ANSI color codes for terminal output (matching riscv-emu.py)
LOG_COLORS = {
    'DEBUG': '\033[35m',    # Magenta
    'INFO': '\033[32m',     # Green
    'WARNING': '\033[33m',  # Yellow
    'ERROR': '\033[31m'     # Red
}
RESET_COLOR = '\033[0m'

class BrowserLogger:
    """Logger that outputs to JavaScript console and terminal"""

    def __init__(self, name='emulator', write_to_terminal=True):
        self.name = name
        self.write_to_terminal = write_to_terminal

    def _terminal_write(self, level, msg):
        """Write colored message to terminal"""
        if self.write_to_terminal and hasattr(js.window, 'emulatorTerminal'):
            color = LOG_COLORS.get(level, '')
            colored_msg = f'{color}[{level}] {msg}{RESET_COLOR}\r\n'
            # Write directly to terminal (xterm.js supports ANSI colors)
            js.window.emulatorTerminal.terminal.write(colored_msg)

    def debug(self, msg):
        """Log debug message"""
        js.console.log(f'[{self.name}] DEBUG: {msg}')
        self._terminal_write('DEBUG', msg)

    def info(self, msg):
        """Log info message"""
        js.console.info(f'[{self.name}] INFO: {msg}')
        self._terminal_write('INFO', msg)

    def warning(self, msg):
        """Log warning message"""
        js.console.warn(f'[{self.name}] WARNING: {msg}')
        self._terminal_write('WARNING', msg)

    def error(self, msg):
        """Log error message"""
        js.console.error(f'[{self.name}] ERROR: {msg}')
        self._terminal_write('ERROR', msg)

# Create default logger instance
log = BrowserLogger()
