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

def signed(val):
    return val if val < 0x80000000 else val - 0x100000000

def sign_extend(value, bits):
    sign_bit = 1 << (bits - 1)
    return (value & (sign_bit - 1)) - (value & sign_bit)

def decode(inst):
    opcode = inst & 0x7F
    rd = (inst >> 7) & 0x1F
    funct3 = (inst >> 12) & 0x7
    rs1 = (inst >> 15) & 0x1F
    rs2 = (inst >> 20) & 0x1F
    funct7 = (inst >> 25) & 0x7F

    # Immediate formats:
    imm_i = sign_extend(inst >> 20, 12)
    imm_s = sign_extend(((inst >> 7) & 0x1F) | ((inst >> 25) << 5), 12)
    imm_b = sign_extend((((inst >> 7) & 0x1) << 11) |
                        (((inst >> 8) & 0xF) << 1) |
                        (((inst >> 25) & 0x3F) << 5) |
                        ((inst >> 31) << 12), 13)
    imm_u = inst >> 12
    imm_j = sign_extend((((inst >> 21) & 0x3FF) << 1) |
                        (((inst >> 20) & 0x1) << 11) |
                        (((inst >> 12) & 0xFF) << 12) |
                        ((inst >> 31) << 20), 21)

    return opcode, rd, funct3, rs1, rs2, funct7, imm_i, imm_s, imm_b, imm_u, imm_j


