#!/usr/bin/env python3
"""
Test C.J instruction expansion
"""

from cpu import expand_compressed

# Test C.J with offset +4
c_inst = 0xA001
print(f"Testing C.J expansion for 0x{c_inst:04X}")
print(f"Binary: {bin(c_inst)}")

quadrant = c_inst & 0x3
funct3 = (c_inst >> 13) & 0x7

print(f"\nQuadrant: {quadrant}")
print(f"Funct3: {funct3}")

# Expand
expanded, success = expand_compressed(c_inst)
print(f"\nExpanded: 0x{expanded:08X}, success={success}")

if success:
    # Decode expanded JAL instruction
    opcode = expanded & 0x7F
    rd = (expanded >> 7) & 0x1F

    # Extract immediate from JAL encoding
    imm_20 = (expanded >> 31) & 0x1
    imm_19_12 = (expanded >> 12) & 0xFF
    imm_11 = (expanded >> 20) & 0x1
    imm_10_1 = (expanded >> 21) & 0x3FF

    # Reconstruct immediate
    imm = (imm_20 << 20) | (imm_19_12 << 12) | (imm_11 << 11) | (imm_10_1 << 1)
    if imm & 0x100000:  # Sign extend
        imm -= 0x200000

    print(f"\nDecoded JAL:")
    print(f"  Opcode: 0x{opcode:02X}")
    print(f"  rd: {rd} (x{rd})")
    print(f"  Immediate: {imm} (0x{imm & 0xFFFFF:X})")
    print(f"  Jump offset: {imm} bytes")

# Test with actual CPU
from cpu import CPU
from ram import SafeRAMOffset

ram = SafeRAMOffset(1024, base_addr=0x8000_0000)
cpu = CPU(ram)

# Write c.j instruction
ram.store_half(0x8000_0000, c_inst)

cpu.pc = 0x8000_0000
cpu.next_pc = 0x8000_0000

print(f"\n--- CPU Execution Test ---")
print(f"Before: PC = 0x{cpu.pc:08X}")

inst = ram.load_half(cpu.pc, signed=False)
cpu.execute(inst)

print(f"After:  PC = 0x{cpu.next_pc:08X}")
print(f"Expected: PC = 0x{0x8000_0000 + imm:08X} (PC + {imm})")

if cpu.next_pc == 0x8000_0000 + imm:
    print("\n✓ C.J executed correctly")
else:
    print(f"\n✗ C.J failed - offset mismatch")
    print(f"  Difference: {cpu.next_pc - 0x8000_0000} bytes")
