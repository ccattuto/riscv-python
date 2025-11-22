#
# Copyright (2025) Ciro Cattuto <ciro.cattuto@gmail.com>
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#

import os, fcntl, selectors, tty, sys
from ram import MemoryAccessError

# Base class for peripherals with memory-mapped IO
class MMIOPeripheral:
    REG_BASE = None
    REG_END = None

    def read32(self, addr):
        return 0
    
    def write32(self, addr, value):
        pass

    # a run() method, if defined, will be registered and called periodically by the emulator 
    #def run(self):
    #    pass

# mtime
class MMIOTimer(MMIOPeripheral):
    REG_BASE  = 0x0200_4000
    REG_MTIMECMP_LO = REG_BASE + 0x00
    REG_MTIMECMP_HI = REG_MTIMECMP_LO + 0x04
    REG_MTIME_LO = 0x0200_BFF8
    REG_MTIME_HI = REG_MTIME_LO + 0x04
    REG_END = REG_MTIME_HI + 0x04

    def __init__(self, cpu):
        super().__init__()
        self.cpu = cpu

        self.mtime_lo = 0
        self.mtime_hi = 0
        self.mtime_lo_updated = False
        self.mtime_hi_updated = False

    def read32(self, addr):
        if addr == self.REG_MTIME_LO:
            return self.cpu.mtime & 0xFFFFFFFF
        elif addr == self.REG_MTIME_HI:
            return self.cpu.mtime >> 32
        if addr == self.REG_MTIMECMP_LO:
            return self.cpu.mtimecmp & 0xFFFFFFFF
        elif addr == self.REG_MTIMECMP_HI:
            return self.cpu.mtimecmp >> 32
        else:
            raise MemoryAccessError(f"Invalid MMIO register read at 0x{addr:08X}")

    def write32(self, addr, value):
        if addr == self.REG_MTIMECMP_LO:
            self.cpu.mtimecmp = (self.cpu.mtimecmp & 0xFFFFFFFF_00000000) | (value & 0xFFFFFFFF)
        elif addr == self.REG_MTIMECMP_HI:
            self.cpu.mtimecmp = (self.cpu.mtimecmp & 0x00000000_FFFFFFFF) | ((value & 0xFFFFFFFF) << 32)
        elif addr == self.REG_MTIME_LO:
            self.mtime_lo = value
            self.mtime_lo_updated = True
        elif addr == self.REG_MTIME_HI:
            self.mtime_hi = value
            self.mtime_hi_updated = True
        else:
            raise MemoryAccessError(f"Invalid MMIO register write at 0x{addr:08X}")

       # atomic update of mtime after writing both high and low words
        if self.mtime_lo_updated and self.mtime_hi_updated:
            self.cpu.mtime = (self.mtime_hi << 32) | self.mtime_lo
            self.mtime_lo_updated = False
            self.mtime_hi_updated = False

# UART exposed as a host pseudo-terminal
class PtyUART(MMIOPeripheral):
    def __init__(self, reg_base=0x1000_0000, logger=None):
        super().__init__()

        self.REG_BASE   = reg_base
        self.REG_TX     = reg_base + 0x00
        self.REG_RX     = reg_base + 0x04
        self.REG_END    = reg_base + 0x08

        self.logger = logger

        # create master/slave pty pair
        self.master_fd, self.slave_fd = os.openpty()
        self.slave_name = os.ttyname(self.slave_fd)
        if self.logger is not None:
            self.logger.info(f"[UART] PTY created: {self.slave_name}")

        # put slave in raw mode so the terminal program sees bytes verbatim
        tty.setraw(self.slave_fd, when=tty.TCSANOW)

        # non-blocking master for polling
        fl = fcntl.fcntl(self.master_fd, fcntl.F_GETFL)
        fcntl.fcntl(self.master_fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

        self.rx_buf = []  # RX buffer
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.master_fd, selectors.EVENT_READ)

    # RX polling, to be called periodically by the emulator
    def run(self):
        for _key, _mask in self.selector.select(timeout=0):
            try:
                data = os.read(self.master_fd, 64)
                self.rx_buf.extend(data)
            except BlockingIOError:
                pass

    # Memory-mapped interface
    
    def read32(self, addr):
        if addr == self.REG_RX:
            self.run()
            if self.rx_buf:
                return self.rx_buf.pop(0)  # return first char in RX buffer
            else:
                return 1 << 31  # RX empty bit
        elif addr == self.REG_TX:
            return 0  # always ready to write
        else:
            raise MemoryAccessError(f"Invalid MMIO register read at 0x{addr:08X}")

    def write32(self, addr, value):
        if addr == self.REG_TX:
            try:
                os.write(self.master_fd, bytes([value & 0xFF]))
            except BlockingIOError:
                pass
        else:
            raise MemoryAccessError(f"Invalid MMIO register write at 0x{addr:08X}")

