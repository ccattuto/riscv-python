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

from machine import MachineError, ExecutionTerminated, SetupError
from rvc import expand_compressed
import random

# Opcode handlers

def signed32(val):
    return val if val < 0x80000000 else val - 0x100000000

def exec_Rtype(cpu, ram, inst, rd, funct3, rs1, rs2, funct7):
    if funct3 == 0x0:  # ADD/SUB/MUL
        if funct7 == 0x01:  # MUL (M extension)
            # Multiply: return lower 32 bits of product
            a = signed32(cpu.registers[rs1])
            b = signed32(cpu.registers[rs2])
            result = (a * b) & 0xFFFFFFFF
            cpu.registers[rd] = result
        elif funct7 == 0x00:  # ADD
            cpu.registers[rd] = (cpu.registers[rs1] + cpu.registers[rs2]) & 0xFFFFFFFF
        elif funct7 == 0x20:  # SUB
            cpu.registers[rd] = (cpu.registers[rs1] - cpu.registers[rs2]) & 0xFFFFFFFF
        else:
            if cpu.logger is not None:
                cpu.logger.warning(f"Invalid funct7=0x{funct7:02x} for ADD/SUB/MUL at PC=0x{cpu.pc:08X}")
            cpu.trap(cause=2, mtval=inst)  # illegal instruction cause
    elif funct3 == 0x1:  # SLL/MULH
        if funct7 == 0x01:  # MULH (M extension)
            # Multiply high: signed × signed, return upper 32 bits
            a = signed32(cpu.registers[rs1])
            b = signed32(cpu.registers[rs2])
            result = (a * b) >> 32
            cpu.registers[rd] = result & 0xFFFFFFFF
        elif funct7 == 0x00:  # SLL
            cpu.registers[rd] = (cpu.registers[rs1] << (cpu.registers[rs2] & 0x1F)) & 0xFFFFFFFF
        else:
            if cpu.logger is not None:
                cpu.logger.warning(f"Invalid funct7=0x{funct7:02x} for SLL/MULH at PC=0x{cpu.pc:08X}")
            cpu.trap(cause=2, mtval=inst)  # illegal instruction cause
    elif funct3 == 0x2:  # SLT/MULHSU
        if funct7 == 0x01:  # MULHSU (M extension)
            # Multiply high: signed × unsigned, return upper 32 bits
            a = signed32(cpu.registers[rs1])
            b = cpu.registers[rs2] & 0xFFFFFFFF
            result = (a * b) >> 32
            cpu.registers[rd] = result & 0xFFFFFFFF
        elif funct7 == 0x00:  # SLT
            cpu.registers[rd] = int(signed32(cpu.registers[rs1]) < signed32(cpu.registers[rs2]))
        else:
            if cpu.logger is not None:
                cpu.logger.warning(f"Invalid funct7=0x{funct7:02x} for SLT/MULHSU at PC=0x{cpu.pc:08X}")
            cpu.trap(cause=2, mtval=inst)  # illegal instruction cause
    elif funct3 == 0x3:  # SLTU/MULHU
        if funct7 == 0x01:  # MULHU (M extension)
            # Multiply high: unsigned × unsigned, return upper 32 bits
            a = cpu.registers[rs1] & 0xFFFFFFFF
            b = cpu.registers[rs2] & 0xFFFFFFFF
            result = (a * b) >> 32
            cpu.registers[rd] = result & 0xFFFFFFFF
        elif funct7 == 0x00:  # SLTU
            cpu.registers[rd] = int((cpu.registers[rs1] & 0xFFFFFFFF) < (cpu.registers[rs2] & 0xFFFFFFFF))
        else:
            if cpu.logger is not None:
                cpu.logger.warning(f"Invalid funct7=0x{funct7:02x} for SLTU/MULHU at PC=0x{cpu.pc:08X}")
            cpu.trap(cause=2, mtval=inst)  # illegal instruction cause
    elif funct3 == 0x4:  # XOR/DIV
        if funct7 == 0x01:  # DIV (M extension)
            # Signed division (RISC-V uses truncating division, rounding towards zero)
            dividend = signed32(cpu.registers[rs1])
            divisor = signed32(cpu.registers[rs2])
            if divisor == 0:
                # Division by zero: quotient = -1
                cpu.registers[rd] = 0xFFFFFFFF
            elif dividend == -2147483648 and divisor == -1:
                # Overflow: return MIN_INT
                cpu.registers[rd] = 0x80000000
            else:
                # Use truncating division (towards zero), not floor division
                result = int(dividend / divisor)
                cpu.registers[rd] = result & 0xFFFFFFFF
        elif funct7 == 0x00:  # XOR
            cpu.registers[rd] = cpu.registers[rs1] ^ cpu.registers[rs2]
        else:
            if cpu.logger is not None:
                cpu.logger.warning(f"Invalid funct7=0x{funct7:02x} for XOR/DIV at PC=0x{cpu.pc:08X}")
            cpu.trap(cause=2, mtval=inst)  # illegal instruction cause
    elif funct3 == 0x5:  # SRL/SRA/DIVU
        if funct7 == 0x01:  # DIVU (M extension)
            # Unsigned division
            dividend = cpu.registers[rs1] & 0xFFFFFFFF
            divisor = cpu.registers[rs2] & 0xFFFFFFFF
            if divisor == 0:
                # Division by zero: quotient = 2^32 - 1
                cpu.registers[rd] = 0xFFFFFFFF
            else:
                result = dividend // divisor
                cpu.registers[rd] = result & 0xFFFFFFFF
        else:
            shamt = cpu.registers[rs2] & 0x1F
            if funct7 == 0x00:  # SRL
                cpu.registers[rd] = (cpu.registers[rs1] & 0xFFFFFFFF) >> shamt
            elif funct7 == 0x20:  # SRA
                cpu.registers[rd] = (signed32(cpu.registers[rs1]) >> shamt) & 0xFFFFFFFF
            else:
                if cpu.logger is not None:
                    cpu.logger.warning(f"Invalid funct7=0x{funct7:02x} for SRL/SRA/DIVU at PC=0x{cpu.pc:08X}")
                cpu.trap(cause=2, mtval=inst)  # illegal instruction cause
    elif funct3 == 0x6:  # OR/REM
        if funct7 == 0x01:  # REM (M extension)
            # Signed remainder (RISC-V uses truncating division, rounding towards zero)
            dividend = signed32(cpu.registers[rs1])
            divisor = signed32(cpu.registers[rs2])
            if divisor == 0:
                # Division by zero: remainder = dividend
                cpu.registers[rd] = cpu.registers[rs1] & 0xFFFFFFFF
            elif dividend == -2147483648 and divisor == -1:
                # Overflow: remainder = 0
                cpu.registers[rd] = 0
            else:
                # Use truncating remainder: dividend - trunc(dividend/divisor) * divisor
                result = dividend - int(dividend / divisor) * divisor
                cpu.registers[rd] = result & 0xFFFFFFFF
        elif funct7 == 0x00:  # OR
            cpu.registers[rd] = cpu.registers[rs1] | cpu.registers[rs2]
        else:
            if cpu.logger is not None:
                cpu.logger.warning(f"Invalid funct7=0x{funct7:02x} for OR/REM at PC=0x{cpu.pc:08X}")
            cpu.trap(cause=2, mtval=inst)  # illegal instruction cause
    elif funct3 == 0x7:  # AND/REMU
        if funct7 == 0x01:  # REMU (M extension)
            # Unsigned remainder
            dividend = cpu.registers[rs1] & 0xFFFFFFFF
            divisor = cpu.registers[rs2] & 0xFFFFFFFF
            if divisor == 0:
                # Division by zero: remainder = dividend
                cpu.registers[rd] = cpu.registers[rs1] & 0xFFFFFFFF
            else:
                result = dividend % divisor
                cpu.registers[rd] = result & 0xFFFFFFFF
        elif funct7 == 0x00:  # AND
            cpu.registers[rd] = cpu.registers[rs1] & cpu.registers[rs2]
        else:
            if cpu.logger is not None:
                cpu.logger.warning(f"Invalid funct7=0x{funct7:02x} for AND/REMU at PC=0x{cpu.pc:08X}")
            cpu.trap(cause=2, mtval=inst)  # illegal instruction cause