def execute(cpu, inst):
    opcode, rd, funct3, rs1, rs2, funct7, imm_i, imm_s, imm_b, imm_u, imm_j = decode(inst)

    next_pc = (cpu.pc + 4) & 0xFFFFFFFF

    if opcode == 0x33:  # R-type
        if funct3 == 0x0:  # ADD/SUB
            if funct7 == 0x00:  # ADD
                cpu.registers[rd] = (cpu.registers[rs1] + cpu.registers[rs2]) & 0xFFFFFFFF
            elif funct7 == 0x20:  # SUB
                cpu.registers[rd] = (cpu.registers[rs1] - cpu.registers[rs2]) & 0xFFFFFFFF
            else:
                raise ValueError(f"Invalid funct7=0x{funct7:02x} for ADD/SUB at PC=0x{cpu.pc:08x}")
        elif funct3 == 0x1:  # SLL
            cpu.registers[rd] = (cpu.registers[rs1] << (cpu.registers[rs2] & 0x1F)) & 0xFFFFFFFF
        elif funct3 == 0x2:  # SLT
            cpu.registers[rd] = int(signed(cpu.registers[rs1]) < signed(cpu.registers[rs2]))
        elif funct3 == 0x3:  # SLTU
            cpu.registers[rd] = int((cpu.registers[rs1] & 0xFFFFFFFF) < (cpu.registers[rs2] & 0xFFFFFFFF))
        elif funct3 == 0x4:  # XOR
            cpu.registers[rd] = cpu.registers[rs1] ^ cpu.registers[rs2]
        elif funct3 == 0x5:  # SRL/SRA
            shamt = cpu.registers[rs2] & 0x1F
            if funct7 == 0x00:  # SRL
                cpu.registers[rd] = (cpu.registers[rs1] & 0xFFFFFFFF) >> shamt
            elif funct7 == 0x20:  # SRA
                cpu.registers[rd] = (signed(cpu.registers[rs1]) >> shamt) & 0xFFFFFFFF
            else:
                raise ValueError(f"Invalid funct7=0x{funct7:02x} for SRL/SRA at PC=0x{cpu.pc:08x}")
        elif funct3 == 0x6:  # OR
            cpu.registers[rd] = cpu.registers[rs1] | cpu.registers[rs2]
        elif funct3 == 0x7:  # AND
            cpu.registers[rd] = cpu.registers[rs1] & cpu.registers[rs2]

    elif opcode == 0x13:  # I-type arithmetic
        if funct3 == 0x0:  # ADDI
            cpu.registers[rd] = (cpu.registers[rs1] + imm_i) & 0xFFFFFFFF
        elif funct3 == 0x1:  # SLLI
            cpu.registers[rd] = (cpu.registers[rs1] << (imm_i & 0x1F)) & 0xFFFFFFFF
        elif funct3 == 0x2:  # SLTI
            cpu.registers[rd] = int(signed(cpu.registers[rs1]) < signed(imm_i))
        elif funct3 == 0x3:  # SLTIU
            cpu.registers[rd] = int((cpu.registers[rs1] & 0xFFFFFFFF) < (imm_i & 0xFFFFFFFF))
        elif funct3 == 0x4:  # XORI
            cpu.registers[rd] = (cpu.registers[rs1] ^ imm_i) & 0xFFFFFFFF
        elif funct3 == 0x5:  # SRLI/SRAI
            shamt = imm_i & 0x1F
            if funct7 == 0x00:  # SRLI
                cpu.registers[rd] = (cpu.registers[rs1] & 0xFFFFFFFF) >> shamt
            elif funct7 == 0x20:  # SRAI
                cpu.registers[rd] = (signed(cpu.registers[rs1]) >> shamt) & 0xFFFFFFFF
            else:
                raise ValueError(f"Invalid funct7=0x{funct7:02x} for SRLI/SRAI at PC=0x{cpu.pc:08x}")
        elif funct3 == 0x6: # ORI
            cpu.registers[rd] = (cpu.registers[rs1] | imm_i) & 0xFFFFFFFF
        elif funct3 == 0x7: # ANDI
            cpu.registers[rd] = (cpu.registers[rs1] & imm_i) & 0xFFFFFFFF

    elif opcode == 0x03:  # Loads
        addr = (cpu.registers[rs1] + imm_i) & 0xFFFFFFFF
        if funct3 == 0x0:  # LB
            cpu.registers[rd] = cpu.load_byte(addr) & 0xFFFFFFFF
        elif funct3 == 0x1:  # LH
            cpu.registers[rd] = cpu.load_half(addr) & 0xFFFFFFFF
        elif funct3 == 0x2:  # LW
            cpu.registers[rd] = cpu.load_word(addr) & 0xFFFFFFFF
        elif funct3 == 0x4:  # LBU
            cpu.registers[rd] = cpu.load_byte(addr, signed=False) & 0xFF
        elif funct3 == 0x5:  # LHU
            cpu.registers[rd] = cpu.load_half(addr, signed=False) & 0xFFFF
        else:
            raise ValueError(f"Invalid funct3=0x{funct3:02x} for LOAD at PC=0x{cpu.pc:08x}")

    elif opcode == 0x23:  # Stores
        addr = (cpu.registers[rs1] + imm_s) & 0xFFFFFFFF
        if funct3 == 0x0:  # SB
            cpu.store_byte(addr, cpu.registers[rs2] & 0xFF)
        elif funct3 == 0x1:  # SH
            cpu.store_half(addr, cpu.registers[rs2] & 0xFFFF)
        elif funct3 == 0x2:  # SW
            cpu.store_word(addr, cpu.registers[rs2])
        else:
            raise ValueError(f"Invalid funct3=0x{funct3:02x} for STORE at PC=0x{cpu.pc:08x}")

    elif opcode == 0x63:  # Branches
        if (
            (funct3 == 0x0 and cpu.registers[rs1] == cpu.registers[rs2]) or  # BEQ
            (funct3 == 0x1 and cpu.registers[rs1] != cpu.registers[rs2]) or  # BNE
            (funct3 == 0x4 and sign_extend(cpu.registers[rs1],32) < sign_extend(cpu.registers[rs2],32)) or  # BLT
            (funct3 == 0x5 and sign_extend(cpu.registers[rs1],32) >= sign_extend(cpu.registers[rs2],32)) or  # BGE
            (funct3 == 0x6 and (cpu.registers[rs1] & 0xFFFFFFFF) < (cpu.registers[rs2] & 0xFFFFFFFF)) or  # BLTU
            (funct3 == 0x7 and (cpu.registers[rs1] & 0xFFFFFFFF) >= (cpu.registers[rs2] & 0xFFFFFFFF))  # BGEU
            ): 
            next_pc = (cpu.pc + imm_b) & 0xFFFFFFFF
        elif funct3 == 0x2 or funct3 == 0x3:
            raise Exception(f"Illegal branch funct3=0x{funct3:X}")

    elif opcode == 0x37:  # LUI
        cpu.registers[rd] = (imm_u << 12) & 0xFFFFFFFF

    elif opcode == 0x17:  # AUIPC
        cpu.registers[rd] = (cpu.pc + (imm_u << 12)) & 0xFFFFFFFF

    elif opcode == 0x6F:  # JAL
        if rd != 0:
            cpu.registers[rd] = next_pc
        next_pc = (cpu.pc + imm_j) & 0xFFFFFFFF
        #print(f"[JAL] pc=0x{cpu.pc:08x}, rd={rd}, target=0x{next_pc:08x}, return_addr=0x{(cpu.pc + 4) & 0xFFFFFFFF:08x}")

    elif opcode == 0x67:  # JALR
        addr_target = (cpu.registers[rs1] + imm_i) & 0xFFFFFFFF
        if rd != 0:
            cpu.registers[rd] = (cpu.pc + 4) & 0xFFFFFFFF
        next_pc = addr_target
        #print(f"[JALR] jumping to 0x{next_pc:08x} from rs1=0x{cpu.registers[rs1]:08x}, imm={imm_i}")

    elif opcode == 0x73:  # SYSTEM (ECALL/EBREAK)
        #print(f"[SYSTEM] opcode=0x{opcode:x}, imm_i={imm_i}")
        if imm_i == 0: # ECALL
            ecall_ret = ecall(cpu)
            if not ecall_ret:
                cpu.pc = next_pc
                return False
        elif imm_i == 1:  # EBREAK
            print("[EBREAK]")
            # we just print register values and stop execution
            cpu.print_registers()
            cpu.pc = next_pc
            return False
        else:
            print(f"[UNHANDLED SYSTEM INSTRUCTION] imm_i={imm_i}")
            cpu.pc = next_pc
            return False
    else:
        print(f"[UNHANDLED INSTRUCTION] opcode=0x{opcode:x}, funct3=0x{funct3:x}, funct7=0x{funct7:x}, imm_i={imm_i}, imm_s={imm_s}, imm_b={imm_b}, imm_u={imm_u}, imm_j={imm_j}")
        cpu.pc = next_pc
        return False
    
    cpu.registers[0] = 0    # x0 is always 0
    cpu.pc = next_pc        # update PC
    return True


