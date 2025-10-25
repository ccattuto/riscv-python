#!/usr/bin/env python3
"""
Comprehensive test of all compressed instruction expansions
"""

from cpu import expand_compressed

tests_passed = 0
tests_failed = 0

def test_expansion(name, c_inst, expected_inst):
    global tests_passed, tests_failed
    expanded, success = expand_compressed(c_inst)
    if not success:
        print(f"✗ {name}: expansion failed")
        tests_failed += 1
        return
    if expanded == expected_inst:
        print(f"✓ {name}: 0x{c_inst:04X} → 0x{expanded:08X}")
        tests_passed += 1
    else:
        print(f"✗ {name}: 0x{c_inst:04X} → 0x{expanded:08X} (expected 0x{expected_inst:08X})")
        tests_failed += 1

print("Testing ALL Compressed Instructions")
print("=" * 70)

# Quadrant 0 (C0)
print("\n### Quadrant 0 (C0) ###")

# C.ADDI4SPN a0, sp, 1020
# nzuimm=1020=0x3FC
test_expansion("C.ADDI4SPN a0, sp, 1020", 0x1FFC,
               (1020 << 20) | (2 << 15) | (0 << 12) | (10 << 7) | 0x13)

# C.LW a0, 0(a1)
test_expansion("C.LW a0, 0(a1)", 0x4188,
               (0 << 20) | (11 << 15) | (0x2 << 12) | (10 << 7) | 0x03)

# C.SW a0, 0(a1)
test_expansion("C.SW a0, 0(a1)", 0xC188,
               (0 << 25) | (10 << 20) | (11 << 15) | (0x2 << 12) | (0 << 7) | 0x23)

# Quadrant 1 (C1)
print("\n### Quadrant 1 (C1) ###")

# C.NOP
test_expansion("C.NOP", 0x0001,
               (0 << 20) | (0 << 15) | (0 << 12) | (0 << 7) | 0x13)

# C.ADDI a0, -16
test_expansion("C.ADDI a0, -16", 0x1541,
               (0xFF0 << 20) | (10 << 15) | (0 << 12) | (10 << 7) | 0x13)

# C.JAL offset=0 (RV32 only)
test_expansion("C.JAL offset=0", 0x2001,
               0x000000EF)

# C.LI a5, -16
test_expansion("C.LI a5, -16", 0x57C1,
               (0xFF0 << 20) | (0 << 15) | (0 << 12) | (15 << 7) | 0x13)

# C.LUI s0, 0xfffe1
# nzimm=-31 (0xFFE1 sign-extended from 6 bits)
test_expansion("C.LUI s0, 0x1", 0x6405,
               (1 << 12) | (8 << 7) | 0x37)

# C.ADDI16SP sp, 496
# nzimm=496=0x1F0
test_expansion("C.ADDI16SP sp, 496", 0x617C,
               (496 << 20) | (2 << 15) | (0 << 12) | (2 << 7) | 0x13)

# C.SRLI s0, 12
test_expansion("C.SRLI a0, 1", 0x8105,
               (0x00 << 25) | (1 << 20) | (10 << 15) | (0x5 << 12) | (10 << 7) | 0x13)

# C.SRAI s0, 12
test_expansion("C.SRAI a0, 1", 0x8505,
               (0x20 << 25) | (1 << 20) | (10 << 15) | (0x5 << 12) | (10 << 7) | 0x13)

# C.ANDI s0, ~0x10
test_expansion("C.ANDI a0, -1", 0x8DFD,
               (0xFFF << 20) | (10 << 15) | (0x7 << 12) | (10 << 7) | 0x13)

# C.SUB s1, a0
test_expansion("C.SUB s1, a0", 0x8C89,
               (0x20 << 25) | (10 << 20) | (9 << 15) | (0x0 << 12) | (9 << 7) | 0x33)

# C.XOR s1, a0
test_expansion("C.XOR s1, a0", 0x8CA9,
               (0x00 << 25) | (10 << 20) | (9 << 15) | (0x4 << 12) | (9 << 7) | 0x33)

# C.OR s1, a0
test_expansion("C.OR s1, a0", 0x8CC9,
               (0x00 << 25) | (10 << 20) | (9 << 15) | (0x6 << 12) | (9 << 7) | 0x33)

# C.AND s1, a0
test_expansion("C.AND s1, a0", 0x8CE9,
               (0x00 << 25) | (10 << 20) | (9 << 15) | (0x7 << 12) | (9 << 7) | 0x33)

# C.J offset=0
test_expansion("C.J offset=0", 0xA001,
               0x0000006F)

# C.BEQZ a0, offset=0
test_expansion("C.BEQZ a0, offset=0", 0xC101,
               (0 << 20) | (10 << 15) | (0x0 << 12) | 0x63)

# C.BNEZ a0, offset=0
test_expansion("C.BNEZ a0, offset=0", 0xE101,
               (0 << 20) | (10 << 15) | (0x1 << 12) | 0x63)

# Quadrant 2 (C2)
print("\n### Quadrant 2 (C2) ###")

# C.SLLI s0, 4
test_expansion("C.SLLI s0, 4", 0x0412,
               (0x00 << 25) | (4 << 20) | (8 << 15) | (0x1 << 12) | (8 << 7) | 0x13)

# C.LWSP a2, offset=0
test_expansion("C.LWSP a2, offset=0", 0x4602,
               (0 << 20) | (2 << 15) | (0x2 << 12) | (12 << 7) | 0x03)

# C.JR t0
test_expansion("C.JR t0", 0x8282,
               (0 << 20) | (5 << 15) | (0 << 12) | (0 << 7) | 0x67)

# C.MV t0, a0
test_expansion("C.MV t0, a0", 0x82AA,
               (0x00 << 25) | (10 << 20) | (0 << 15) | (0x0 << 12) | (5 << 7) | 0x33)

# C.EBREAK
test_expansion("C.EBREAK", 0x9002,
               0x00100073)

# C.JALR t0
test_expansion("C.JALR t0", 0x9282,
               (0 << 20) | (5 << 15) | (0 << 12) | (1 << 7) | 0x67)

# C.ADD t0, a0
test_expansion("C.ADD t0, a0", 0x92AA,
               (0x00 << 25) | (10 << 20) | (5 << 15) | (0x0 << 12) | (5 << 7) | 0x33)

# C.SWSP a0, offset=0
test_expansion("C.SWSP a0, offset=0", 0xC02A,
               (0 << 25) | (10 << 20) | (2 << 15) | (0x2 << 12) | (0 << 7) | 0x23)

print("\n" + "=" * 70)
print(f"Results: {tests_passed} passed, {tests_failed} failed")
if tests_failed == 0:
    print("✓ All compressed instruction expansions are correct!")
else:
    print(f"✗ {tests_failed} expansions failed!")