def exec_Itype(cpu, ram, inst, rd, funct3, rs1, rs2, funct7):
    imm_i = inst >> 20
    if imm_i >= 0x800: imm_i -= 0x1000

    if funct3 == 0x0:  # ADDI
        cpu.registers[rd] = (cpu.registers[rs1] + imm_i) & 0xFFFFFFFF
    elif funct3 == 0x1:  # SLLI
        if funct7 == 0x00:
            cpu.registers[rd] = (cpu.registers[rs1] << (imm_i & 0x1F)) & 0xFFFFFFFF
        else:
            if cpu.logger is not None:
                cpu.logger.warning(f"Invalid funct7=0x{funct7:02x} for SLLI at PC=0x{cpu.pc:08X}")
            cpu.trap(cause=2, mtval=inst)  # illegal instruction cause
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
                cpu.logger.warning(f"Invalid funct7=0x{funct7:02x} for SRLI/SRAI at PC=0x{cpu.pc:08X}")
            cpu.trap(cause=2, mtval=inst)  # illegal instruction cause
    elif funct3 == 0x6: # ORI
        cpu.registers[rd] = (cpu.registers[rs1] | imm_i) & 0xFFFFFFFF
    elif funct3 == 0x7: # ANDI
        cpu.registers[rd] = (cpu.registers[rs1] & imm_i) & 0xFFFFFFFF

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
            cpu.logger.warning(f"Invalid funct3=0x{funct3:02x} for LOAD at PC=0x{cpu.pc:08X}")
        cpu.trap(cause=2, mtval=inst)  # illegal instruction cause

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
            cpu.logger.warning(f"Invalid funct3=0x{funct3:02x} for STORE at PC=0x{cpu.pc:08X}")
        cpu.trap(cause=2, mtval=inst)  # illegal instruction cause

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
        addr_target = (cpu.pc + imm_b) & 0xFFFFFFFF
        # Check alignment: 2-byte (RVC) or 4-byte (no RVC)
        if addr_target & cpu.alignment_mask:
            cpu.trap(cause=0, mtval=addr_target)  # unaligned address
        else:
            cpu.next_pc = addr_target
    elif funct3 == 0x2 or funct3 == 0x3:
        if cpu.logger is not None:
            cpu.logger.warning(f"Invalid branch instruction funct3=0x{funct3:X} at PC=0x{cpu.pc:08X}")
        cpu.trap(cause=2, mtval=inst)  # illegal instruction cause

