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

from machine import MachineError, ExecutionTerminated, SetupError
import random

# Helper functions

def signed32(val):
    return val if val < 0x80000000 else val - 0x100000000

def exec_Rtype(cpu, ram, inst, rd, funct3, rs1, rs2, funct7):
    if funct3 == 0x0:  # ADD/SUB
        if funct7 == 0x00:  # ADD
            cpu.registers[rd] = (cpu.registers[rs1] + cpu.registers[rs2]) & 0xFFFFFFFF
        elif funct7 == 0x20:  # SUB
            cpu.registers[rd] = (cpu.registers[rs1] - cpu.registers[rs2]) & 0xFFFFFFFF
        else:
            if cpu.logger is not None:
                cpu.logger.warning(f"Invalid funct7=0x{funct7:02x} for ADD/SUB at PC=0x{cpu.pc:08x}")
            cpu.trap(cause=2, mtval=inst)  # illegal instruction cause
    elif funct3 == 0x1:  # SLL
        cpu.registers[rd] = (cpu.registers[rs1] << (cpu.registers[rs2] & 0x1F)) & 0xFFFFFFFF
    elif funct3 == 0x2:  # SLT
        cpu.registers[rd] = int(signed32(cpu.registers[rs1]) < signed32(cpu.registers[rs2]))
    elif funct3 == 0x3:  # SLTU
        cpu.registers[rd] = int((cpu.registers[rs1] & 0xFFFFFFFF) < (cpu.registers[rs2] & 0xFFFFFFFF))
    elif funct3 == 0x4:  # XOR
        cpu.registers[rd] = cpu.registers[rs1] ^ cpu.registers[rs2]
    elif funct3 == 0x5:  # SRL/SRA
        shamt = cpu.registers[rs2] & 0x1F
        if funct7 == 0x00:  # SRL
            cpu.registers[rd] = (cpu.registers[rs1] & 0xFFFFFFFF) >> shamt
        elif funct7 == 0x20:  # SRA
            cpu.registers[rd] = (signed32(cpu.registers[rs1]) >> shamt) & 0xFFFFFFFF
        else:
            if cpu.logger is not None:
                cpu.logger.warning(f"Invalid funct7=0x{funct7:02x} for SRL/SRA at PC=0x{cpu.pc:08x}")
            cpu.trap(cause=2, mtval=inst)  # illegal instruction cause
    elif funct3 == 0x6:  # OR
        cpu.registers[rd] = cpu.registers[rs1] | cpu.registers[rs2]
    elif funct3 == 0x7:  # AND
        cpu.registers[rd] = cpu.registers[rs1] & cpu.registers[rs2]

    return True

def exec_Itype(cpu, ram, inst, rd, funct3, rs1, rs2, funct7):
    imm_i = inst >> 20
    if imm_i >= 0x800: imm_i -= 0x1000

    if funct3 == 0x0:  # ADDI
        cpu.registers[rd] = (cpu.registers[rs1] + imm_i) & 0xFFFFFFFF
    elif funct3 == 0x1:  # SLLI
        cpu.registers[rd] = (cpu.registers[rs1] << (imm_i & 0x1F)) & 0xFFFFFFFF
    elif funct3 == 0x2:  # SLTI
        cpu.registers[rd] = int(signed32(cpu.registers[rs1]) < signed32(imm_i))
    elif funct3 == 0x3:  # SLTIU
        cpu.registers[rd] = int((cpu.registers[rs1] & 0xFFFFFFFF) < (imm_i & 0xFFFFFFFF))
    elif funct3 == 0x4:  # XORI
        cpu.registers[rd] = (cpu.registers[rs1] ^ imm_i) & 0xFFFFFFFF
    elif funct3 == 0x5:  # SRLI/SRAI
        shamt = imm_i & 0x1F
        if funct7 == 0x00:  # SRLI
            cpu.registers[rd] = (cpu.registers[rs1] & 0xFFFFFFFF) >> shamt
        elif funct7 == 0x20:  # SRAI
            cpu.registers[rd] = (signed32(cpu.registers[rs1]) >> shamt) & 0xFFFFFFFF
        else:
            if cpu.logger is not None:
                cpu.logger.warning(f"Invalid funct7=0x{funct7:02x} for SRLI/SRAI at PC=0x{cpu.pc:08x}")
            cpu.trap(cause=2, mtval=inst)  # illegal instruction cause
    elif funct3 == 0x6: # ORI
        cpu.registers[rd] = (cpu.registers[rs1] | imm_i) & 0xFFFFFFFF
    elif funct3 == 0x7: # ANDI
        cpu.registers[rd] = (cpu.registers[rs1] & imm_i) & 0xFFFFFFFF

    return True

