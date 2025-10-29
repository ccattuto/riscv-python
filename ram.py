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

from machine import MachineError
import random

# We provide multiple implementations of the RAM class, each with a different set of features.
# This is verbose but outweights the performance cost of having conditions along the hot memory access path
# (load_word and store_store functions, in particular). Available classes are:
#
# - RAM:            Base RAM class: fast, no address checks, no MMIO
# - SafeRAM:        Safe RAM class: all accesses are checked, no MMIO
# - SafeRAMOffset:  Safe RAM class + optional base address (necessary for unit tests), no MMIO
# - RAM_MMIO:       RAM class with MMIO
# - SafeRAM_MMIO:   Safe RAM class with MMIO, all accesses are checked
#

class MemoryAccessError(MachineError):
    pass

def initialize_ram(ram, fill='0x00'):
    if fill == 'random':
        for i in range(ram.size):
            ram.memory[i] = random.getrandbits(8)
    elif fill == 'addr':
        for i in range(ram.size):
            ram.memory[i] = i & 0xFF
    else:
        try:
            value = int(fill, 0) & 0xFF
        except ValueError:
            raise ValueError(f"Invalid --init-ram value: {fill}")
        for i in range(ram.size):
            ram.memory[i] = value

# Base RAM class: fast, no address checks, no MMIO
class RAM:
    def __init__(self, size=1024*1024, init=None, logger=None, padding=4):
        self.memory = bytearray(size + padding)
        self.memory32 = memoryview(self.memory ).cast("I")  # word view
        self.size = size
        self.logger = logger
        if init is not None and init != 'zero':
            initialize_ram(self, init)

    def load_byte(self, addr, signed=True):
        try:
            val = self.memory[addr]
            return val if not signed or val < 0x80 else val - 0x100
        except IndexError:
            raise MemoryAccessError(f"Access out of bounds: 0x{addr:08X} (+{1})")

    def load_half(self, addr, signed=True):
        try:
            val = self.memory[addr] | (self.memory[addr+1] << 8)
            return val if not signed or val < 0x8000 else val - 0x10000
        except IndexError:
            raise MemoryAccessError(f"Access out of bounds: 0x{addr:08X} (+{2})")

    def load_word(self, addr):  # always unsigned (performance)
        try:
            if addr & 0x3 == 0:
                return self.memory32[addr >> 2]  # word aligned
            else:
                return self.memory[addr] | (self.memory[addr+1] << 8) | self.memory[addr+2] << 16 | self.memory[addr+3] << 24
        except IndexError:
            raise MemoryAccessError(f"Access out of bounds: 0x{addr:08X} (+{4})")

    def store_byte(self, addr, value):
        try:
            self.memory[addr] = value & 0xFF
        except IndexError:
            raise MemoryAccessError(f"Access out of bounds: 0x{addr:08X} (+{1})")

    def store_half(self, addr, value):
        try:
            value &= 0xFFFF  # make it unsigned
            self.memory[addr] = value & 0xFF
            self.memory[addr+1] = (value >> 8) & 0xFF
        except IndexError:
            raise MemoryAccessError(f"Access out of bounds: 0x{addr:08X} (+{2})")

    def store_word(self, addr, value):
        try:
            value &= 0xFFFFFFFF  # make it unsigned
            if addr & 0x3 == 0:
                self.memory32[addr >> 2] = value
            else:
                self.memory[addr] = value & 0xFF
                self.memory[addr+1] = (value >> 8) & 0xFF
                self.memory[addr+2] = (value >> 16) & 0xFF
                self.memory[addr+3] = (value >> 24) & 0xFF
        except IndexError:
            raise MemoryAccessError(f"Access out of bounds: 0x{addr:08X} (+{4})")

    def load_binary(self, addr, n):
        return self.memory[addr:addr+n]

    def store_binary(self, addr, binary):
        try:
            self.memory[addr:addr+len(binary)] = binary
        except (IndexError, BufferError):
            raise MemoryAccessError(f"Access out of bounds: 0x{addr:08X}-0x{addr+len(binary)}")

    def load_cstring(self, addr, max_len=1024):
        end = min(addr + max_len, self.size)
        memory_slice = self.memory[addr:end]
        nul_index = memory_slice.find(0)
        if nul_index == -1:
            raise MemoryAccessError(f"Exceeded maximum length while reading C string at 0x{addr:08X}")
        return memory_slice[:nul_index].decode('utf-8', errors='replace')