def exec_LUI(cpu, ram, inst, rd, funct3, rs1, rs2, funct7):
    imm_u = inst >> 12
    cpu.registers[rd] = (imm_u << 12) & 0xFFFFFFFF

def exec_AUIPC(cpu, ram, inst, rd, funct3, rs1, rs2, funct7):
    imm_u = inst >> 12
    cpu.registers[rd] = (cpu.pc + (imm_u << 12)) & 0xFFFFFFFF

def exec_JAL(cpu, ram, inst, rd, funct3, rs1, rs2, funct7):
    imm_j = (((inst >> 21) & 0x3FF) << 1) | \
            (((inst >> 20) & 0x1) << 11)  | \
            (((inst >> 12) & 0xFF) << 12) | \
            ((inst >> 31) << 20)
    if imm_j >= 0x100000: imm_j -= 0x200000
    addr_target = (cpu.pc + imm_j) & 0xFFFFFFFF  # (compared to JALR, no need to clear bit 0 here)
    # Check alignment: 2-byte (RVC) or 4-byte (no RVC)
    if addr_target & cpu.alignment_mask:
        cpu.trap(cause=0, mtval=addr_target)  # unaligned address
    else:
        if rd != 0:
            # Use inst_size (2 for compressed, 4 for normal) for return address
            cpu.registers[rd] = (cpu.pc + cpu.inst_size) & 0xFFFFFFFF
        cpu.next_pc = addr_target
        #if cpu.logger is not None:
        #    cpu.logger.debug(f"[JAL] pc=0x{cpu.pc:08X}, rd={rd}, target=0x{cpu.next_pc:08X}, return_addr=0x{(cpu.pc + cpu.inst_size) & 0xFFFFFFFF:08X}")

