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

# We provide a base implementation of the RAM class, with minimal features,
# and then a set of mixins that are combined to create RAM classes with different features.

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
    def __init__(self, size=1024*1024, init=None, logger=None):
        self.memory = bytearray(size)
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

# Safe mixin: checks all memory accesses
class _SafeMixin:
    def check(self, addr, n):
        if not (0 <= addr < self.size and addr + n <= self.size):
            raise MemoryAccessError(f"Access out of bounds: 0x{addr:08X} (+{n})")

    def load_byte(self, addr, signed=True):
        self.check(addr, 1); return super().load_byte(addr, signed)

    def store_byte(self, addr, value):
        self.check(addr, 1); super().store_byte(addr, value)

    def load_half(self, addr, signed=True):
        self.check(addr, 2); return super().load_half(addr, signed)

    def store_half(self, addr, value):
        self.check(addr, 2); super().store_half(addr, value)

    def load_word(self, addr):
        self.check(addr, 4); return super().load_word(addr)

    def store_word(self, addr, value):
        self.check(addr, 4); super().store_word(addr, value)

    def load_binary(self, addr, n):
        self.check(addr, n); return super().load_binary(addr, n)

    def store_binary(self, addr, data):
        self.check(addr, len(data)); super().store_binary(addr, data)

    def load_cstring(self, addr, max_len=1024):
        if not (0 <= addr < self.size):
            raise MemoryAccessError(f"Invalid C-string start: 0x{addr:08X}")
        return super().load_cstring(addr, max_len)

# Offset mixin: non-zero RAM base address (e.g., necessary for unit tests)
class _OffsetMixin:
    def __init__(self, size, base_addr=0, init=None, logger=None):
        super().__init__(size, init, logger)
        self.base_addr = base_addr

    def _adj(self, addr):
        return addr - self.base_addr

    def load_byte(self, addr, signed=True):
        return super().load_byte(self._adj(addr), signed)

    def store_byte(self, addr, value):
        super().store_byte(self._adj(addr), value)

    def load_half(self, addr, signed=True):
        return super().load_half(self._adj(addr), signed)

    def store_half(self, addr, value):
        super().store_half(self._adj(addr), value)

    def load_word(self, addr):
        return super().load_word(self._adj(addr))

    def store_word(self, addr, value):
        super().store_word(self._adj(addr), value)

    def load_binary(self, addr, n):
        return super().load_binary(self._adj(addr), n)

    def store_binary(self, addr, data):
        super().store_binary(self._adj(addr), data)

    def load_cstring(self, addr, max_len=1024):
        return super().load_cstring(self._adj(addr), max_len)

# MMIO mixin: support for memory-mapped I/O
class _MMIOMixin:
    def __init__(self, size, init=None, logger=None):
        super().__init__(size, init, logger)
        self.mmio_ranges = []

    def register_peripheral(self, p):
        self.mmio_ranges.append((p.REG_BASE, p.REG_END, p.read32, p.write32))

    def load_word(self, addr):
        for lo, hi, read32, _ in self.mmio_ranges:
            if lo <= addr < hi:
                return read32(addr)
        return super().load_word(addr)

    def store_word(self, addr, value):
        for lo, hi, _, write32 in self.mmio_ranges:
            if lo <= addr < hi:
                return write32(addr, value)
        return super().store_word(addr, value)


# Combine mixins to create RAM classes with different features
# (Offset, Safe, MMIO)

_feature_sets = [
    (True,  False, False),  # Offset_RAM
    (False, True,  False),  # Safe_RAM
    (True,  True,  False),  # Offset_Safe_RAM
    (False, False, True),   # MMIO_RAM
    (True,  False, True),   # Offset_MMIO_RAM
    (False,  True, True),   # Safe_MMIO_RAM
    (True,  True,  True)    # Offset_Safe_MMIO_RAM
]

# Create all classes specified by the feature sets
for safe, offset, mmio in _feature_sets:
    name_parts = []
    parts = []
    if offset:
        name_parts.append("Offset"); parts.append(_OffsetMixin)
    if safe:
        name_parts.append("Safe");   parts.append(_SafeMixin)
    if mmio:
        name_parts.append("MMIO");   parts.append(_MMIOMixin)
    name_parts.append("RAM")

    class_name = "_".join(name_parts)
    parts.append(RAM)

    globals()[class_name] = type(class_name, tuple(parts), {})
