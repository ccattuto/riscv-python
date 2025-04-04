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

import sys
from elftools.elf.elffile import ELFFile
from riscv import CPU, execute

cpu = CPU(memory_size=1024 * 1024)

# handle different binary file formats
if sys.argv[1][-4:] == '.bin':
    # Load binary instructions into memory
    with open(sys.argv[1], 'rb') as f:
        binary = f.read()
        cpu.load_binary(binary, addr=0)
        cpu.pc = 0
        cpu.stack_top = None
        cpu.stack_bottom = None
        cpu.heap_end = None

elif sys.argv[1][-4:] == '.elf':
    # Load ELF file
    with open(sys.argv[1], 'rb') as f:
        elf = ELFFile(f)

        # load segments into memory
        for segment in elf.iter_segments():
            if segment['p_type'] == 'PT_LOAD':
                addr = segment['p_paddr']
                data = segment.data()
                cpu.load_binary(data, addr=addr)

        # load entry point
        cpu.pc = elf.header.e_entry

        # load stack top, stack bottom and heap end addresses
        cpu.heap_end = None
        cpu.stack_top = None
        cpu.stack_bottom = None
        symtab = elf.get_section_by_name(".symtab")
        if symtab:
            for sym in symtab.iter_symbols():
                if sym.name == "end":
                    cpu.heap_end = sym["st_value"]
                    cpu.text_end = sym["st_value"]
                if sym.name == "__stack_top":
                    cpu.stack_top = sym["st_value"]
                if sym.name == "__stack_bottom":
                    cpu.stack_bottom = sym["st_value"]

else:
    print("Unsupported file format. Please provide a .bin or .elf file.")
    sys.exit(-1)

def check_invariants(cpu):
    assert cpu.registers[0] == 0, "x0 register should always be 0"

    assert cpu.pc >= 0 and cpu.pc < cpu.memory_size, f"PC out of bounds: 0x{cpu.pc}"

    if cpu.stack_top is not None and cpu.registers[3] != 0:
        assert cpu.registers[2] <= cpu.stack_top, f"SP above stack top: 0x{cpu.registers[2]:08x} > 0x{cpu.stack_top:08x}"

    if cpu.stack_bottom is not None and cpu.registers[3] != 0:
        assert cpu.registers[2] >= cpu.stack_bottom, f"SP below stack bottom: 0x{cpu.registers[2]:08x} < 0x{cpu.stack_bottom:08x}"

    min_gap = 256  # bytes, arbitrary guard zone
    if cpu.heap_end is not None:
        assert cpu.heap_end + min_gap <= cpu.stack_bottom, f"Heap too close to stack: heap_end=0x{cpu.heap_end:08x}, stack_bottom=0x{cpu.stack_bottom:08x}"

    assert cpu.registers[2] % 4 == 0, f"SP not aligned: 0x{cpu.registers[2]:08x}"

    if cpu.heap_end is not None:
        assert cpu.heap_end % 4 == 0, f"Heap end not aligned: 0x{cpu.heap_end:08x}"


# Execution loop
while True:
    #print(f"PC={cpu.pc:08x}, ra={cpu.registers[1]:08x}, sp={cpu.registers[2]:08x}, gp={cpu.registers[3]:08x}")
    #check_invariants(cpu)
    inst = cpu.load_word(cpu.pc)
    continue_exec = execute(cpu, inst)
    if not continue_exec:
        break