def exec_JALR(cpu, ram, inst, rd, funct3, rs1, rs2, funct7):
    imm_i = inst >> 20
    if imm_i >= 0x800: imm_i -= 0x1000
    addr_target = (cpu.registers[rs1] + imm_i) & 0xFFFFFFFE  # clear bit 0
    # Check alignment: 2-byte (RVC) or 4-byte (no RVC)
    if addr_target & cpu.alignment_mask:
        cpu.trap(cause=0, mtval=addr_target)  # unaligned address
    else:
        if rd != 0:
            # Use inst_size (2 for compressed, 4 for normal) for return address
            cpu.registers[rd] = (cpu.pc + cpu.inst_size) & 0xFFFFFFFF
        cpu.next_pc = addr_target
        #if cpu.logger is not None:
        #    cpu.logger.debug(f"[JALR] jumping to 0x{cpu.next_pc:08X} from rs1=0x{cpu.registers[rs1]:08X}, imm={imm_i}")

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
        mepc = cpu.csrs[0x341]
        # Check alignment: 2-byte (RVC) or 4-byte (no RVC)
        if mepc & cpu.alignment_mask:
            cpu.trap(cause=0, mtval=mepc)  # unaligned address
        else:
            cpu.next_pc = mepc                              # return address <- mepc

            mstatus = cpu.csrs[0x300]                       # mstatus
            mpie = (mstatus >> 7) & 1                       # extract MPIE
            mstatus = (mstatus & ~(1 << 3)) | (mpie << 3)   # MIE <- MPIE
            mstatus |= (1 << 7)                             # MPIE = 1 (re-arm)
            cpu.csrs[0x300] = mstatus
    
    elif inst == 0x00100073:  # EBREAK
        # syscalls >= 0xFFFF0000 bypass the rest of the EBREAK logic and are used for logging.
        a7 = cpu.registers[17]
        if a7 >= 0xFFFF0000:
            if cpu.logger is None:
                return
            a0 = cpu.registers[10]
            if a7 == 0xFFFF0000:  # print all registers
                cpu.print_registers()
            elif a7 == 0xFFFF0001:  # log integer
                cpu.logger.info(f"EBREAK LOG INT: 0x{a0:08X} ({a0})")
            elif a7 == 0xFFFF0002:  # log string
                str = cpu.ram.load_cstring(a0)
                cpu.logger.info(f"EBREAK LOG STR: {str}")
            elif a7 == 0xFFFF0003:  # log string + integer (decimal)
                str = cpu.ram.load_cstring(a0)
                a1 = cpu.registers[11]
                cpu.logger.info(f"EBREAK LOG STR_INT: {str}{a1}")
            elif a7 == 0xFFFF0004:  # log string + integer (hex)
                str = cpu.ram.load_cstring(a0)
                a1 = cpu.registers[11]
                cpu.logger.info(f"EBREAK LOG STR_XINT: {str}0x{a1:08X}")
            return

        if cpu.csrs[0x305] == 0: # no trap handler, terminate execution
            cpu.bypassed_trap_return(cause=3)
            cpu.print_registers()
            raise ExecutionTerminated(f"BREAKPOINT at PC={cpu.pc:08X}")
        else:  # trap
            cpu.trap(cause=3)  # 3 = machine EBREAK
    
    elif funct3 in (0b001, 0b010, 0b011, 0b101, 0b110, 0b111):  # CSRRW/CSRRWI, CSRRS/CSRRSI, CSRRC/CSRRCI
        csr = (inst >> 20) & 0xFFF
        old = cpu.csrs[csr]
        
        # handle register vs immediate operations
        rs1_val = cpu.registers[rs1] if (funct3 < 0b101) else rs1
        
        # handle read-only CSRs
        if csr in cpu.CSR_RO and ((funct3 in (0b001, 0b101)) or (rs1_val != 0)):
            cpu.trap(cause=2, mtval=inst)  # 2 = illegal instruction

        if funct3 in (0b001, 0b101):  # CSRRW / CSRRWI
            if csr == 0x305:  # we don't support vectored interrupts, so mask away lower 2 bits of mtvect
                cpu.csrs[csr] = rs1_val & ~0x3
            elif not (csr in cpu.CSR_NOWRITE):
                cpu.csrs[csr] = rs1_val

           # Atomic update of mtime
            if csr in (0x7C0, 0x7C1):
                cpu.mtime_lo_updated |= (csr == 0x7C0)
                cpu.mtime_hi_updated |= (csr == 0x7C1)
                if cpu.mtime_lo_updated and cpu.mtime_hi_updated:
                    cpu.mtime = (cpu.csrs[0x7C1] << 32) | cpu.csrs[0x7C0]
                    cpu.mtime_lo_updated = False
                    cpu.mtime_hi_updated = False
                    cpu.mtip = (cpu.mtime >= cpu.mtimecmp)

            # Atomic update of mtimecmp
            if csr in (0x7C2, 0x7C3):
                cpu.mtimecmp_lo_updated |= (csr == 0x7C2)
                cpu.mtimecmp_hi_updated |= (csr == 0x7C3)
                if cpu.mtimecmp_lo_updated and cpu.mtimecmp_hi_updated:
                    cpu.mtimecmp = (cpu.csrs[0x7C3] << 32) | cpu.csrs[0x7C2]
                    cpu.mtimecmp_lo_updated = False
                    cpu.mtimecmp_hi_updated = False
                    cpu.mtime_countdown = cpu.mtimecmp - cpu.mtime
                    cpu.mtip = (cpu.mtime >= cpu.mtimecmp)

        elif funct3 in (0b010, 0b110):  # CSRRS / CSRRSI
            if rs1_val != 0 and not (csr in cpu.CSR_NOWRITE):
                cpu.csrs[csr] = old | rs1_val
        
        elif funct3 in (0b011, 0b111):  # CSRRC / CSRRCI
            if rs1_val != 0 and not (csr in cpu.CSR_NOWRITE):
                cpu.csrs[csr] = old & ~rs1_val

        if csr == 0x300:  # MPP field of mstatus is forced to 0b11 as we only support machine mode
            cpu.csrs[0x300] |= 0x00001800  # set bits 12 and 11

        if rd != 0:
            if csr == 0x7C0:
                old = cpu.mtime & 0xFFFFFFFF
            elif csr == 0x7C1:
                old = (cpu.mtime >> 32) & 0xFFFFFFFF
            elif csr == 0x7C2:
                old = cpu.mtimecmp & 0xFFFFFFFF
            elif csr == 0x7C3:
                old = (cpu.mtimecmp >> 32) & 0xFFFFFFFF
            
            cpu.registers[rd] = old

    elif inst == 0x10500073:  # WFI
        pass  # implemented as a no-operation
    
    else:
        if cpu.logger is not None:
            cpu.logger.warning(f"Unhandled system instruction 0x{inst:08X} at PC={cpu.pc:08X}")
        cpu.trap(cause=2, mtval=inst)  # illegal instruction cause