def exec_loads(cpu, ram, inst, rd, funct3, rs1, rs2, funct7):
    imm_i = inst >> 20
    if imm_i >= 0x800: imm_i -= 0x1000
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
        if cpu.logger is not None:
            cpu.logger.warning(f"Invalid funct3=0x{funct3:02x} for LOAD at PC=0x{cpu.pc:08x}")
        cpu.trap(cause=2, mtval=inst)  # illegal instruction cause

    return True

def exec_stores(cpu, ram, inst, rd, funct3, rs1, rs2, funct7):
    imm_s = ((inst >> 7) & 0x1F) | ((inst >> 25) << 5)
    if imm_s >= 0x800: imm_s -= 0x1000                 
    addr = (cpu.registers[rs1] + imm_s) & 0xFFFFFFFF

    if funct3 == 0x0:  # SB
        ram.store_byte(addr, cpu.registers[rs2] & 0xFF)
    elif funct3 == 0x1:  # SH
        ram.store_half(addr, cpu.registers[rs2] & 0xFFFF)
    elif funct3 == 0x2:  # SW
        ram.store_word(addr, cpu.registers[rs2])
    else:
        if cpu.logger is not None:
            cpu.logger.warning(f"Invalid funct3=0x{funct3:02x} for STORE at PC=0x{cpu.pc:08x}")
        cpu.trap(cause=2, mtval=inst)  # illegal instruction cause

    return True

def exec_branches(cpu, ram, inst, rd, funct3, rs1, rs2, funct7):
    if (
        (funct3 == 0x0 and cpu.registers[rs1] == cpu.registers[rs2]) or  # BEQ
        (funct3 == 0x1 and cpu.registers[rs1] != cpu.registers[rs2]) or  # BNE
        (funct3 == 0x4 and signed32(cpu.registers[rs1]) < signed32(cpu.registers[rs2])) or  # BLT
        (funct3 == 0x5 and signed32(cpu.registers[rs1]) >= signed32(cpu.registers[rs2])) or  # BGE
        (funct3 == 0x6 and (cpu.registers[rs1] & 0xFFFFFFFF) < (cpu.registers[rs2] & 0xFFFFFFFF)) or  # BLTU
        (funct3 == 0x7 and (cpu.registers[rs1] & 0xFFFFFFFF) >= (cpu.registers[rs2] & 0xFFFFFFFF))  # BGEU
        ):
        imm_b = (((inst >> 7) & 0x1) << 11)  | \
                (((inst >> 8) & 0xF) << 1)   | \
                (((inst >> 25) & 0x3F) << 5) | \
                ((inst >> 31) << 12)
        if imm_b >= 0x1000: imm_b -= 0x2000
        cpu.next_pc = (cpu.pc + imm_b) & 0xFFFFFFFF
    elif funct3 == 0x2 or funct3 == 0x3:
        if cpu.logger is not None:
            cpu.logger.warning(f"Invalid branch instruction funct3=0x{funct3:X} at PC=0x{cpu.pc:08x}")
        cpu.trap(cause=2, mtval=inst)  # illegal instruction cause

    return True

def exec_LUI(cpu, ram, inst, rd, funct3, rs1, rs2, funct7):
    imm_u = inst >> 12
    cpu.registers[rd] = (imm_u << 12) & 0xFFFFFFFF
    return True

def exec_AUIPC(cpu, ram, inst, rd, funct3, rs1, rs2, funct7):
    imm_u = inst >> 12
    cpu.registers[rd] = (cpu.pc + (imm_u << 12)) & 0xFFFFFFFF
    return True

