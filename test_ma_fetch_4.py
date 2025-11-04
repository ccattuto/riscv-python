#!/usr/bin/env python3
"""
Test for ma_fetch test #4: JALR with misaligned target (RVC enabled)

Test logic:
1. jalr t1, t0, 3  -> target = (t0 + 3) & ~1 = t0 + 2
2. At t0+0: c.j forward (2 bytes)
3. At t0+2: c.j to_success (2 bytes) <- TARGET
4. Should execute c.j at t0+2 and jump to success

Expected: t1 should be 0 (not written because trap handler clears it)
Or: t1 should be return address if no trap occurs
"""

from cpu import CPU
from ram import SafeRAMOffset

# Create CPU and RAM
ram = SafeRAMOffset(64*1024, base_addr=0x8000_0000)
cpu = CPU(ram)

print("Testing ma_fetch test #4: JALR to 2-byte aligned address")
print("=" * 70)

# Set up the test scenario:
# 0x80000000: jalr t1, t0, 3
# 0x80000004: c.j +6 (jump forward 6 bytes to 0x8000000A)
# 0x80000006: c.j +8 (jump forward 8 bytes to 0x8000000E) <- TARGET at t0+2
# 0x80000008: (would be part of fail path)
# 0x8000000A: j fail (4-byte instruction)
# 0x8000000E: (success - continue)

# Write jalr instruction: jalr t1, t0, 3 (0x003282E7)
# Format: imm[11:0]=3, rs1=5(t0), funct3=0, rd=6(t1), opcode=0x67(JALR)
jalr_inst = (3 << 20) | (5 << 15) | (0 << 12) | (6 << 7) | 0x67
ram.store_word(0x8000_0000, jalr_inst)

# Write C.J instructions with correct encodings
# C.J offset +4 encodes as 0xA011 (not 0xA001 which is offset=0)
#
# offset=+4: bits [3:1]=010, bit[4]=0
# inst[5:3] = offset[3:1] = 010
# inst[11] = offset[4] = 0
# Result: 0xA011

# C.J offset=+4 at 0x80000004 (skip to 0x80000008)
ram.store_half(0x8000_0004, 0xa011)  # c.j +4

# C.J offset=+4 at 0x80000006 (TARGET - jump to 0x8000000A)
ram.store_half(0x8000_0006, 0xa011)  # c.j +4

# At 0x80000008: c.j +4 (would skip to 0x8000000C if executed)
ram.store_half(0x8000_0008, 0xa011)  # c.j +4

# Success marker at 0x8000000A: c.nop
ram.store_half(0x8000_000A, 0x0001)  # c.nop

print("\nTest setup:")
print(f"  0x80000000: jalr t1, t0, 3 (0x{jalr_inst:08X})")
print(f"  0x80000004: c.j +4 (0xa011)")
print(f"  0x80000006: c.j +4 (0xa011) <- TARGET (t0 + 2)")
print(f"  0x80000008: c.j +4 (0xa011)")
print(f"  0x8000000A: c.nop (0x0001) <- SUCCESS")

# Set up registers
cpu.registers[5] = 0x8000_0004  # t0 = address of first c.j
cpu.registers[6] = 0xDEADBEEF   # t1 = sentinel (should not be written if trap occurs)

cpu.pc = 0x8000_0000
cpu.next_pc = 0x8000_0000

print(f"\nBefore JALR:")
print(f"  t0 (x5) = 0x{cpu.registers[5]:08X}")
print(f"  t1 (x6) = 0x{cpu.registers[6]:08X}")
print(f"  PC = 0x{cpu.pc:08X}")

# Execute jalr instruction
inst = ram.load_word(cpu.pc)
cpu.execute(inst)

print(f"\nAfter JALR:")
print(f"  t0 (x5) = 0x{cpu.registers[5]:08X}")
print(f"  t1 (x6) = 0x{cpu.registers[6]:08X}")
print(f"  PC = 0x{cpu.next_pc:08X}")

# Calculate expected values
# jalr t1, t0, 3 -> target = (t0 + 3) & ~1 = (0x80000004 + 3) & ~1 = 0x80000006
expected_target = (cpu.registers[5] + 3) & 0xFFFFFFFE
expected_return = 0x8000_0004  # PC + 4 (jalr is 4-byte instruction)

print(f"\nExpected:")
print(f"  Target address: 0x{expected_target:08X} (t0+3 with LSB cleared)")
print(f"  t1 (return addr): 0x{expected_return:08X}")
print(f"  PC should jump to: 0x{expected_target:08X}")

# Verify
success = True
if cpu.next_pc != expected_target:
    print(f"\n✗ FAIL: PC mismatch")
    print(f"  Expected: 0x{expected_target:08X}")
    print(f"  Got: 0x{cpu.next_pc:08X}")
    success = False

if cpu.registers[6] != expected_return:
    print(f"\n✗ FAIL: Return address mismatch")
    print(f"  Expected: 0x{expected_return:08X}")
    print(f"  Got: 0x{cpu.registers[6]:08X}")
    success = False

# Now execute the instruction at the target (c.j at 0x80000006)
if success:
    cpu.pc = cpu.next_pc
    inst2 = ram.load_half(cpu.pc, signed=False)
    print(f"\nExecuting instruction at target: 0x{inst2:04X} (c.j)")
    cpu.execute(inst2)
    print(f"After c.j: PC = 0x{cpu.next_pc:08X}")

    # Should jump to 0x8000000A
    if cpu.next_pc == 0x8000_000A:
        print("\n✓ TEST PASSED: Correctly executed 2-byte aligned jump")
    else:
        print(f"\n✗ TEST FAILED: c.j didn't jump to expected location")
        print(f"  Expected: 0x8000000A")
        print(f"  Got: 0x{cpu.next_pc:08X}")
