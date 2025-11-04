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

"""
RISC-V Compressed (RVC) Instruction Extension

This module provides support for the RVC extension, which allows 16-bit
compressed instructions to be mixed with standard 32-bit instructions,
improving code density by approximately 25-30%.

The expand_compressed() function takes a 16-bit compressed instruction
and returns its 32-bit equivalent, ready for execution by the CPU.
"""

def expand_compressed(c_inst):
    """
    Expand a 16-bit compressed instruction to its 32-bit equivalent.

    Args:
        c_inst: 16-bit compressed instruction

    Returns:
        (expanded_32bit_inst, success_flag) tuple
        - expanded_32bit_inst: The 32-bit equivalent instruction
        - success_flag: True if expansion succeeded, False for illegal instruction

    Supports all RV32C instructions across three quadrants:
    - Quadrant 0 (C0): Stack/memory operations
    - Quadrant 1 (C1): Arithmetic & control flow
    - Quadrant 2 (C2): Register operations
    """
    quadrant = c_inst & 0x3
    funct3 = (c_inst >> 13) & 0x7

    # Quadrant 0 (C0)
    if quadrant == 0b00:
        if funct3 == 0b000:  # C.ADDI4SPN
            nzuimm = ((c_inst >> 7) & 0x30) | ((c_inst >> 1) & 0x3C0) | ((c_inst >> 4) & 0x4) | ((c_inst >> 2) & 0x8)
            rd_prime = ((c_inst >> 2) & 0x7) + 8
            if nzuimm == 0:
                return (0, False)  # Illegal instruction
            # ADDI rd', x2, nzuimm
            return ((nzuimm << 20) | (2 << 15) | (0 << 12) | (rd_prime << 7) | 0x13, True)

        elif funct3 == 0b010:  # C.LW
            imm = ((c_inst >> 7) & 0x38) | ((c_inst >> 4) & 0x4) | ((c_inst << 6) & 0x40)
            rs1_prime = ((c_inst >> 7) & 0x7) + 8
            rd_prime = ((c_inst >> 2) & 0x7) + 8
            # LW rd', imm(rs1')
            return ((imm << 20) | (rs1_prime << 15) | (0x2 << 12) | (rd_prime << 7) | 0x03, True)

        elif funct3 == 0b110:  # C.SW
            imm = ((c_inst >> 7) & 0x38) | ((c_inst >> 4) & 0x4) | ((c_inst << 6) & 0x40)
            rs1_prime = ((c_inst >> 7) & 0x7) + 8
            rs2_prime = ((c_inst >> 2) & 0x7) + 8
            imm_low = imm & 0x1F
            imm_high = (imm >> 5) & 0x7F
            # SW rs2', imm(rs1')
            return ((imm_high << 25) | (rs2_prime << 20) | (rs1_prime << 15) | (0x2 << 12) | (imm_low << 7) | 0x23, True)

    # Quadrant 1 (C1)
    elif quadrant == 0b01:
        if funct3 == 0b000:  # C.NOP / C.ADDI
            nzimm = ((c_inst >> 7) & 0x20) | ((c_inst >> 2) & 0x1F)
            if nzimm & 0x20: nzimm -= 0x40  # sign extend
            rd_rs1 = (c_inst >> 7) & 0x1F
            # ADDI rd, rd, nzimm (if rd=0, it's NOP)
            imm = nzimm & 0xFFF
            return ((imm << 20) | (rd_rs1 << 15) | (0 << 12) | (rd_rs1 << 7) | 0x13, True)

        elif funct3 == 0b001:  # C.JAL (RV32 only)
            imm = ((c_inst >> 1) & 0x800) | ((c_inst << 2) & 0x400) | ((c_inst >> 1) & 0x300) | \
                  ((c_inst << 1) & 0x80) | ((c_inst >> 1) & 0x40) | ((c_inst << 3) & 0x20) | \
                  ((c_inst >> 7) & 0x10) | ((c_inst >> 2) & 0xE)
            if imm & 0x800: imm -= 0x1000  # sign extend to 12 bits
            imm = imm & 0xFFFFF  # 20-bit immediate for JAL
            # JAL x1, imm
            imm_bits = ((imm & 0x100000) << 11) | ((imm & 0x7FE) << 20) | ((imm & 0x800) << 9) | (imm & 0xFF000)
            return (imm_bits | (1 << 7) | 0x6F, True)

        elif funct3 == 0b010:  # C.LI
            imm = ((c_inst >> 7) & 0x20) | ((c_inst >> 2) & 0x1F)
            if imm & 0x20: imm -= 0x40  # sign extend
            rd = (c_inst >> 7) & 0x1F
            # ADDI rd, x0, imm
            imm = imm & 0xFFF
            return ((imm << 20) | (0 << 15) | (0 << 12) | (rd << 7) | 0x13, True)

        elif funct3 == 0b011:  # C.ADDI16SP / C.LUI
            rd = (c_inst >> 7) & 0x1F
            if rd == 2:  # C.ADDI16SP
                nzimm = ((c_inst >> 3) & 0x200) | ((c_inst >> 2) & 0x10) | \
                        ((c_inst << 1) & 0x40) | ((c_inst << 4) & 0x180) | ((c_inst << 3) & 0x20)
                if nzimm & 0x200: nzimm -= 0x400  # sign extend
                if nzimm == 0:
                    return (0, False)  # Illegal
                # ADDI x2, x2, nzimm
                imm = nzimm & 0xFFF
                return ((imm << 20) | (2 << 15) | (0 << 12) | (2 << 7) | 0x13, True)
            else:  # C.LUI
                nzimm = ((c_inst >> 7) & 0x20) | ((c_inst >> 2) & 0x1F)
                if nzimm & 0x20: nzimm -= 0x40  # sign extend
                if nzimm == 0 or rd == 0:
                    return (0, False)  # Illegal
                # LUI rd, nzimm
                # Need to mask to 32 bits because nzimm can be negative after sign extension
                imm_20bit = nzimm & 0xFFFFF  # Mask to 20 bits
                expanded = (imm_20bit << 12) | (rd << 7) | 0x37
                return (expanded, True)

        elif funct3 == 0b100:  # Arithmetic operations
            funct2 = (c_inst >> 10) & 0x3
            rd_rs1_prime = ((c_inst >> 7) & 0x7) + 8

            if funct2 == 0b00:  # C.SRLI
                shamt = ((c_inst >> 7) & 0x20) | ((c_inst >> 2) & 0x1F)
                if shamt == 0:
                    return (0, False)  # RV32 NSE
                # SRLI rd', rd', shamt
                return ((0x00 << 25) | (shamt << 20) | (rd_rs1_prime << 15) | (0x5 << 12) | (rd_rs1_prime << 7) | 0x13, True)

            elif funct2 == 0b01:  # C.SRAI
                shamt = ((c_inst >> 7) & 0x20) | ((c_inst >> 2) & 0x1F)
                if shamt == 0:
                    return (0, False)  # RV32 NSE
                # SRAI rd', rd', shamt
                return ((0x20 << 25) | (shamt << 20) | (rd_rs1_prime << 15) | (0x5 << 12) | (rd_rs1_prime << 7) | 0x13, True)

            elif funct2 == 0b10:  # C.ANDI
                imm = ((c_inst >> 7) & 0x20) | ((c_inst >> 2) & 0x1F)
                if imm & 0x20: imm -= 0x40  # sign extend
                # ANDI rd', rd', imm
                imm = imm & 0xFFF
                return ((imm << 20) | (rd_rs1_prime << 15) | (0x7 << 12) | (rd_rs1_prime << 7) | 0x13, True)

            elif funct2 == 0b11:  # Register-register operations
                funct2_low = (c_inst >> 5) & 0x3
                rs2_prime = ((c_inst >> 2) & 0x7) + 8
                bit12 = (c_inst >> 12) & 0x1

                if bit12 == 0:
                    if funct2_low == 0b00:  # C.SUB
                        return ((0x20 << 25) | (rs2_prime << 20) | (rd_rs1_prime << 15) | (0x0 << 12) | (rd_rs1_prime << 7) | 0x33, True)
                    elif funct2_low == 0b01:  # C.XOR
                        return ((0x00 << 25) | (rs2_prime << 20) | (rd_rs1_prime << 15) | (0x4 << 12) | (rd_rs1_prime << 7) | 0x33, True)
                    elif funct2_low == 0b10:  # C.OR
                        return ((0x00 << 25) | (rs2_prime << 20) | (rd_rs1_prime << 15) | (0x6 << 12) | (rd_rs1_prime << 7) | 0x33, True)
                    elif funct2_low == 0b11:  # C.AND
                        return ((0x00 << 25) | (rs2_prime << 20) | (rd_rs1_prime << 15) | (0x7 << 12) | (rd_rs1_prime << 7) | 0x33, True)

        elif funct3 == 0b101:  # C.J
            imm = ((c_inst >> 1) & 0x800) | ((c_inst << 2) & 0x400) | ((c_inst >> 1) & 0x300) | \
                  ((c_inst << 1) & 0x80) | ((c_inst >> 1) & 0x40) | ((c_inst << 3) & 0x20) | \
                  ((c_inst >> 7) & 0x10) | ((c_inst >> 2) & 0xE)
            if imm & 0x800: imm -= 0x1000  # sign extend
            imm = imm & 0xFFFFF  # 20-bit
            # JAL x0, imm
            imm_bits = ((imm & 0x100000) << 11) | ((imm & 0x7FE) << 20) | ((imm & 0x800) << 9) | (imm & 0xFF000)
            return (imm_bits | (0 << 7) | 0x6F, True)

        elif funct3 == 0b110:  # C.BEQZ
            imm = ((c_inst >> 4) & 0x100) | ((c_inst << 1) & 0xC0) | ((c_inst << 3) & 0x20) | \
                  ((c_inst >> 7) & 0x18) | ((c_inst >> 2) & 0x6)
            if imm & 0x100: imm -= 0x200  # sign extend
            rs1_prime = ((c_inst >> 7) & 0x7) + 8
            # BEQ rs1', x0, imm
            imm_bits = ((imm & 0x1000) << 19) | ((imm & 0x7E0) << 20) | ((imm & 0x1E) << 7) | ((imm & 0x800) >> 4)
            return (imm_bits | (0 << 20) | (rs1_prime << 15) | (0x0 << 12) | 0x63, True)

        elif funct3 == 0b111:  # C.BNEZ
            imm = ((c_inst >> 4) & 0x100) | ((c_inst << 1) & 0xC0) | ((c_inst << 3) & 0x20) | \
                  ((c_inst >> 7) & 0x18) | ((c_inst >> 2) & 0x6)
            if imm & 0x100: imm -= 0x200  # sign extend
            rs1_prime = ((c_inst >> 7) & 0x7) + 8
            # BNE rs1', x0, imm
            imm_bits = ((imm & 0x1000) << 19) | ((imm & 0x7E0) << 20) | ((imm & 0x1E) << 7) | ((imm & 0x800) >> 4)
            return (imm_bits | (0 << 20) | (rs1_prime << 15) | (0x1 << 12) | 0x63, True)

    # Quadrant 2 (C2)
    elif quadrant == 0b10:
        if funct3 == 0b000:  # C.SLLI
            shamt = ((c_inst >> 7) & 0x20) | ((c_inst >> 2) & 0x1F)
            rd_rs1 = (c_inst >> 7) & 0x1F
            if shamt == 0 or rd_rs1 == 0:
                return (0, False)  # Illegal
            # SLLI rd, rd, shamt
            return ((0x00 << 25) | (shamt << 20) | (rd_rs1 << 15) | (0x1 << 12) | (rd_rs1 << 7) | 0x13, True)

        elif funct3 == 0b010:  # C.LWSP
            # Format: offset[5] from bit 12, offset[4:2] from bits 6:4, offset[7:6] from bits 3:2
            offset_5 = (c_inst >> 12) & 0x1
            offset_4_2 = (c_inst >> 4) & 0x7
            offset_7_6 = (c_inst >> 2) & 0x3
            imm = (offset_7_6 << 6) | (offset_5 << 5) | (offset_4_2 << 2)
            rd = (c_inst >> 7) & 0x1F
            if rd == 0:
                return (0, False)  # Illegal
            # LW rd, imm(x2)
            return ((imm << 20) | (2 << 15) | (0x2 << 12) | (rd << 7) | 0x03, True)

        elif funct3 == 0b100:  # C.JR / C.MV / C.EBREAK / C.JALR / C.ADD
            bit12 = (c_inst >> 12) & 0x1
            rs1 = (c_inst >> 7) & 0x1F
            rs2 = (c_inst >> 2) & 0x1F

            if bit12 == 0:
                if rs2 == 0:  # C.JR
                    if rs1 == 0:
                        return (0, False)  # Illegal
                    # JALR x0, 0(rs1)
                    return ((0 << 20) | (rs1 << 15) | (0 << 12) | (0 << 7) | 0x67, True)
                else:  # C.MV
                    if rs1 == 0:
                        return (0, False)  # Illegal
                    # ADD rd, x0, rs2
                    return ((0x00 << 25) | (rs2 << 20) | (0 << 15) | (0x0 << 12) | (rs1 << 7) | 0x33, True)
            else:  # bit12 == 1
                if rs1 == 0 and rs2 == 0:  # C.EBREAK
                    return (0x00100073, True)
                elif rs2 == 0:  # C.JALR
                    # JALR x1, 0(rs1)
                    return ((0 << 20) | (rs1 << 15) | (0 << 12) | (1 << 7) | 0x67, True)
                else:  # C.ADD
                    # ADD rd, rd, rs2
                    return ((0x00 << 25) | (rs2 << 20) | (rs1 << 15) | (0x0 << 12) | (rs1 << 7) | 0x33, True)

        elif funct3 == 0b110:  # C.SWSP
            imm = ((c_inst >> 7) & 0x3C) | ((c_inst >> 1) & 0xC0)
            rs2 = (c_inst >> 2) & 0x1F
            imm_low = imm & 0x1F
            imm_high = (imm >> 5) & 0x7F
            # SW rs2, imm(x2)
            return ((imm_high << 25) | (rs2 << 20) | (2 << 15) | (0x2 << 12) | (imm_low << 7) | 0x23, True)

    # Invalid compressed instruction
    return (0, False)
