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

import sys, argparse
from elftools.elf.elffile import ELFFile
from riscv import CPU, execute

MEMORY_SIZE = 1024 * 1024 # 1MB

def parse_args():
    parser = argparse.ArgumentParser(description="RISC-V Emulator")
    parser.add_argument("input", help="Input .elf or .bin file")
    parser.add_argument("--trace", action="store_true", help="Enable symbol-based call tracing")
    parser.add_argument("--regs", action="store_true", help="Print registers at each instruction")
    parser.add_argument("--check", action="store_true", help="Check invariants on each step")
    parser.add_argument("--check-text", action="store_true", help="Ensure text segment is not modified")
    return parser.parse_args()

def check_invariants(cpu):
    # x0
    assert cpu.registers[0] == 0, "x0 register should always be 0"

    # PC within memory bounds
    assert 0 <= cpu.pc < cpu.memory_size, f"PC out of bounds: 0x{cpu.pc}"

    # SP below stack top
    if cpu.stack_top is not None and cpu.registers[3] != 0:
        assert cpu.registers[2] <= cpu.stack_top, f"SP above stack top: 0x{cpu.registers[2]:08x} > 0x{cpu.stack_top:08x}"

    # SP above stack bottom
    if cpu.stack_bottom is not None and cpu.registers[3] != 0:
        assert cpu.registers[2] >= cpu.stack_bottom, f"SP below stack bottom: 0x{cpu.registers[2]:08x} < 0x{cpu.stack_bottom:08x}"

    # Stack and heap separation
    min_gap = 256
    if cpu.heap_end is not None and cpu.stack_bottom is not None:
        assert cpu.heap_end + min_gap <= cpu.stack_bottom, f"Heap too close to stack: heap_end=0x{cpu.heap_end:08x}, stack_bottom=0x{cpu.stack_bottom:08x}"

    # SP alignment
    assert cpu.registers[2] % 4 == 0, f"SP not aligned: 0x{cpu.registers[2]:08x}"

    # Heap end alignment
    if cpu.heap_end is not None:
        assert cpu.heap_end % 4 == 0, f"Heap end not aligned: 0x{cpu.heap_end:08x}"


if __name__ == '__main__':
    args = parse_args()
    
    # Instantiate CPU + RAM
    cpu = CPU(memory_size=MEMORY_SIZE)

    cpu.heap_end = None
    cpu.stack_top = None
    cpu.stack_bottom = None
    cpu.text_start = None
    cpu.text_end = None
    cpu.text_snapshot = None
    symbol_dict = None

    # Load binary or ELF file
    if args.input.endswith('.bin'):
        # load binary file
        with open(args.input, 'rb') as f:
            binary = f.read()
            cpu.load_binary(binary, addr=0)
            cpu.pc = 0 # entry point at start of the binary

    elif args.input.endswith('.elf'):
        # load ELF file
        with open(args.input, 'rb') as f:
            elf = ELFFile(f)

            # load all segments
            for segment in elf.iter_segments():
                if segment['p_type'] == 'PT_LOAD':
                    addr = segment['p_paddr']
                    data = segment.data()
                    cpu.load_binary(data, addr=addr)

            # set entry point
            cpu.pc = elf.header.e_entry

            # extract text / stack / heap boundaries
            symtab = elf.get_section_by_name(".symtab")
            if symtab:
                for sym in symtab.iter_symbols():
                    if sym.name == "end":
                        cpu.heap_end = sym["st_value"]
                    elif sym.name == "__stack_top":
                        cpu.stack_top = sym["st_value"]
                    elif sym.name == "__stack_bottom":
                        cpu.stack_bottom = sym["st_value"]

                # load symbols for tracing
                if args.trace:
                    symbol_dict = {}
                    for sym in symtab.iter_symbols():
                        name = sym.name
                        if not name:
                            continue
                        if sym['st_info']['type'] == 'STT_FUNC':
                            addr = sym['st_value']
                            symbol_dict[addr] = name

            # get boundaries of the text segment
            text_section = elf.get_section_by_name(".text")
            if text_section:
                cpu.text_start = text_section['sh_addr']
                cpu.text_end = cpu.text_start + text_section['sh_size']
                # if checking for text segment integrity, take a snapshot
                if args.check_text:
                    cpu.text_snapshot = cpu.memory[cpu.text_start:cpu.text_end]

    else:
        print("Unsupported file format. Please provide a .bin or .elf file.")
        sys.exit(-1)

    # Execution loop
    try:
        while True:
            if args.regs:
                print(f"PC={cpu.pc:08x}, ra={cpu.registers[1]:08x}, sp={cpu.registers[2]:08x}, gp={cpu.registers[3]:08x}, a0={cpu.registers[10]:08x}")
            if args.check:
                check_invariants(cpu)
            if args.check_text and hasattr(cpu, 'text_snapshot'):
                assert cpu.memory[cpu.text_start:cpu.text_end] == cpu.text_snapshot, "Text segment has been modified!"
            if args.trace and symbol_dict and cpu.pc in symbol_dict:
                print(f"PC={cpu.pc:08x}, {symbol_dict[cpu.pc]}")

            inst = cpu.load_word(cpu.pc)
            continue_exec = execute(cpu, inst)
            if not continue_exec:
                break

    except KeyboardInterrupt:
        print("\nExecution interrupted by user.")