def ecall(cpu):
    syscall_id = cpu.registers[17]  # a7
    #print(f"[SYSCALL {syscall_id}]")

    # _write syscall (newlib standard)
    if syscall_id == 64:
        fd = cpu.registers[10]      # a0
        addr = cpu.registers[11]    # a1
        count = cpu.registers[12]   # a2
        #print(f"[ECALL (write) fd={fd}, addr={addr:08x}, count={count}]")
        data = cpu.memory[addr:addr+count]
        if fd == 1 or fd == 2:  # stdout or stderr
            print(data.decode(), end='')
        cpu.registers[10] = count  # return count as written
        return True
    
    # _read systcall (newlib standard)
    elif syscall_id == 63:
        fd = cpu.registers[10]      # a0
        addr = cpu.registers[11]    # a1
        count = cpu.registers[12]   # a2
        #print(f"[ECALL (read) fd={fd}, addr=0x{addr:08x}, count={count}]")
        if fd == 0:  # stdin
            try:
                # Blocking read from stdin
                input_text = input() + "\n"  # Simulate ENTER key
                data = input_text.encode()[:count]
            except EOFError:
                data = b''
            for i, byte in enumerate(data):
                cpu.memory[addr + i] = byte
            cpu.registers[10] = len(data)
        else:
            print(f"[ECALL read] Unsupported fd={fd}")
            cpu.registers[10] = -1  # error
            return False
        return True
    
    # _sbrk syscall (newlib standard)
    elif syscall_id == 214:
        assert(cpu.stack_bottom is not None)

        increment = cpu.registers[10]
        old_heap_end = cpu.heap_end
        new_heap_end = old_heap_end + increment

        if new_heap_end >= cpu.stack_bottom:
            cpu.registers[10] = 0xFFFFFFFF  # -1 = failure
        else:
            cpu.heap_end = new_heap_end
            cpu.registers[10] = old_heap_end  # return old break
        #print(f"[ECALL (sbrk)]: increment={increment}, old_heap_end=0x{old_heap_end:08x}, new_heap_end=0x{new_heap_end:08x}")
        return True
    
    # exit systcall (newlib standard)
    elif syscall_id == 93:  # _exit syscall
        exit_code = sign_extend(cpu.registers[10], 32)  # a0
        print(f"[ECALL (exit)]: exit code {exit_code}")
        return False
    
    # unhandled syscall
    else:
        print(f"[ECALL (UNKNOWN {syscall_id})]")
        return False
    

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


class CPU:
    def __init__(self, memory_size=1024 * 1024):
        self.registers = [0] * 32
        self.pc = 0
        self.memory = bytearray(memory_size)
        self.memory_size = memory_size

        self.stack_top = None
        self.stack_bottom = None
        self.heap_end = None
        self.text_start = None
        self.text_end = None
        self.text_snapshot = None
        self.symbol_dict = {}
        
    def execute(self, inst):
        return execute(self, inst)
    
    def load_byte(self, addr, signed=True):
        return int.from_bytes(self.memory[addr:addr+1], 'little', signed=signed)

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

    def load_binary(self, binary, addr=0):
        self.memory[addr:addr+len(binary)] = binary

    def load_flatbinary(self, fname):
        with open(fname, 'rb') as f:
            binary = f.read()
            self.load_binary(binary, addr=0)
            self.pc = 0 # entry point at start of the binary

    def load_elf(self, fname, load_symbols=False, text_snapshot=False):
        with open(fname, 'rb') as f:
            elf = ELFFile(f)

            # load all segments
            for segment in elf.iter_segments():
                if segment['p_type'] == 'PT_LOAD':
                    addr = segment['p_paddr']
                    data = segment.data()
                    self.load_binary(data, addr=addr)

            # set entry point
            self.pc = elf.header.e_entry

            # extract text / stack / heap boundaries
            symtab = elf.get_section_by_name(".symtab")
            if symtab:
                for sym in symtab.iter_symbols():
                    if sym.name == "end":
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
                if text_snapshot:
                    self.text_snapshot = self.memory[self.text_start:self.text_end]

    def check_invariants(self):
        check_invariants(self)

    def print_registers(self):
        reg_names = [
            'zero', 'ra', 'sp', 'gp', 'tp',
            't0', 't1', 't2', 's0/fp', 's1',
            'a0', 'a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7',
            's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9', 's10', 's11',
            't3', 't4', 't5', 't6'
        ]

        print("Register State:")
        for i, name in enumerate(reg_names):
            value = self.registers[i]
            print(f"{name:<6} (x{i:02}): 0x{value:08x} ({value})")

