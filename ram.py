#!/usr/bin/env python3

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

from machine import MachineError

class MemoryAccessError(MachineError):
    pass

# "Fast" RAM class: no address checks
class RAM:
    def __init__(self, size, logger=None):
        self.memory = bytearray(size)
        self.size = size
        self.logger = logger

    def load_byte(self, addr, signed=True):
        val = self.memory[addr]
        return val if not signed or val < 0x80 else val - 0x100
    
    def load_half(self, addr, signed=True):
        return int.from_bytes(self.memory[addr:addr+2], 'little', signed=signed)

    def load_word(self, addr, signed=True):
        return int.from_bytes(self.memory[addr:addr+4], 'little', signed=signed)

    def store_byte(self, addr, value):
        self.memory[addr] = value & 0xFF

    def store_half(self, addr, value):
        self.memory[addr:addr+2] = (value & 0xFFFF).to_bytes(2, 'little')

    def store_word(self, addr, value):
        self.memory[addr:addr+4] = (value & 0xFFFFFFFF).to_bytes(4, 'little')

    def load_binary(self, addr, n):
        return self.memory[addr:addr+n]

    def store_binary(self, addr, binary):
        self.memory[addr:addr+len(binary)] = binary

    def load_cstring(self, addr, max_len=1024):
        end = min(addr + max_len, self.size)
        memory_slice = self.memory[addr:end]
        nul_index = memory_slice.find(0)
        if nul_index == -1:
            raise MemoryAccessError(f"Exceeded maximum length while reading C string: 0x{addr:08x}")
        return memory_slice[:nul_index].decode('utf-8', errors='replace')

# Safe RAM class: checks all addresses
class SafeRAM:
    def __init__(self, size, logger=None):
        self.memory = bytearray(size)
        self.size = size
        self.logger = logger

    def check(self, addr, n):
        if addr < 0 or addr + n > self.size:
            raise MemoryAccessError(f"Access out of bounds: 0x{addr:08x} (+{n})")

    def load_byte(self, addr, signed=True):
        self.check(addr, 1)
        val = self.memory[addr]
        return val if not signed or val < 0x80 else val - 0x100
 
    def load_half(self, addr, signed=True):
        self.check(addr, 2)
        return int.from_bytes(self.memory[addr:addr+2], 'little', signed=signed)

    def load_word(self, addr, signed=True):
        self.check(addr, 4)
        return int.from_bytes(self.memory[addr:addr+4], 'little', signed=signed)

    def store_byte(self, addr, value):
        self.check(addr, 1)
        self.memory[addr] = value & 0xFF

    def store_half(self, addr, value):
        self.check(addr, 2)
        self.memory[addr:addr+2] = (value & 0xFFFF).to_bytes(2, 'little')

    def store_word(self, addr, value):
        self.check(addr, 4)
        self.memory[addr:addr+4] = (value & 0xFFFFFFFF).to_bytes(4, 'little')

    def load_binary(self, addr, n):
        self.check(addr, n)
        return self.memory[addr:addr+n]

    def store_binary(self, addr, binary):
        self.check(addr, n=len(binary))
        self.memory[addr:addr+len(binary)] = binary

    def load_cstring(self, addr, max_len=1024):
        if addr < 0 or addr >= self.size:
            raise MemoryAccessError(f"Invalid start address reading C string: 0x{addr:08x}")
        end = min(addr + max_len, self.size)
        memory_slice = self.memory[addr:end]
        nul_index = memory_slice.find(0)
        if nul_index == -1:
            raise MemoryAccessError(f"Exceeded maximum length while reading C string: 0x{addr:08x}")
        return memory_slice[:nul_index].decode('utf-8', errors='replace')
