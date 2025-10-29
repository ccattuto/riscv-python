#!/usr/bin/env python3
"""
Test C.JALR return address calculation
"""

from cpu import CPU
from ram import SafeRAMOffset

# Create CPU and RAM
ram = SafeRAMOffset(1024, base_addr=0x8000_0000)
cpu = CPU(ram)

print("Testing C.JALR return address calculation")
print("=" * 60)

# Write test code:
# 0x80000000: c.jalr t0  (0x9282)
# 0x80000002: c.nop      (0x0001)
# Target at 0x80000010

ram.store_half(0x8000_0000, 0x9282)  # c.jalr t0 (jalr x1, 0(x5))
ram.store_half(0x8000_0002, 0x0001)  # c.nop

# Set t0 to target address
cpu.registers[5] = 0x8000_0010  # t0 = target
cpu.registers[1] = 0xDEADBEEF   # ra = sentinel

cpu.pc = 0x8000_0000
cpu.next_pc = 0x8000_0000

# Execute c.jalr
inst = ram.load_half(cpu.pc, signed=False)
print(f"\nInstruction at 0x{cpu.pc:08X}: 0x{inst:04X} (c.jalr t0)")
print(f"Before: ra (x1) = 0x{cpu.registers[1]:08X}")
print(f"Before: t0 (x5) = 0x{cpu.registers[5]:08X}")

cpu.execute(inst)

print(f"\nAfter:  ra (x1) = 0x{cpu.registers[1]:08X}")
print(f"After:  PC = 0x{cpu.next_pc:08X}")

expected_ra = 0x8000_0002  # PC + 2 (compressed instruction)
expected_pc = 0x8000_0010  # Target from t0

print(f"\nExpected ra: 0x{expected_ra:08X}")
print(f"Expected PC: 0x{expected_pc:08X}")

if cpu.registers[1] == expected_ra and cpu.next_pc == expected_pc:
    print("\n✓ TEST PASSED")
else:
    print("\n✗ TEST FAILED")
    if cpu.registers[1] != expected_ra:
        print(f"  ra mismatch: got 0x{cpu.registers[1]:08X}, expected 0x{expected_ra:08X}")
    if cpu.next_pc != expected_pc:
        print(f"  PC mismatch: got 0x{cpu.next_pc:08X}, expected 0x{expected_pc:08X}")

# Also test regular (non-compressed) JALR for comparison
print("\n" + "=" * 60)
print("Testing regular JALR return address calculation")
print("=" * 60)

cpu2 = CPU(ram)
ram.store_word(0x8000_0020, 0x000280E7)  # jalr x1, 0(x5)
cpu2.registers[5] = 0x8000_0030  # t0 = target
cpu2.registers[1] = 0xDEADBEEF   # ra = sentinel
cpu2.pc = 0x8000_0020
cpu2.next_pc = 0x8000_0020

inst2 = ram.load_word(cpu2.pc)
print(f"\nInstruction at 0x{cpu2.pc:08X}: 0x{inst2:08X} (jalr x1, 0(t0))")
print(f"Before: ra (x1) = 0x{cpu2.registers[1]:08X}")

cpu2.execute(inst2)

expected_ra2 = 0x8000_0024  # PC + 4 (normal instruction)
expected_pc2 = 0x8000_0030  # Target from t0

print(f"After:  ra (x1) = 0x{cpu2.registers[1]:08X}")
print(f"After:  PC = 0x{cpu2.next_pc:08X}")
print(f"\nExpected ra: 0x{expected_ra2:08X}")
print(f"Expected PC: 0x{expected_pc2:08X}")

if cpu2.registers[1] == expected_ra2 and cpu2.next_pc == expected_pc2:
    print("\n✓ TEST PASSED")
else:
    print("\n✗ TEST FAILED")