# Block device
class MMIOBlockDevice(MMIOPeripheral):
    def __init__(self, reg_base=0x1001_0000, image_path=None, ram=None, block_size=512, size=1024, logger=None):
        super().__init__()

        self.REG_BASE    = reg_base
        self.REG_CMD     = reg_base + 0x00  # 0 = read, 1 = write
        self.REG_BLK     = reg_base + 0x04  # block number
        self.REG_PTR     = reg_base + 0x08  # guest pointer to buffer
        self.REG_CTRL    = reg_base + 0x0C  # write 1 to trigger
        self.REG_STATUS  = reg_base + 0x10  # 1 = ready
        self.REG_END     = reg_base + 0x14

        self.logger = logger
        self.block_size = block_size
        self.num_blocks = size
        self.image_path = image_path
        self.ram = ram
        self.cmd = 0
        self.blk = 0
        self.ptr = 0
        self.status = 1
        self.fd = None

        self._open_or_create_image()

    def _open_or_create_image(self):
        total_bytes = self.num_blocks * self.block_size
        if not os.path.exists(self.image_path):
            if self.logger is not None:
                self.logger.info(f"[BLOCK] Creating new block device image: {self.image_path}")
            with open(self.image_path, "wb") as f:
                f.write(b"\xFF" * total_bytes)  # emulating the initial state of a blank flash

        if self.logger is not None:
            self.logger.info(f"[BLOCK] Opening block device image: {self.image_path}")
        self.fd = open(self.image_path, "r+b")  # read/write, binary

    def read32(self, addr):
        if addr == self.REG_CMD:
            return self.cmd
        elif addr == self.REG_BLK:
            return self.blk
        elif addr == self.REG_PTR:
            return self.ptr
        elif addr == self.REG_CTRL:
            return 0
        elif addr == self.REG_STATUS:
            return self.status
        else:
            raise MemoryAccessError(f"Invalid MMIO register read at 0x{addr:08X}")

    def write32(self, addr, value):
        if addr == self.REG_CMD:
            self.cmd = value
        elif addr == self.REG_BLK:
            self.blk = value
        elif addr == self.REG_PTR:
            self.ptr = value
        elif addr == self.REG_CTRL:
            if value == 1:
                self._execute_cmd()
        else:
            raise MemoryAccessError(f"Invalid MMIO register write at 0x{addr:08X}")

    def _execute_cmd(self):
        offset = self.blk * self.block_size
        if offset >= self.num_blocks * self.block_size:
            self.status = 1
            if self.logger is not None:
                self.logger.warning(f"[BLOCK] Invalid block {self.blk}")
            return

        if self.cmd == 0:  # READ
            self.fd.seek(offset)
            data = self.fd.read(self.block_size)
            self.ram.store_binary(self.ptr, data)
            #if self.logger is not None:
            #    self.logger.debug(f"[BLOCK] READ blk={self.blk} -> 0x{self.ptr:08x}")
        elif self.cmd == 1:  # WRITE
            data = self.ram.load_binary(self.ptr, self.block_size)
            self.fd.seek(offset)
            self.fd.write(data)
            self.fd.flush()
            #if self.logger is not None:
            #    self.logger.debug(f"[BLOCK] WRITE blk={self.blk} <- 0x{self.ptr:08x}")

        self.status = 1