def exec_JAL(cpu, ram, inst, rd, funct3, rs1, rs2, funct7):
    imm_j = (((inst >> 21) & 0x3FF) << 1) | \
            (((inst >> 20) & 0x1) << 11)  | \
            (((inst >> 12) & 0xFF) << 12) | \
            ((inst >> 31) << 20)
    if imm_j >= 0x100000: imm_j -= 0x200000

    if rd != 0:
        cpu.registers[rd] = cpu.next_pc
    cpu.next_pc = (cpu.pc + imm_j) & 0xFFFFFFFF
    #if cpu.logger is not None:
    #    cpu.logger.debug(f"[JAL] pc=0x{cpu.pc:08x}, rd={rd}, target=0x{cpu.next_pc:08x}, return_addr=0x{(cpu.pc + 4) & 0xFFFFFFFF:08x}")

    return True

def exec_JALR(cpu, ram, inst, rd, funct3, rs1, rs2, funct7):
    imm_i = inst >> 20
    if imm_i >= 0x800: imm_i -= 0x1000
    addr_target = (cpu.registers[rs1] + imm_i) & 0xFFFFFFFF

    if rd != 0:
        cpu.registers[rd] = (cpu.pc + 4) & 0xFFFFFFFF
    cpu.next_pc = addr_target
    #if cpu.logger is not None:
    #    cpu.logger.debug(f"[JALR] jumping to 0x{cpu.next_pc:08x} from rs1=0x{cpu.registers[rs1]:08x}, imm={imm_i}")

    return True

def exec_SYSTEM(cpu, ram, inst, rd, funct3, rs1, rs2, funct7):
    if inst == 0x00000073:  # ECALL
        if (cpu.csrs[0x305] == 0) and (cpu.handle_ecall is not None):  # no trap handler, Python handler set
            cpu.handle_ecall()
            cpu.bypassed_trap_return(cause=11)
        elif cpu.csrs[0x305] != 0:  # trap handler set
            cpu.trap(cause=11)  # cause 11 == machine ECALL
        else:
            raise MachineError("No trap handler and no Python ecall handler installed: cannot process ECALL instruction")

    elif inst == 0x30200073:  # MRET
        cpu.next_pc = cpu.csrs[0x341]   # return address <- mepc

        mstatus = cpu.csrs[0x300]       # mstatus
        mpie = (mstatus >> 7) & 1       # extract MPIE
        mstatus = (mstatus & ~(1 << 3)) | (mpie << 3)  # MIE <- MPIE
        mstatus |= (1 << 7)             # MPIE = 1 (re-arm)
        cpu.csrs[0x300] = mstatus

    elif funct3 in (0b001, 0b010, 0b011, 0b101, 0b110, 0b111):  # CSRRW, CSRRS, CSRRC
        csr = (inst >> 20) & 0xFFF
        old = cpu.csrs.get(csr, 0)

        # handle register vs immediate operations
        rs1_val = cpu.registers[rs1] if (funct3 < 0b101) else rs1

        # handle read-only CSRs
        if csr in CSR_RO and ((funct3 in (0b001, 0b101)) or (rs1_val != 0)):
            cpu.trap(cause=2, mtval=inst)  # 2 = illegal instruction

        if funct3 in (0b001, 0b101):  # CSRRW / CSRRWI
            cpu.csrs[csr] = rs1_val
        elif funct3 in (0b010, 0b110):  # CSRRS / CSRRSI
            if rs1_val != 0:
                cpu.csrs[csr] = old | rs1_val
        elif funct3 in (0b011, 0b111):  # CSRRC / CSRRCI
            if rs1_val != 0:
                cpu.csrs[csr] = old & ~rs1_val
      
        if rd != 0:
            cpu.registers[rd] = old
        
    elif inst == 0x00100073:  # EBREAK
        if cpu.csrs[0x305] == 0: # no trap handler, terminate execution
            cpu.bypassed_trap_return(cause=3)
            cpu.print_registers()
            raise ExecutionTerminated(f"BREAKPOINT at PC={cpu.pc:08x}")
        else:  # trap
            cpu.trap(cause=3)  # 3 = machine EBREAK
    
    else:
        if cpu.logger is not None:
            cpu.logger.warning(f"Unhandled system instruction 0x{inst:08x} at PC={cpu.pc:08x}")
        cpu.trap(cause=2, mtval=inst)  # illegal instruction cause
    
    return True

