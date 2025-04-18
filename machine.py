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

from elftools.elf.elffile import ELFFile

class MachineError(Exception):
    pass
class ConfigError(MachineError):
    pass
class InvariantViolationError(MachineError):
    pass

class Machine:
    def __init__(self, cpu, ram, logger=None, args=None):
        self.cpu = cpu
        self.ram = ram

        self.logger = logger
        self.args = args
        self.check_start = args.check_start if args is not None else False;
        self.check_enable = False

        # text, stack and heap boundaries
        self.stack_top = None
        self.stack_bottom = None
        self.heap_end = None
        self.text_start = None
        self.text_end = None

        # text segment snapshot
        self.text_snapshot = None

        # symbol dictionary for syscall tracing
        self.symbol_dict = {}
        self.main_addr = None

    # setup argv[] strings in the heap
    def setup_argv(self, argv_list):
        argv_pointers = []
        for arg in argv_list:
            addr = self.heap_end
            self.ram.store_binary(addr, arg.encode() + b'\0')
            argv_pointers.append(addr)
            self.heap_end += len(arg) + 1
            self.heap_end = (self.heap_end + 3) & ~3  # ensure 4-byte alignment

        argv_table_addr = self.heap_end
        for ptr in argv_pointers + [0]:
            self.ram.store_word(self.heap_end, ptr)
            self.heap_end += 4

        self.heap_end = (self.heap_end + 7) & ~7  # ensure 8-byte alignment

        self.cpu.registers[10] = len(argv_list)   # a0
        self.cpu.registers[11] = argv_table_addr  # a1

    # load a flat binary executable into RAM
    def load_flatbinary(self, fname):
        with open(fname, 'rb') as f:
            binary = f.read()
            self.ram.store_binary(0, binary)
            self.cpu.pc = 0  # entry point at start of the binary
            if self.check_start == 'main':
                raise ConfigError("check_start=main is unsupported for flat binary executables")
            if self.check_start is None or self.check_start == 'default':
                self.check_start = 'first-call'

    # load an ELF executable into RAM
    def load_elf(self, fname, load_symbols=False, check_text=False):
        with open(fname, 'rb') as f:
            elf = ELFFile(f)

            # load all segments
            for segment in elf.iter_segments():
                if segment['p_type'] == 'PT_LOAD':
                    addr = segment['p_paddr']
                    data = segment.data()
                    self.ram.store_binary(addr, data)

            # set entry point
            self.cpu.pc = elf.header.e_entry

            # extract text / stack / heap boundaries
            symtab = elf.get_section_by_name(".symtab")
            if symtab:
                for sym in symtab.iter_symbols():
                    if sym.name == "__heap_start":
                        self.heap_end = sym["st_value"]
                    elif sym.name == "__stack_top":
                        self.stack_top = sym["st_value"]
                    elif sym.name == "__stack_bottom":
                        self.stack_bottom = sym["st_value"]
                    elif sym.name == "main":
                        self.main_addr = sym["st_value"]

                # load symbols for tracing
                if load_symbols:
                    for sym in symtab.iter_symbols():
                        name = sym.name
                        if not name:
                            continue
                        if sym['st_info']['type'] == 'STT_FUNC':
                            addr = sym['st_value']
                            self.symbol_dict[addr] = name

            # get boundaries of the text segment
            text_section = elf.get_section_by_name(".text")
            if text_section:
                self.text_start = text_section['sh_addr']
                self.text_end = self.text_start + text_section['sh_size']
                # if checking for text segment integrity, take a snapshot
                if check_text:
                    self.text_snapshot = self.ram.memory[self.text_start:self.text_end]

        if self.check_start is None or self.check_start == 'default':
            self.check_start = 'main'
        if self.check_start == 'main' and self.main_addr is None:
            self.logger.warning("No symbol found for main() — invariants checks disabled")
    
    # Invariant check trigger
    def trigger_check(self):
        if self.check_start == 'early':
            return True
        elif self.check_start == 'main':
            return self.cpu.pc == self.main_addr
        elif self.check_start == 'first-call':
            inst = self.ram.load_word(self.cpu.pc)
            opcode = inst & 0x7F
            return opcode in (0x6F, 0x67)
        else:
            try:
                value = int(self.check_start, 0) & 0xFFFFFFFF
                return self.cpu.pc == value
            except ValueError:
                raise ConfigError(f"Invalid --start-check value: {self.check_start}")

    # Invariants check
    def check_invariants(self):
        cpu = self.cpu

        # trigger checks
        if not self.check_enable:
            self.check_enable = self.trigger_check()
            if not self.check_enable:
                return
            else:
                self.logger.debug(f"Invariants checking started ({self.check_start})")

        # x0 = 0
        if not (cpu.registers[0] == 0):
            raise InvariantViolationError("x0 register should always be 0")

        # PC within memory bounds
        if not(0 <= cpu.pc < self.ram.size):
            raise InvariantViolationError(f"PC out of bounds: PC=0x{cpu.pc}")

        # SP below stack top
        if self.stack_top is not None and cpu.registers[3] != 0:
            if not(cpu.registers[2] <= self.stack_top):
                raise InvariantViolationError(f"SP above stack top: SP=0x{cpu.registers[2]:08x} > 0x{self.stack_top:08x}")

        # SP above stack bottom (stack overflow check)
        if self.stack_bottom is not None and cpu.registers[3] != 0:
            if not(cpu.registers[2] >= self.stack_bottom):
                raise InvariantViolationError(f"SP below stack bottom (stack overlow): SP=0x{cpu.registers[2]:08x} < 0x{self.stack_bottom:08x}")

        # Stack and heap separation
        MIN_GAP = 256
        if self.heap_end is not None and self.stack_bottom is not None:
            if not (self.heap_end + MIN_GAP <= self.stack_bottom):
                raise InvariantViolationError(f"Heap too close to stack: heap_end=0x{self.heap_end:08x}, stack_bottom=0x{self.stack_bottom:08x}")

        # SP word alignment (commented out as word-unaligned SP is actually used in the RISC-V unit tests)
        #if not(cpu.registers[2] % 4 == 0):
        #    raise InvariantViolationError(f"SP not aligned: SP=0x{cpu.registers[2]:08x}")

        # Heap end word alignment
        if self.heap_end is not None:
            if not(self.heap_end % 4 == 0):
                raise InvariantViolationError(f"Heap end not aligned: 0x{self.heap_end:08x}")
            
        # Text segment integrity check
        if self.text_snapshot is not None and \
            self.ram.memory[self.text_start:self.text_end] != self.text_snapshot:
                raise InvariantViolationError("Text segment has been modified!")

    def run_fast(self):
        cpu = self.cpu
        ram = self.ram
        running = True
        
        while running:
            inst = ram.load_word(cpu.pc)
            running = cpu.execute(inst)

    def run_with_checks(self):
        running = True
        while running:
            if self.args.regs:
                self.logger.debug(f"REGS: PC={self.cpu.pc:08x}, ra={self.cpu.registers[1]:08x}, sp={self.cpu.registers[2]:08x}, gp={self.cpu.registers[3]:08x}, a0={self.cpu.registers[10]:08x}")
            if self.args.check_inv:
                self.check_invariants()
            if self.args.trace and (self.cpu.pc in self.symbol_dict):
                self.logger.debug(f"FUNC {self.symbol_dict[self.cpu.pc]}, PC={self.cpu.pc:08x}")

            inst = self.ram.load_word(self.cpu.pc)
            running = self.cpu.execute(inst)

    def run(self):
        if not(self.args.regs or self.args.check_inv or self.args.trace):
            self.run_fast()
        else:
            self.run_with_checks()
