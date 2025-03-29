#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from elftools.elf.elffile import ELFFile

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
    imm_b = sign_extend(((inst >> 7 & 0x1) << 11) |
                        ((inst >> 8 & 0xF) << 1) |
                        ((inst >> 25 & 0x3F) << 5) |
                        ((inst >> 31) << 12), 13)
    imm_u = inst >> 12
    imm_j = sign_extend(((inst >> 21 & 0x3FF) << 1) |
                        ((inst >> 20 & 0x1) << 11) |
                        ((inst >> 12 & 0xFF) << 12) |
                        ((inst >> 31) << 20), 21)

    return opcode, rd, funct3, rs1, rs2, funct7, imm_i, imm_s, imm_b, imm_u, imm_j


def execute(cpu, inst):
    opcode, rd, funct3, rs1, rs2, funct7, imm_i, imm_s, imm_b, imm_u, imm_j = decode(inst)

    #print(f"a0 = 0x{cpu.registers[10]:08x}, a1 = 0x{cpu.registers[11]:08x}")

    assert cpu.registers[0] == 0, "x0 register should always be 0"

    next_pc = (cpu.pc + 4) & 0xFFFFFFFF

    if opcode == 0x33:  # R-type
        if funct3 == 0x0:
            cpu.registers[rd] = (cpu.registers[rs1] + cpu.registers[rs2]) & 0xFFFFFFFF if funct7 == 0x00 else (cpu.registers[rs1] - cpu.registers[rs2]) & 0xFFFFFFFF
        elif funct3 == 0x7:
            cpu.registers[rd] = cpu.registers[rs1] & cpu.registers[rs2]
        elif funct3 == 0x6:
            cpu.registers[rd] = cpu.registers[rs1] | cpu.registers[rs2]
        elif funct3 == 0x4:
            cpu.registers[rd] = cpu.registers[rs1] ^ cpu.registers[rs2]
        elif funct3 == 0x1:
            cpu.registers[rd] = (cpu.registers[rs1] << (cpu.registers[rs2] & 0x1F)) & 0xFFFFFFFF
        elif funct3 == 0x5:
            if funct7 == 0x00:
                cpu.registers[rd] = (cpu.registers[rs1] % (1 << 32)) >> (cpu.registers[rs2] & 0x1F)
            else:
                cpu.registers[rd] = cpu.registers[rs1] >> (cpu.registers[rs2] & 0x1F)
        elif funct3 == 0x2:
            cpu.registers[rd] = int(cpu.registers[rs1] < cpu.registers[rs2])
        elif funct3 == 0x3:
            cpu.registers[rd] = int((cpu.registers[rs1] & 0xFFFFFFFF) < (cpu.registers[rs2] & 0xFFFFFFFF))

    elif opcode == 0x13:  # I-type arithmetic
        if funct3 == 0x0:
            cpu.registers[rd] = (cpu.registers[rs1] + imm_i) & 0xFFFFFFFF
        elif funct3 == 0x7:
            cpu.registers[rd] = cpu.registers[rs1] & imm_i
        elif funct3 == 0x6:
            cpu.registers[rd] = cpu.registers[rs1] | imm_i
        elif funct3 == 0x4:
            cpu.registers[rd] = cpu.registers[rs1] ^ imm_i
        elif funct3 == 0x1:
            cpu.registers[rd] = (cpu.registers[rs1] << (imm_i & 0x1F)) & 0xFFFFFFFF
        elif funct3 == 0x5:
            if funct7 == 0x00:
                cpu.registers[rd] = (cpu.registers[rs1] % (1 << 32)) >> (imm_i & 0x1F)
            else:
                cpu.registers[rd] = cpu.registers[rs1] >> (imm_i & 0x1F)
        elif funct3 == 0x2:
            cpu.registers[rd] = int(cpu.registers[rs1] < imm_i)
        elif funct3 == 0x3:
            cpu.registers[rd] = int((cpu.registers[rs1] & 0xFFFFFFFF) < (imm_i & 0xFFFFFFFF))

    elif opcode == 0x03:  # Loads
        addr = (cpu.registers[rs1] + imm_i) & 0xFFFFFFFF
        if funct3 == 0x2:  # LW
            cpu.registers[rd] = cpu.load_word(addr)
        elif funct3 == 0x0:  # LB
            cpu.registers[rd] = cpu.load_byte(addr)
        elif funct3 == 0x1:  # LH
            cpu.registers[rd] = cpu.load_half(addr)
        elif funct3 == 0x4:  # LBU
            cpu.registers[rd] = cpu.load_byte(addr) & 0xFF
        elif funct3 == 0x5:  # LHU
            cpu.registers[rd] = cpu.load_half(addr) & 0xFFFF

    elif opcode == 0x23:  # Stores
        addr = (cpu.registers[rs1] + imm_s) & 0xFFFFFFFF
        if funct3 == 0x2:  # SW
            cpu.store_word(addr, cpu.registers[rs2])
        elif funct3 == 0x0:  # SB
            cpu.store_byte(addr, cpu.registers[rs2] & 0xFF)
        elif funct3 == 0x1:  # SH
            cpu.store_half(addr, cpu.registers[rs2] & 0xFFFF)

    elif opcode == 0x63:  # Branches
        if (funct3 == 0x0 and cpu.registers[rs1] == cpu.registers[rs2]) or \
           (funct3 == 0x1 and cpu.registers[rs1] != cpu.registers[rs2]) or \
           (funct3 == 0x4 and sign_extend(cpu.registers[rs1],32) < sign_extend(cpu.registers[rs2],32)) or \
           (funct3 == 0x5 and sign_extend(cpu.registers[rs1],32) >= sign_extend(cpu.registers[rs2],32)) or \
           (funct3 == 0x6 and (cpu.registers[rs1] & 0xFFFFFFFF) < (cpu.registers[rs2] & 0xFFFFFFFF)) or \
           (funct3 == 0x7 and (cpu.registers[rs1] & 0xFFFFFFFF) >= (cpu.registers[rs2] & 0xFFFFFFFF)):
            next_pc = (cpu.pc + imm_b) & 0xFFFFFFFF

    elif opcode == 0x37:  # LUI
        cpu.registers[rd] = (imm_u << 12) & 0xFFFFFFFF

    elif opcode == 0x17:  # AUIPC
        cpu.registers[rd] = (cpu.pc + (imm_u << 12)) & 0xFFFFFFFF

    elif opcode == 0x6F:  # JAL
        if rd != 0:
            cpu.registers[rd] = (cpu.pc + 4) & 0xFFFFFFFF
        next_pc = (cpu.pc + imm_j) & 0xFFFFFFFF

    elif opcode == 0x67:  # JALR
        if rd != 0:
            cpu.registers[rd] = (cpu.pc + 4) & 0xFFFFFFFF
        next_pc = (cpu.registers[rs1] + imm_i) & ~1

    elif opcode == 0x73:  # SYSTEM (ECALL/EBREAK)
        if imm_i == 0: # ECALL
            syscall_id = cpu.registers[17]  # a7
            #print(f"[SYSCALL {syscall_id}]")
            if syscall_id == 64:  # _write syscall (newlib standard)
                fd = cpu.registers[10]      # a0
                addr = cpu.registers[11]    # a1
                count = cpu.registers[12]   # a2
                #print(f"[ECALL (write) fd={fd}, addr={addr:08x}, count={count}]")
                data = cpu.memory[addr:addr+count]
                if fd == 1 or fd == 2:  # stdout or stderr
                    print(data.decode(), end='')
                cpu.registers[10] = count  # return count as written
                cpu.pc = next_pc
                return True
            elif syscall_id == 93:  # _exit syscall
                exit_code = cpu.registers[10]  # a0
                print(f"[ECALL (exit)]: code {exit_code}")
                cpu.pc = next_pc
                return False
            else:
                print(f"[ECALL (UNKNOWN {syscall_id})]")
                cpu.pc = next_pc
                return False
        elif imm_i == 1: # EBREAK
            print("[EBREAK]")
            # Handle EBREAK (breakpoint)
            # For now, we just print the registers and stop execution
            cpu.print_registers()
            cpu.pc = next_pc
            return False
        else:
            print(f"[UNHANDLED SYSTEM INSTRUCTION] imm_i={imm_i}")
            cpu.pc = next_pc
            return False

    cpu.registers[0] = 0
    cpu.pc = next_pc
    return True