def exec_MISCMEM(cpu, ram, inst, rd, funct3, rs1, rs2, funct7):
    if funct3 in (0b000, 0b001):  # FENCE / FENCE.I
        pass  # NOP
    else:
        if cpu.logger is not None:
            cpu.logger.warning(f"Invalid misc-mem instruction funct3=0x{funct3:X} at PC=0x{cpu.pc:08X}")
        cpu.trap(cause=2, mtval=inst)  # illegal instruction cause

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
    0x73:   exec_SYSTEM,    # SYSTEM (ECALL/EBREAK)
    0x0F:   exec_MISCMEM    # MISC-MEM
}


# Compressed instruction expansion (RVC extension) - moved to rvc.py
# Import: from rvc import expand_compressed

# CPU class
class CPU:
    def __init__(self, ram, init_regs=None, logger=None, trace_traps=False, rvc_enabled=False):
        # registers
        self.registers = [0] * 32
        if init_regs is not None and init_regs != 'zero':
            self.init_registers(init_regs)
        self.pc = 0
        self.next_pc = 0

        self.ram = ram
        self.handle_ecall = None  # system calls handler
        self.rvc_enabled = rvc_enabled  # RVC extension enabled flag
        # Cache alignment mask for performance: 0x1 for RVC (2-byte), 0x3 for RV32I (4-byte)
        self.alignment_mask = 0x1 if rvc_enabled else 0x3

        self.logger = logger
        self.trace_traps = trace_traps

        # Instruction size for current instruction (2 for compressed, 4 for normal)
        # Used by handlers that need to compute return addresses (JAL, JALR)
        self.inst_size = 4

        # CSRs
        self.csrs = [0] * 4096
        # 0x300 mstatus
        # 0x301 misa (RO, bits 30 and 8 set: RV32I)
        # 0x304 mie
        # 0x305 mtvec
        # 0x340 mscratch
        # 0x341 mepc
        # 0x342 mcause
        # 0x343 mtval
        # 0x344 mip
        # 0x7C0 mtime_low
        # 0x7C1 mtime_high
        # 0x7C2 mtimecmp_low
        # 0x7C3 mtimecmp_high
        # 0xF11 mvendorid (RO)
        # 0xF12 marchid (RO)
        # 0xF13 mimpid (RO)
        # 0xF14 mhartid (RO)

        self.csrs[0x301] = 0x40000104  # misa (RO, bits 30, 8, and 2 set: RV32IC)
        self.csrs[0x300] = 0x00001800  # mstatus (machine mode only: MPP field kept = 0b11)
        self.csrs[0x7C2] = 0xFFFFFFFF  # mtimecmp_low
        self.csrs[0x7C3] = 0xFFFFFFFF  # mtimecmp_hi
        self.csrs[0xF12] = 0x00000001  # marchid (RO)
        self.csrs[0xF13] = 0x20250400  # mimpid (RO)

        # read-only CSRs: writes cause a trap
        self.CSR_RO = { 0xF11, 0xF12, 0xF13, 0xF14 }
        # mvendorid, marchid, mimpid, mhartid
        # (misa should be here, but tests expect it to be writable without trapping)

        # read-only CSRs: writes are ignored
        self.CSR_NOWRITE ={ 0x301, 0xB02, 0xB82, 0x7A0, 0x7A1, 0x7A2 }
        # misa, minstret, minstreth, tselect, tdata1, tdata2

        self.mtime = 0x00000000_00000000
        self.mtimecmp = 0xFFFFFFFF_FFFFFFFF
        self.mtime_lo_updated = False
        self.mtime_hi_updated = False
        self.mtimecmp_lo_updated = False
        self.mtimecmp_hi_updated = False
        self.mtip = False

        # name - ID register maps
        self.REG_NUM_NAME = {}
        self.REG_NAME_NUM = {}
        self.REG_NAMES = [
            'zero', 'ra', 'sp', 'gp', 'tp',
            't0', 't1', 't2', 's0/fp', 's1',
            'a0', 'a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7',
            's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9', 's10', 's11',
            't3', 't4', 't5', 't6'
        ]
        for num, name in enumerate(self.REG_NAMES):
            self.REG_NUM_NAME[num] = name
            self.REG_NAME_NUM[name] = num
            self.REG_NAME_NUM[f"x{num}"] = num
        self.REG_NAME_NUM['s0'] = 8
        self.REG_NAME_NUM['fp'] = 8

        # name - address CSR maps
        self.CSR_NAME_ADDR = {}
        self.CSR_ADDR_NAME = {}
        csr_names = {
            'mstatus': 0x300, 'misa': 0x301, 'mie': 0x304, 'mtvec': 0x305,
            'mscratch': 0x340, 'mepc': 0x341, 'mcause': 0x342, 'mtval': 0x343, 'mip': 0x344,
            #'mtime_lo': 0x7C0, 'mtime_hi': 0x7C1, 'mtimecmp_lo': 0x7C2, 'mtimecmp_hi': 0x7C3
        }
        for name, addr in csr_names.items():
            self.CSR_NAME_ADDR[name] = addr
            self.CSR_ADDR_NAME[addr] = name

        # Trap cause descriptions (RISC-V Privileged Spec)
        self.TRAP_CAUSE_NAMES = {
            0: "Instruction address misaligned",
            1: "Instruction access fault",
            2: "Illegal instruction",
            3: "Breakpoint",
            4: "Load address misaligned",
            5: "Load access fault",
            6: "Store/AMO address misaligned",
            7: "Store/AMO access fault",
            8: "Environment call from U-mode",
            9: "Environment call from S-mode",
            11: "Environment call from M-mode",
            12: "Instruction page fault",
            13: "Load page fault",
            15: "Store/AMO page fault",
            0x80000007: "Machine timer interrupt",
        }

        # instruction decode caches
        self.decode_cache = {}  # For 32-bit instructions (or when RVC disabled)
        self.decode_cache_compressed = {}  # For 16-bit compressed instructions (when RVC enabled)

    # Set handler for system calls
    def set_ecall_handler(self, handler):
        self.handle_ecall = handler

    # Instruction execution (supports both 32-bit and compressed 16-bit instructions)
    def execute(self, inst):
        # Fast path for RV32I without RVC extension (zero overhead)
        if not self.rvc_enabled:
            try:
                opcode, rd, funct3, rs1, rs2, funct7 = self.decode_cache[inst >> 2]
            except KeyError:
                opcode = inst & 0x7F
                rd = (inst >> 7) & 0x1F
                funct3 = (inst >> 12) & 0x7
                rs1 = (inst >> 15) & 0x1F
                rs2 = (inst >> 20) & 0x1F
                funct7 = (inst >> 25) & 0x7F
                self.decode_cache[inst >> 2] = (opcode, rd, funct3, rs1, rs2, funct7)

            self.next_pc = (self.pc + 4) & 0xFFFFFFFF
            self.inst_size = 4

            if opcode in opcode_handler:
                (opcode_handler[opcode])(self, self.ram, inst, rd, funct3, rs1, rs2, funct7)
            else:
                if self.logger is not None:
                    self.logger.warning(f"Invalid instruction at PC={self.pc:08X}: 0x{inst:08X}, opcode=0x{opcode:x}")
                self.trap(cause=2, mtval=inst)

            self.registers[0] = 0
            return

        # RVC path: handle both 32-bit and 16-bit compressed instructions
        is_compressed = (inst & 0x3) != 0x3

        if is_compressed:
            # Compressed 16-bit instruction
            inst16 = inst & 0xFFFF
            try:
                opcode, rd, funct3, rs1, rs2, funct7, expanded_inst = self.decode_cache_compressed[inst16]
                inst = expanded_inst
                inst_size = 2
            except KeyError:
                # Expand compressed instruction to 32-bit equivalent
                expanded_inst, success = expand_compressed(inst16)
                if not success:
                    if self.logger is not None:
                        self.logger.warning(f"Invalid compressed instruction at PC={self.pc:08X}: 0x{inst16:04X}")
                    self.trap(cause=2, mtval=inst16)  # illegal instruction
                    return

                # Decode the expanded 32-bit instruction
                inst = expanded_inst
                inst_size = 2
                opcode = inst & 0x7F
                rd = (inst >> 7) & 0x1F
                funct3 = (inst >> 12) & 0x7
                rs1 = (inst >> 15) & 0x1F
                rs2 = (inst >> 20) & 0x1F
                funct7 = (inst >> 25) & 0x7F

                # Cache the decoded and expanded instruction
                self.decode_cache_compressed[inst16] = (opcode, rd, funct3, rs1, rs2, funct7, expanded_inst)
        else:
            # Standard 32-bit instruction
            try:
                opcode, rd, funct3, rs1, rs2, funct7 = self.decode_cache[inst >> 2]
            except KeyError:
                opcode = inst & 0x7F
                rd = (inst >> 7) & 0x1F
                funct3 = (inst >> 12) & 0x7
                rs1 = (inst >> 15) & 0x1F
                rs2 = (inst >> 20) & 0x1F
                funct7 = (inst >> 25) & 0x7F
                self.decode_cache[inst >> 2] = (opcode, rd, funct3, rs1, rs2, funct7)

            inst_size = 4

        self.next_pc = (self.pc + inst_size) & 0xFFFFFFFF
        self.inst_size = inst_size  # Store for handlers that need it (JAL, JALR)

        if opcode in opcode_handler:
            (opcode_handler[opcode])(self, self.ram, inst, rd, funct3, rs1, rs2, funct7)  # dispatch to opcode handler
        else:
            if self.logger is not None:
                self.logger.warning(f"Invalid instruction at PC={self.pc:08X}: 0x{inst:08X}, opcode=0x{opcode:x}")
            self.trap(cause=2, mtval=inst)  # illegal instruction cause

        self.registers[0] = 0       # x0 is always 0
    
    # Trap handling
    def trap(self, cause, mtval=0, sync=True):
        if self.csrs[0x305] == 0:
            cause_name = self.TRAP_CAUSE_NAMES.get(cause, "Unknown")
            raise ExecutionTerminated(f"Trap at PC={self.pc:08X} without trap handler installed (mcause={cause}: {cause_name}) – execution terminated.")

        # for synchronous traps, MEPC <- PC, for asynchronous ones (e.g., timer) MEPC <- next instruction
        self.csrs[0x341] = self.pc if sync else self.next_pc  # mepc
        self.csrs[0x342] = cause  # mcause
        self.csrs[0x343] = mtval  # mtval

        mstatus = self.csrs[0x300]
        mie = (mstatus >> 3) & 1            # extract MIE
        mstatus &= ~(1 << 3 | 1 << 7)       # clear MIE and MPIE
        mstatus |= (mie << 7)               # MPIE <- MIE
        self.csrs[0x300] = mstatus

        self.next_pc = self.csrs[0x305] & ~0x3  # next PC <- mtvec (clearing the mode bits)
        # we only support direct (non-vectored) mode, so the mode field (bits 0 and 1) of mtvect is ignored

        if self.logger is not None and self.trace_traps: 
            self.logger.debug(f"TRAP at PC={self.pc:08X}: mcause=0x{cause:08X}, mtvec={self.csrs[0x305]:08X}, mtval=0x{mtval:08X}, sync={sync}")

    # Performs the side effects of trap + mret,
    # for those cases when the trap is handled by the emulator
    def bypassed_trap_return(self, cause, mtval=0):
        self.csrs[0x341] = self.pc          # mepc
        self.csrs[0x342] = cause            # mcause
        self.csrs[0x343] = mtval            # mtval
        self.csrs[0x300] |= (1 << 7)        # MPIE = 1
        # (MIE, bit 3, stays unchanged)

    # Machine timer interrupt logic
    def timer_update(self):
        csrs = self.csrs
        mtime = self.mtime

        self.mtime = (mtime + 1) # & 0xFFFFFFFF_FFFFFFFF  # the counter should wrap, but it's unlikely to ever happen ;)
        mtip_asserted = (mtime >= self.mtimecmp)

        # Set interrupt pending flag
        if mtip_asserted != self.mtip:
            if mtip_asserted:
                csrs[0x344] |= (1 << 7)     # set MTIP
            else:
                csrs[0x344] &= ~(1 << 7)    # clear MTIP
            self.mtip = mtip_asserted

        if not mtip_asserted:
            return

        # Trigger Machine Timer Interrupt
        if (csrs[0x300] & (1<<3)) and (csrs[0x304] & (1<<7)):
            self.trap(cause=0x80000007, sync=False)  # fire timer interrupt as an asynchronous trap

    # CPU registers initialization
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
        if self.logger is None:
            return

        self.logger.info("REGISTER STATE:")

        self.logger.info(f"{'pc':<12}        {self.pc:08X} ({self.pc})")
        for i, name in enumerate(self.REG_NAMES):
            value = self.registers[i]
            self.logger.info(f"{name:<12} (x{i:02}): {value:08X} ({value})")

        for name, addr in self.CSR_NAME_ADDR.items():
            value = self.csrs[addr]
            self.logger.info(f"{name:<12} ({addr:03X}): {value:08X} ({value})")

        self.logger.info(f"{'mtime_lo':<18}: {self.mtime & 0xFFFFFFFF:08X} ({self.mtime & 0xFFFFFFFF})")
        self.logger.info(f"{'mtime_hi':<18}: {self.mtime >> 32:08X} ({self.mtime >> 32})")
        self.logger.info(f"{'mtimecmp_lo':<18}: {self.mtimecmp & 0xFFFFFFFF:08X} ({self.mtimecmp & 0xFFFFFFFF})")
        self.logger.info(f"{'mtimecmp_hi':<18}: {self.mtimecmp >> 32:08X} ({self.mtimecmp >> 32})")