# Safe RAM class: all accesses are checked, no MMIO
class SafeRAM(RAM):
    def __init__(self, size=1024*1024, init=None, logger=None):
        super().__init__(size, init, logger)

    def check(self, addr, n):
        if addr < 0 or addr + n > self.size:
            raise MemoryAccessError(f"Access out of bounds: 0x{addr:08X} (+{n})")

    def load_byte(self, addr, signed=True):
        self.check(addr, 1)
        val = self.memory[addr]
        return val if not signed or val < 0x80 else val - 0x100
 
    def load_half(self, addr, signed=True):
        self.check(addr, 2)
        val = self.memory[addr] | (self.memory[addr+1] << 8)
        return val if not signed or val < 0x8000 else val - 0x10000

    def load_word(self, addr):  # always unsigned (performance)
        self.check(addr, 4)
        if addr & 0x3 == 0:
            return self.memory32[addr >> 2]  # word aligned
        else:
            return self.memory[addr] | (self.memory[addr+1] << 8) | self.memory[addr+2] << 16 | self.memory[addr+3] << 24

    def store_byte(self, addr, value):
        self.check(addr, 1)
        self.memory[addr] = value & 0xFF

    def store_half(self, addr, value):
        self.check(addr, 2)
        value &= 0xFFFF  # make it unsigned
        self.memory[addr] = value & 0xFF
        self.memory[addr+1] = (value >> 8) & 0xFF

    def store_word(self, addr, value):
        self.check(addr, 4)
        value &= 0xFFFFFFFF  # make it unsigned
        if addr & 0x3 == 0:
            self.memory32[addr >> 2] = value
        else:
            self.memory[addr] = value & 0xFF
            self.memory[addr+1] = (value >> 8) & 0xFF
            self.memory[addr+2] = (value >> 16) & 0xFF
            self.memory[addr+3] = (value >> 24) & 0xFF

    def load_binary(self, addr, n):
        self.check(addr, n)
        return self.memory[addr:addr+n]

    def store_binary(self, addr, binary):
        self.check(addr, n=len(binary))
        self.memory[addr:addr+len(binary)] = binary

    def load_cstring(self, addr, max_len=1024):
        if addr < 0 or addr >= self.size:
            raise MemoryAccessError(f"Invalid start address reading C string: 0x{addr:08X}")
        end = min(addr + max_len, self.size)
        memory_slice = self.memory[addr:end]
        nul_index = memory_slice.find(0)
        if nul_index == -1:
            raise MemoryAccessError(f"Exceeded maximum length while reading C string at 0x{addr:08X}")
        return memory_slice[:nul_index].decode('utf-8', errors='replace')

