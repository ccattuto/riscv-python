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

# CPU exceptions
class InvalidInstructionError(MachineError):
    pass

# Helper functions

def signed(val):
    return val if val < 0x80000000 else val - 0x100000000

def sign_extend(value, bits):
    sign_bit = 1 << (bits - 1)
    return (value & (sign_bit - 1)) - (value & sign_bit)

# Instruction decoding
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


# Instruction execution
def execute(cpu, ram, inst):
    opcode, rd, funct3, rs1, rs2, funct7, imm_i, imm_s, imm_b, imm_u, imm_j = decode(inst)

    next_pc = (cpu.pc + 4) & 0xFFFFFFFF

    if opcode == 0x33:  # R-type
        if funct3 == 0x0:  # ADD/SUB
            if funct7 == 0x00:  # ADD
                cpu.registers[rd] = (cpu.registers[rs1] + cpu.registers[rs2]) & 0xFFFFFFFF
            elif funct7 == 0x20:  # SUB
                cpu.registers[rd] = (cpu.registers[rs1] - cpu.registers[rs2]) & 0xFFFFFFFF
            else:
                raise InvalidInstructionError(f"Invalid funct7=0x{funct7:02x} for ADD/SUB at PC=0x{cpu.pc:08x}")
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
                raise InvalidInstructionError(f"Invalid funct7=0x{funct7:02x} for SRL/SRA at PC=0x{cpu.pc:08x}")
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
                raise InvalidInstructionError(f"Invalid funct7=0x{funct7:02x} for SRLI/SRAI at PC=0x{cpu.pc:08x}")
        elif funct3 == 0x6: # ORI
            cpu.registers[rd] = (cpu.registers[rs1] | imm_i) & 0xFFFFFFFF
        elif funct3 == 0x7: # ANDI
            cpu.registers[rd] = (cpu.registers[rs1] & imm_i) & 0xFFFFFFFF

    elif opcode == 0x03:  # Loads
        addr = (cpu.registers[rs1] + imm_i) & 0xFFFFFFFF
        if funct3 == 0x0:  # LB
            cpu.registers[rd] = ram.load_byte(addr) & 0xFFFFFFFF
        elif funct3 == 0x1:  # LH
            cpu.registers[rd] = ram.load_half(addr) & 0xFFFFFFFF
        elif funct3 == 0x2:  # LW
            cpu.registers[rd] = ram.load_word(addr) & 0xFFFFFFFF
        elif funct3 == 0x4:  # LBU
            cpu.registers[rd] = ram.load_byte(addr, signed=False) & 0xFF
        elif funct3 == 0x5:  # LHU
            cpu.registers[rd] = ram.load_half(addr, signed=False) & 0xFFFF
        else:
            raise InvalidInstructionError(f"Invalid funct3=0x{funct3:02x} for LOAD at PC=0x{cpu.pc:08x}")

    elif opcode == 0x23:  # Stores
        addr = (cpu.registers[rs1] + imm_s) & 0xFFFFFFFF
        if funct3 == 0x0:  # SB
            ram.store_byte(addr, cpu.registers[rs2] & 0xFF)
        elif funct3 == 0x1:  # SH
            ram.store_half(addr, cpu.registers[rs2] & 0xFFFF)
        elif funct3 == 0x2:  # SW
            ram.store_word(addr, cpu.registers[rs2])
        else:
            raise InvalidInstructionError(f"Invalid funct3=0x{funct3:02x} for STORE at PC=0x{cpu.pc:08x}")

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
            raise InvalidInstructionError(f"Illegal branch funct3=0x{funct3:X}")

    elif opcode == 0x37:  # LUI
        cpu.registers[rd] = (imm_u << 12) & 0xFFFFFFFF

    elif opcode == 0x17:  # AUIPC
        cpu.registers[rd] = (cpu.pc + (imm_u << 12)) & 0xFFFFFFFF

    elif opcode == 0x6F:  # JAL
        if rd != 0:
            cpu.registers[rd] = next_pc
        next_pc = (cpu.pc + imm_j) & 0xFFFFFFFF
        #if cpu.logger is not None:
        #    cpu.logger.debug(f"[JAL] pc=0x{cpu.pc:08x}, rd={rd}, target=0x{next_pc:08x}, return_addr=0x{(cpu.pc + 4) & 0xFFFFFFFF:08x}")

    elif opcode == 0x67:  # JALR
        addr_target = (cpu.registers[rs1] + imm_i) & 0xFFFFFFFF
        if rd != 0:
            cpu.registers[rd] = (cpu.pc + 4) & 0xFFFFFFFF
        next_pc = addr_target
        #if cpu.logger is not None:
        #    cpu.logger.debug(f"[JALR] jumping to 0x{next_pc:08x} from rs1=0x{cpu.registers[rs1]:08x}, imm={imm_i}")

    elif opcode == 0x73:  # SYSTEM (ECALL/EBREAK)
        #if cpu.logger is not None:
        #    cpu.logger.debug(f"SYSTEM: opcode=0x{opcode:x}, imm_i={imm_i}")
        if imm_i == 0 and cpu.handle_ecall is not None:  # ECALL
            ecall_ret = cpu.handle_ecall()
            if not ecall_ret:
                cpu.pc = next_pc
                return False
        elif imm_i == 1:  # EBREAK
            if cpu.logger is not None:
                cpu.logger.debug(f"BREAKPOINT: PC=0x{cpu.pc:08x}, a0=0x{cpu.registers[10]:08x}")
            # print register values and stop execution
            cpu.print_registers()
            cpu.pc = next_pc
            return False
        else:
            raise InvalidInstructionError(f"UNHANDLED SYSTEM INSTRUCTION at PC={cpu.pc:08x},: imm_i={imm_i}")
    else:
        raise InvalidInstructionError(f"UNHANDLED INSTRUCTION at PC={cpu.pc:08x},: opcode=0x{opcode:x}, funct3=0x{funct3:x}, funct7=0x{funct7:x}, imm_i={imm_i}, imm_s={imm_s}, imm_b={imm_b}, imm_u={imm_u}, imm_j={imm_j}")
    
    cpu.registers[0] = 0    # x0 is always 0
    cpu.pc = next_pc        # update PC
    return True


# CPU class
class CPU:
    def __init__(self, ram, logger=None):
        self.registers = [0] * 32
        self.pc = 0
        self.ram = ram
        self.handle_ecall = None
        self.logger = logger

    def set_ecall_handler(self, handler):
        self.handle_ecall = handler
        
    def execute(self, inst):
        return execute(self, self.ram, inst)

    def print_registers(self):
        reg_names = [
            'zero', 'ra', 'sp', 'gp', 'tp',
            't0', 't1', 't2', 's0/fp', 's1',
            'a0', 'a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7',
            's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9', 's10', 's11',
            't3', 't4', 't5', 't6'
        ]

        print("\r\nRegister State:\r\n", end='')
        for i, name in enumerate(reg_names):
            value = self.registers[i]
            print(f"{name:<6} (x{i:02}): 0x{value:08x} ({value})\r\n", end='')
