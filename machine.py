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

class MachineError(Exception):
    pass
class InvalidSyscallError(MachineError):
    pass
class InvariantViolationError(MachineError):
    pass

class Machine:
    def __init__(self, cpu, ram, logger=None, raw_tty=False, trace_syscalls=False):
        self.cpu = cpu
        self.ram = ram

        self.logger = logger
        self.raw_tty = raw_tty
        self.trace_syscalls = trace_syscalls

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


    # Syscall handling
    def handle_ecall(self):
        cpu = self.cpu
        syscall_id = cpu.registers[17]  # a7

        # _write syscall (Newlib standard)
        if syscall_id == 64:
            fd = cpu.registers[10]      # a0
            addr = cpu.registers[11]    # a1
            count = cpu.registers[12]   # a2
            if self.logger is not None and self.trace_syscalls:
                self.logger.debug(f"SYSCALL _write: fd={fd}, addr={addr:08x}, count={count}")
            data = self.ram.load_binary(addr, count)
            if fd == 1 or fd == 2:  # stdout or stderr
                if not self.raw_tty:
                    print(data.decode(), end='')
                else:
                    sys.stdout.buffer.write(data)
                    sys.stdout.flush()
            cpu.registers[10] = count  # return count as written
            return True
        
        # _read systcall (Newlib standard)
        elif syscall_id == 63:
            fd = cpu.registers[10]      # a0
            addr = cpu.registers[11]    # a1
            count = cpu.registers[12]   # a2
            if self.logger is not None and self.trace_syscalls:
                self.logger.debug(f"SYSCALL _read: fd={fd}, addr=0x{addr:08x}, count={count}")
            if fd == 0:  # stdin
                if not self.raw_tty:
                    try:  # normal (cooked) terminal mode
                        # Blocking read from stdin
                        input_text = input() + "\n"  # Simulate ENTER key
                        data = input_text.encode()[:count]
                    except EOFError:
                        data = b''
                    self.ram.store_binary(addr, data)
                    cpu.registers[10] = len(data)
                else:  # raw terminal mode
                    ch = sys.stdin.read(1)  # blocks for a single char
                    if ch == '\x03':  # CTRL+C
                        raise KeyboardInterrupt
                    self.ram.store_byte(addr, ord(ch))
                    cpu.registers[10] = 1
            else:
                raise InvalidSyscallError(f"SYSCALL _read: unsupported fd={fd}")
            return True
        
        # _sbrk syscall (Newlib standard)
        elif syscall_id == 214:
            if self.stack_bottom is None:
                raise InvalidSyscallError("SYSCALL _sbrk: stack bottom not set")

            increment = cpu.registers[10]
            old_heap_end = self.heap_end
            new_heap_end = old_heap_end + increment

            if new_heap_end >= self.stack_bottom:
                cpu.registers[10] = 0xFFFFFFFF  # -1 = failure
            else:
                self.heap_end = new_heap_end
                cpu.registers[10] = old_heap_end  # return old break
            if self.logger is not None and self.trace_syscalls:
                self.logger.debug(f"SYSCALL _sbrk: increment={increment}, old_heap_end={old_heap_end:08x}, new_heap_end={new_heap_end:08x}")
            return True
        
        # _exit systcall (Newlib standard)
        elif syscall_id == 93:  # _exit syscall
            exit_code = cpu.registers[10]  # a0
            if exit_code >= 0x80000000:
                exit_code - 0x100000000
            if self.logger is not None:
                self.logger.debug(f"SYSCALL _exit: exit code={exit_code}")
            return False
        
        # unhandled syscall
        else:
            raise InvalidSyscallError(f"SYSCALL UNKNOWN: {syscall_id})]")
        

    # Invariants check
    def check_invariants(self):
        cpu = self.cpu

        # x0
        if not (cpu.registers[0] == 0):
            raise InvariantViolationError("x0 register should always be 0")

        # PC within memory bounds
        if not(0 <= cpu.pc < self.ram.size):
            raise InvariantViolationError(f"PC out of bounds: PC=0x{cpu.pc}")

        # SP below stack top
        if self.stack_top is not None and cpu.registers[3] != 0:
            if not(cpu.registers[2] <= self.stack_top):
                raise InvariantViolationError(f"SP above stack top: SP=0x{cpu.registers[2]:08x} > 0x{self.stack_top:08x}")

        # SP above stack bottom
        if self.stack_bottom is not None and cpu.registers[3] != 0:
            if not(cpu.registers[2] >= self.stack_bottom):
                raise InvariantViolationError(f"SP below stack bottom: SP=0x{cpu.registers[2]:08x} < 0x{self.stack_bottom:08x}")

        # Stack and heap separation
        min_gap = 256
        if self.heap_end is not None and self.stack_bottom is not None:
            if not (self.heap_end + min_gap <= self.stack_bottom):
                raise InvariantViolationError(f"Heap too close to stack: heap_end=0x{self.heap_end:08x}, stack_bottom=0x{self.stack_bottom:08x}")

        # SP alignment
        if not(cpu.registers[2] % 4 == 0):
            raise InvariantViolationError(f"SP not aligned: SP=0x{cpu.registers[2]:08x}")

        # Heap end alignment
        if self.heap_end is not None:
            if not(self.heap_end % 4 == 0):
                raise InvariantViolationError(f"Heap end not aligned: 0x{self.heap_end:08x}")
            
        # Text segment integrity check
        if self.text_snapshot is not None and \
            self.ram.memory[self.text_start:self.text_end] != self.text_snapshot:
                raise InvariantViolationError("Text segment has been modified!")