# Safe RAM class + optional base address (necessary for unit tests), no MMIO
class SafeRAMOffset(RAM):
    def __init__(self, size=1024*1024, base_addr=0, init=None, logger=None):
        super().__init__(size, init, logger)
        self.base_addr = base_addr
      
    def check(self, addr, n):
        if addr < 0 or addr + n > self.size:
            raise MemoryAccessError(f"Access out of bounds: 0x{self.base_addr+addr:08X} (+{n})")

    def load_byte(self, addr, signed=True):
        addr -= self.base_addr
        self.check(addr, 1)
        val = self.memory[addr]
        return val if not signed or val < 0x80 else val - 0x100
 
    def load_half(self, addr, signed=True):
        addr -= self.base_addr
        self.check(addr, 2)
        val = self.memory[addr] | (self.memory[addr+1] << 8)
        return val if not signed or val < 0x8000 else val - 0x10000

    def load_word(self, addr):  # always unsigned (performance)
        addr -= self.base_addr
        self.check(addr, 4)
        if addr & 0x3 == 0:
            return self.memory32[addr >> 2]  # word aligned
        else:
            return self.memory[addr] | (self.memory[addr+1] << 8) | self.memory[addr+2] << 16 | self.memory[addr+3] << 24

    def store_byte(self, addr, value):
        addr -= self.base_addr
        self.check(addr, 1)
        self.memory[addr] = value & 0xFF

    def store_half(self, addr, value):
        addr -= self.base_addr
        self.check(addr, 2)
        value &= 0xFFFF  # make it unsigned
        self.memory[addr] = value & 0xFF
        self.memory[addr+1] = (value >> 8) & 0xFF

    def store_word(self, addr, value):
        addr -= self.base_addr
        self.check(addr, 4)
        value &= 0xFFFFFFFF  # make it unsigned
        if addr & 0x3 == 0:
            self.memory32[addr >> 2] = value
        else:
            self.memory[addr] = value & 0xFF
            self.memory[addr+1] = (value >> 8) & 0xFF
            self.memory[addr+2] = (value >> 16) & 0xFF
            self.memory[addr+3] = (value >> 24) & 0xFF

    def load_binary(self, addr, n):
        addr -= self.base_addr
        self.check(addr, n)
        return self.memory[addr:addr+n]

    def store_binary(self, addr, binary):
        addr -= self.base_addr
        self.check(addr, n=len(binary))
        self.memory[addr:addr+len(binary)] = binary

    def load_cstring(self, addr, max_len=1024):
        addr -= self.base_addr
        if addr < 0 or addr >= self.size:
            raise MemoryAccessError(f"Invalid start address reading C string: 0x{addr:08X}")
        end = min(addr + max_len, self.size)
        memory_slice = self.memory[addr:end]
        nul_index = memory_slice.find(0)
        if nul_index == -1:
            raise MemoryAccessError(f"Exceeded maximum length while reading C string at 0x{addr:08X}")
        return memory_slice[:nul_index].decode('utf-8', errors='replace')

# RAM class with MMIO
class RAM_MMIO(RAM):
    def __init__(self, size=1024*1024, init=None, logger=None):
        super().__init__(size, init, logger)
        self.mmio_ranges = []

    def register_peripheral(self, peripheral):
        self.mmio_ranges.append( (peripheral.REG_BASE, peripheral.REG_END, peripheral.read32, peripheral.write32) )

    def load_byte(self, addr, signed=True):
        try:
            val = self.memory[addr]
            return val if not signed or val < 0x80 else val - 0x100
        except IndexError:
            raise MemoryAccessError(f"Access out of bounds: 0x{addr:08X} (+{1})")
 
    def load_half(self, addr, signed=True):
        try:
            val = self.memory[addr] | (self.memory[addr+1] << 8)
            return val if not signed or val < 0x8000 else val - 0x10000
        except IndexError:
            raise MemoryAccessError(f"Access out of bounds: 0x{addr:08X} (+{2})")

    def load_word(self, addr):  # always unsigned (performance)
        for (mmio_addr_base, mmio_addr_end, mmio_read32, mmio_write32) in self.mmio_ranges:
            if mmio_addr_base <= addr < mmio_addr_end:
                return mmio_read32(addr)

        try:
            if addr & 0x3 == 0:
                return self.memory32[addr >> 2]  # word aligned
            else:
                return self.memory[addr] | (self.memory[addr+1] << 8) | self.memory[addr+2] << 16 | self.memory[addr+3] << 24
        except IndexError:
            raise MemoryAccessError(f"Access out of bounds: 0x{addr:08X} (+{1})")

    def store_byte(self, addr, value):
        try:
            self.memory[addr] = value & 0xFF
        except IndexError:
            raise MemoryAccessError(f"Access out of bounds: 0x{addr:08X} (+{1})")

    def store_half(self, addr, value):
        try:
            value &= 0xFFFF  # make it unsigned
            self.memory[addr] = value & 0xFF
            self.memory[addr+1] = (value >> 8) & 0xFF
        except IndexError:
            raise MemoryAccessError(f"Access out of bounds: 0x{addr:08X} (+{2})")

    def store_word(self, addr, value):
        value &= 0xFFFFFFFF  # make it unsigned

        for (mmio_addr_base, mmio_addr_end, mmio_read32, mmio_write32) in self.mmio_ranges:
            if mmio_addr_base <= addr < mmio_addr_end:
                mmio_write32(addr, value)
                return

        try:
            if addr & 0x3 == 0:
                self.memory32[addr >> 2] = value
            else:
                self.memory[addr] = value & 0xFF
                self.memory[addr+1] = (value >> 8) & 0xFF
                self.memory[addr+2] = (value >> 16) & 0xFF
                self.memory[addr+3] = (value >> 24) & 0xFF
        except IndexError:
            raise MemoryAccessError(f"Access out of bounds: 0x{addr:08X} (+{4})")

    def load_binary(self, addr, n):
        return self.memory[addr:addr+n]

    def store_binary(self, addr, binary):
        try:
            self.memory[addr:addr+len(binary)] = binary
        except (IndexError, BufferError):
            raise MemoryAccessError(f"Access out of bounds: 0x{addr:08X}-0x{addr+len(binary)}")

    def load_cstring(self, addr, max_len=1024):
        end = min(addr + max_len, self.size)
        memory_slice = self.memory[addr:end]
        nul_index = memory_slice.find(0)
        if nul_index == -1:
            raise MemoryAccessError(f"Exceeded maximum length while reading C string at 0x{addr:08X}")
        return memory_slice[:nul_index].decode('utf-8', errors='replace')

