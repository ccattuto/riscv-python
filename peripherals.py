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

import os, fcntl, selectors, tty

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

# UART exposed as a host pseudo-terminal
class PtyUART(MMIOPeripheral):
    REG_BASE  = 0x1000_0000
    REG_TX = REG_BASE + 0x00
    REG_RX = REG_BASE + 0x04
    REG_END = REG_BASE + 0x08

    def __init__(self, logger=None):
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
        return 0

    def write32(self, addr, value):
        if addr == self.REG_TX:
            try:
                os.write(self.master_fd, bytes([value & 0xFF]))
            except BlockingIOError:
                pass
