#!/usr/bin/env python3
"""
Test specific compressed instructions that might be failing
"""

from cpu import CPU, expand_compressed
from ram import RAM

print("Testing Compressed Instruction Expansion")
print("=" * 60)

# Test C.JAL immediate encoding
print("\nTest: C.JAL immediate encoding")
# C.JAL with offset +4 (jump forward 4 bytes)
# Format: 001 imm[11|4|9:8|10|6|7|3:1|5] 01
# For offset +4: imm = 0x004 = 0000 0000 0100
# Bits: [11|4|9:8|10|6|7|3:1|5] = [0|0|00|0|0|0|010|0]
# Let me construct this carefully...

# Actually, let's test with a simple known value
# C.JAL offset=0 (should be a simple case)
c_inst_jal = 0x2001  # C.JAL with imm=0
expanded, success = expand_compressed(c_inst_jal)
print(f"  C.JAL (0x{c_inst_jal:04X}) -> 0x{expanded:08X}, success={success}")

# The expanded should be JAL x1, 0
# JAL format: imm[20|10:1|11|19:12] rd opcode
# JAL x1, 0: should be 0x000000EF
expected_jal = 0x000000EF
if expanded == expected_jal:
    print(f"  ✓ Correct expansion")
else:
    print(f"  ✗ WRONG! Expected 0x{expected_jal:08X}, got 0x{expanded:08X}")

# Test C.LI
print("\nTest: C.LI rd=x10, imm=5")
c_inst_li = 0x4515  # C.LI a0, 5
expanded, success = expand_compressed(c_inst_li)
print(f"  C.LI (0x{c_inst_li:04X}) -> 0x{expanded:08X}, success={success}")
# Should expand to: ADDI x10, x0, 5
# Format: imm[11:0] rs1[4:0] 000 rd[4:0] 0010011
# imm=5=0x005, rs1=0, rd=10
expected_addi = (5 << 20) | (0 << 15) | (0 << 12) | (10 << 7) | 0x13
print(f"  Expected: 0x{expected_addi:08X}")
if expanded == expected_addi:
    print(f"  ✓ Correct")
else:
    print(f"  ✗ WRONG!")

# Test C.LWSP
print("\nTest: C.LWSP rd=x10, offset=0")
c_inst_lwsp = 0x4502  # C.LWSP a0, 0
expanded, success = expand_compressed(c_inst_lwsp)
print(f"  C.LWSP (0x{c_inst_lwsp:04X}) -> 0x{expanded:08X}, success={success}")
# Should expand to: LW x10, 0(x2)
# Format: imm[11:0] rs1[4:0] 010 rd[4:0] 0000011
expected_lw = (0 << 20) | (2 << 15) | (0x2 << 12) | (10 << 7) | 0x03
print(f"  Expected: 0x{expected_lw:08X}")
if expanded == expected_lw:
    print(f"  ✓ Correct")
else:
    print(f"  ✗ WRONG!")

# Test illegal compressed instruction (all zeros except quadrant)
print("\nTest: Illegal compressed instruction")
c_inst_illegal = 0x0000  # All zeros is illegal for C.ADDI4SPN
expanded, success = expand_compressed(c_inst_illegal)
print(f"  Illegal (0x{c_inst_illegal:04X}) -> success={success}")
if not success:
    print(f"  ✓ Correctly detected as illegal")
else:
    print(f"  ✗ WRONG! Should be illegal")

print("\n" + "=" * 60)
print("Expansion tests complete")