# Safe RAM class with MMIO, all accesses are checked
class SafeRAM_MMIO(RAM):
    def __init__(self, size=1024*1024, init=None, logger=None):
        super().__init__(size, init, logger)
        self.mmio_ranges = []

    def register_peripheral(self, peripheral):
        self.mmio_ranges.append( (peripheral.REG_BASE, peripheral.REG_END, peripheral.read32, peripheral.write32) )

    def check(self, addr, n):
        if addr < 0 or addr + n > self.size:
            raise MemoryAccessError(f"Access out of bounds: 0x{addr:08X} (+{n})")

    def load_byte(self, addr, signed=True):
        self.check(addr, 1)
        val = self.memory[addr]
        return val if not signed or val < 0x80 else val - 0x100
 
    def load_half(self, addr, signed=True):
        self.check(addr, 2)
        val = self.memory[addr] | (self.memory[addr+1] << 8)
        return val if not signed or val < 0x8000 else val - 0x10000

    def load_word(self, addr):  # always unsigned (performance)
        for (mmio_addr_base, mmio_addr_end, mmio_read32, mmio_write32) in self.mmio_ranges:
            if mmio_addr_base <= addr < mmio_addr_end:
                return mmio_read32(addr)

        self.check(addr, 4)
        if addr & 0x3 == 0:
            return self.memory32[addr >> 2]  # word aligned
        else:
            return self.memory[addr] | (self.memory[addr+1] << 8) | self.memory[addr+2] << 16 | self.memory[addr+3] << 24

    def store_byte(self, addr, value):
        self.check(addr, 1)
        self.memory[addr] = value & 0xFF

    def store_half(self, addr, value):
        self.check(addr, 2)
        value &= 0xFFFF  # make it unsigned
        self.memory[addr] = value & 0xFF
        self.memory[addr+1] = (value >> 8) & 0xFF

    def store_word(self, addr, value):
        value &= 0xFFFFFFFF  # make it unsigned

        for (mmio_addr_base, mmio_addr_end, mmio_read32, mmio_write32) in self.mmio_ranges:
            if mmio_addr_base <= addr < mmio_addr_end:
                mmio_write32(addr, value)
                return

        self.check(addr, 4)
        if addr & 0x3 == 0:
            self.memory32[addr >> 2] = value
        else:
            self.memory[addr] = value & 0xFF
            self.memory[addr+1] = (value >> 8) & 0xFF
            self.memory[addr+2] = (value >> 16) & 0xFF
            self.memory[addr+3] = (value >> 24) & 0xFF

    def load_binary(self, addr, n):
        self.check(addr, n)
        return self.memory[addr:addr+n]

    def store_binary(self, addr, binary):
        self.check(addr, n=len(binary))
        self.memory[addr:addr+len(binary)] = binary

    def load_cstring(self, addr, max_len=1024):
        if addr < 0 or addr >= self.size:
            raise MemoryAccessError(f"Invalid start address reading C string: 0x{addr:08X}")
        end = min(addr + max_len, self.size)
        memory_slice = self.memory[addr:end]
        nul_index = memory_slice.find(0)
        if nul_index == -1:
            raise MemoryAccessError(f"Exceeded maximum length while reading C string at 0x{addr:08X}")
        return memory_slice[:nul_index].decode('utf-8', errors='replace')