class CPU:
    def __init__(self, memory_size=1024 * 1024):
        self.registers = [0] * 32
        self.pc = 0
        self.memory = bytearray(memory_size)

    def load_byte(self, addr):
        return int.from_bytes(self.memory[addr:addr+1], 'little', signed=True)

    def load_half(self, addr):
        return int.from_bytes(self.memory[addr:addr+2], 'little', signed=True)

    def load_word(self, addr):
        return int.from_bytes(self.memory[addr:addr+4], 'little', signed=True)

    def store_byte(self, addr, value):
        self.memory[addr] = value & 0xFF

    def store_half(self, addr, value):
        self.memory[addr:addr+2] = (value & 0xFFFF).to_bytes(2, 'little')

    def store_word(self, addr, value):
        self.memory[addr:addr+4] = (value & 0xFFFFFFFF).to_bytes(4, 'little')

    def load_binary(self, binary, addr=0):
        self.memory[addr:addr+len(binary)] = binary
        self.pc = addr

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


### MAIN

cpu = CPU()

# handle different binary file formats
if sys.argv[1][-4:] == '.bin':
    # Load binary instructions into memory
    with open(sys.argv[1], 'rb') as f:
        binary = f.read()
        cpu.load_binary(binary, addr=0)
elif sys.argv[1][-4:] == '.elf':
    # Load ELF file
    with open(sys.argv[1], 'rb') as f:
        elf = ELFFile(f)
        for segment in elf.iter_segments():
            if segment['p_type'] == 'PT_LOAD':
                addr = segment['p_paddr']
                data = segment.data()
                cpu.load_binary(data, addr=addr)
    cpu.pc = elf.header.e_entry
else:
    print("Unsupported file format. Please provide a .bin or .elf file.")
    sys.exit(-1)

# Run execution loop
while True:
    inst = cpu.load_word(cpu.pc)
    continue_exec = execute(cpu, inst)
    if not continue_exec:
        break
    #print(f"PC={cpu.pc:08x}, x5={cpu.registers[5]}")