# Terminal status line manager
class TerminalStatusLine:
    """Manages a fixed status line at the top of the terminal using ANSI escape codes."""

    def __init__(self):
        # Clear screen and set up scroll region
        # Reserve line 1 for status, allow scrolling from line 2 onwards
        print("\033[2J", end="")       # Clear screen
        print("\033[1;1H", end="")     # Move cursor to home (1,1)
        print("\033[2;r", end="")      # Set scroll region starting at line 2
        sys.stdout.flush()

        self.sections = {}
        self.last_display = ""

    def update_section(self, name, content):
        """Update a named section of the status line."""
        self.sections[name] = content
        self._redraw()

    def remove_section(self, name):
        """Remove a named section from the status line."""
        if name in self.sections:
            del self.sections[name]
            self._redraw()

    def _redraw(self):
        """Redraw the entire status line."""
        # Build the full status line
        status_parts = [f"{name}: {content}" for name, content in self.sections.items()]
        status_line = " │ ".join(status_parts) if status_parts else ""

        # Only redraw if changed
        if status_line == self.last_display:
            return
        self.last_display = status_line

        # Save cursor, move to top, clear line, print status, restore cursor
        print(f"\033[s"          # Save cursor position
              f"\033[1;1H"       # Move to line 1, column 1
              f"\033[K"          # Clear line
              f"{status_line}"   # Print status
              f"\033[u",         # Restore cursor position
              end="", flush=True)

# Multi-color LED GPIO peripheral
class LED_GPIO(MMIOPeripheral):
    """
    GPIO peripheral with 8 multi-color LEDs.
    Each LED can display 4 colors (2 bits per LED):
      00 = OFF (dark gray)
      01 = RED
      10 = GREEN
      11 = BLUE (or YELLOW)

    Register map:
      REG_BASE + 0x00: LED state (bits 15:0, 2 bits per LED)
                       Bits [1:0] = LED0, [3:2] = LED1, ..., [15:14] = LED7
    """

    # Color definitions using ANSI escape codes
    COLORS = [
        "\033[90m●\033[0m",   # 00 = OFF (dark gray circle)
        "\033[91m●\033[0m",   # 01 = RED (bright red)
        "\033[92m●\033[0m",   # 10 = GREEN (bright green)
        "\033[94m●\033[0m",   # 11 = BLUE (bright blue)
    ]

    COLOR_NAMES = ["OFF", "RED", "GRN", "BLU"]

    def __init__(self, reg_base=0x1002_0000, num_leds=8, status_line=None, logger=None):
        super().__init__()

        self.REG_BASE = reg_base
        self.REG_OUT  = reg_base + 0x00  # LED output register
        self.REG_END  = reg_base + 0x04

        self.num_leds = num_leds
        self.led_state = 0  # 2 bits per LED
        self.status_line = status_line
        self.logger = logger

        if self.logger is not None:
            self.logger.info(f"[LED_GPIO] Initialized with {num_leds} LEDs at 0x{reg_base:08X}")

        self._update_display()

    def read32(self, addr):
        if addr == self.REG_OUT:
            return self.led_state
        else:
            raise MemoryAccessError(f"Invalid MMIO register read at 0x{addr:08X}")

    def write32(self, addr, value):
        if addr == self.REG_OUT:
            # Mask to 2 bits per LED
            mask = (1 << (self.num_leds * 2)) - 1
            self.led_state = value & mask
            self._update_display()
        else:
            raise MemoryAccessError(f"Invalid MMIO register write at 0x{addr:08X}")

    def _update_display(self):
        """Update the terminal status line with current LED states."""
        if not self.status_line:
            return

        # Build LED display string (right to left: LED7 ... LED0)
        led_display = []
        for i in range(self.num_leds - 1, -1, -1):
            color_bits = (self.led_state >> (i * 2)) & 0b11
            led_display.append(self.COLORS[color_bits])

        led_str = " ".join(led_display)

        # Add hex representation
        display_text = f"{led_str}  [0x{self.led_state:04X}]"

        self.status_line.update_section("LEDs", display_text)