# dispatch table for opcode handlers
opcode_handler = {
    0x33:   exec_Rtype,     # R-type
    0x13:   exec_Itype,     # I-type
    0x03:   exec_loads,     # Loads
    0x23:   exec_stores,    # Stores
    0x63:   exec_branches,  # Branches
    0x37:   exec_LUI,       # LUI
    0x17:   exec_AUIPC,     # AUIPC
    0x6F:   exec_JAL,       # JAL
    0x67:   exec_JALR,      # JALR
    0x73:   exec_SYSTEM     # SYSTEM (ECALL/EBREAK)
}

CSR_RO = {
    0x301,  # misa
    0xF11,  # mvendorid
    0xF12,  # marchid
    0xF13,  # mimpid
    0xF14   # mhartid
}

# CPU class
class CPU:
    def __init__(self, ram, init_regs=None, logger=None):
        self.registers = [0] * 32
        self.csrs = {
            0x300: 0x00000000,  # mstatus
            0x301: 0x40000100,  # misa (RO, bits 30 and 8 set: RV32I)
            0x305: 0x00000000,  # mtvec
            0x340: 0x00000000,  # mscratch
            0x341: 0x00000000,  # mepc
            0x342: 0x00000000,  # mcause
            0xF11: 0x00000000,  # mvendorid (RO)
            0xF12: 0x00000000,  # marchid (RO)
            0xF13: 0x00000000,  # mimpid (RO)
            0xF14: 0x00000000   # mhartid (RO)
        }
        self.pc = 0
        self.next_pc = 0
        self.ram = ram
        self.handle_ecall = None
        self.logger = logger
        if init_regs is not None and init_regs != 'zero':
            self.init_registers(init_regs)

    def set_ecall_handler(self, handler):
        self.handle_ecall = handler

    # Instruction execution
    def execute(self, inst):
        opcode = inst & 0x7F
        rd = (inst >> 7) & 0x1F
        funct3 = (inst >> 12) & 0x7
        rs1 = (inst >> 15) & 0x1F
        rs2 = (inst >> 20) & 0x1F
        funct7 = (inst >> 25) & 0x7F

        self.next_pc = (self.pc + 4) & 0xFFFFFFFF

        if opcode in opcode_handler:
            continue_exec = (opcode_handler[opcode])(self, self.ram, inst, rd, funct3, rs1, rs2, funct7)  # dispatch to opcode handler
        else:
            if self.logger is not None:
                self.logger.warning(f"Invalid instruction at PC={self.pc:08x}: 0x{inst:08x}, opcode=0x{opcode:x}")
            self.trap(cause=2, mtval=inst)  # illegal instruction cause
            continue_exec = True

        self.registers[0] = 0       # x0 is always 0
        self.pc = self.next_pc      # update PC

        return continue_exec
    
    def trap(self, cause, mtval=0):
        self.csrs[0x341] = self.pc          # mepc
        self.csrs[0x342] = cause            # mcause
        self.csrs[0x343] = mtval            # mtval
        self.next_pc = self.csrs[0x305]     # mtvec

        mstatus = self.csrs[0x300]
        mie = (mstatus >> 3) & 1            # extract MIE
        mstatus &= ~(1 << 3 | 1 << 7)       # clear MIE and MPIE
        mstatus |= (mie << 7)               # MPIE <- MIE
        self.csrs[0x300] = mstatus

    # Performs the side effects of trap + mret,
    # for those cases when the trap is handled by the emulator
    def bypassed_trap_return(self, cause, mtval=0):
        self.csrs[0x341] = self.pc          # mepc
        self.csrs[0x342] = cause            # mcause
        self.csrs[0x343] = mtval            # mtval
        self.csrs[0x300] |= (1 << 7)        # MPIE = 1
        # (MIE, bit 3, stays unchanged)

    # CPU register initialization
    def init_registers(self, mode='0x00000000'):
        self.registers[0] = 0
        if mode == 'random':
            for i in range(1, 32):
                self.registers[i] = random.getrandbits(32)
        else:
            try:
                value = int(mode, 0) & 0xFFFFFFFF
            except ValueError:
                raise SetupError(f"Invalid --init-regs value: {mode}")
            for i in range(1, 32):
                self.registers[i] = value

    # print state of all CPU registers
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
