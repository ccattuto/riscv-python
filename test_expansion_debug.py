#!/usr/bin/env python3
"""
Test to verify C.LUI expansion for instruction 0x7405
"""

# Test the expansion logic directly
c_inst = 0x7405
print(f"Testing C.LUI expansion for c_inst = 0x{c_inst:04X}")
print(f"Binary: {bin(c_inst)}")

# Extract fields
quadrant = c_inst & 0x3
funct3 = (c_inst >> 13) & 0x7
rd = (c_inst >> 7) & 0x1F

print(f"\nDecoded fields:")
print(f"  Quadrant: {quadrant}")
print(f"  funct3: {funct3}")
print(f"  rd: {rd} (register x{rd}, which is s0)")

# C.LUI expansion logic (current code in cpu.py)
nzimm = ((c_inst >> 7) & 0x20) | ((c_inst >> 2) & 0x1F)
print(f"\nC.LUI expansion:")
print(f"  nzimm (raw): {nzimm} = 0x{nzimm:02X} = {bin(nzimm)}")

if nzimm & 0x20:
    nzimm -= 0x40
    print(f"  nzimm (sign-extended): {nzimm}")

# Current fix: mask to 20 bits
imm_20bit = nzimm & 0xFFFFF
print(f"  imm_20bit: 0x{imm_20bit:05X}")
print(f"  imm_20bit (decimal): {imm_20bit}")
print(f"  imm_20bit (binary): {bin(imm_20bit)}")

# Build expanded instruction
expanded = (imm_20bit << 12) | (rd << 7) | 0x37
print(f"\nExpanded instruction:")
print(f"  expanded: 0x{expanded:08X}")
print(f"  expanded (binary): {bin(expanded)}")

# Simulate LUI execution
imm_u = expanded >> 12
result = (imm_u << 12) & 0xFFFFFFFF
print(f"\nSimulated LUI execution:")
print(f"  imm_u (from expanded): 0x{imm_u:05X}")
print(f"  result (imm_u << 12): 0x{result:08X}")
print(f"  Expected result: 0xFFFE1000")
print(f"  Match: {result == 0xFFFE1000}")

# What if we didn't have the mask fix?
print(f"\n--- Testing WITHOUT mask (old buggy code) ---")
nzimm_buggy = ((c_inst >> 7) & 0x20) | ((c_inst >> 2) & 0x1F)
if nzimm_buggy & 0x20:
    nzimm_buggy -= 0x40
print(f"  nzimm (sign-extended): {nzimm_buggy}")

# Old code: directly shift negative number
expanded_buggy = (nzimm_buggy << 12) | (rd << 7) | 0x37
print(f"  expanded (direct shift): {expanded_buggy}")
print(f"  expanded (hex): 0x{expanded_buggy & 0xFFFFFFFF:08X}")
print(f"  Is negative?: {expanded_buggy < 0}")

if expanded_buggy < 0:
    # Try to see what happens when a negative expanded instruction is used
    imm_u_buggy = expanded_buggy >> 12
    result_buggy = (imm_u_buggy << 12) & 0xFFFFFFFF
    print(f"  imm_u (from negative expanded): {imm_u_buggy}")
    print(f"  result: 0x{result_buggy:08X}")
