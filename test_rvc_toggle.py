#!/usr/bin/env python3
"""Test toggling RVC extension on/off"""

from cpu import CPU
from ram import RAM

def test_rvc_toggle():
    """Test that misa.C bit can be toggled and affects alignment checks"""
    print("Testing RVC Extension Toggle")
    print("=" * 60)

    ram = RAM(1024)
    cpu = CPU(ram)

    # Initially C extension is enabled
    print(f"Initial misa: 0x{cpu.csrs[0x301]:08X}")
    print(f"  C bit (bit 2): {(cpu.csrs[0x301] >> 2) & 1}")
    print(f"  is_rvc_enabled(): {cpu.is_rvc_enabled()}")
    assert cpu.is_rvc_enabled(), "C extension should be enabled initially"

    # Test 1: JALR to 2-byte aligned address (t0+2) with C enabled
    print("\nTest 1: JALR to 2-byte aligned address with C enabled")
    cpu.registers[5] = 0x100  # t0
    cpu.registers[6] = 0      # t1
    cpu.pc = 0x00

    # JALR t1, t0, 2
    jalr_inst = (2 << 20) | (5 << 15) | (0 << 12) | (6 << 7) | 0x67
    cpu.execute(jalr_inst)
    print(f"  Target: 0x{0x102:08X} (2-byte aligned)")
    print(f"  next_pc: 0x{cpu.next_pc:08X}")
    print(f"  Expected: No trap, next_pc = 0x{0x102:08X}")
    assert cpu.next_pc == 0x102, "Should jump to 0x102 (2-byte aligned is OK with C)"
    print("  ✓ PASSED")

    # Test 2: Disable C extension
    print("\nTest 2: Disabling C extension")
    # CSRCI misa, 0x4 (clear bit 2)
    cpu.csrs[0x301] &= ~0x4
    cpu.rvc_enabled = (cpu.csrs[0x301] & 0x4) != 0  # Update cache
    print(f"  misa after clear: 0x{cpu.csrs[0x301]:08X}")
    print(f"  C bit (bit 2): {(cpu.csrs[0x301] >> 2) & 1}")
    print(f"  is_rvc_enabled(): {cpu.is_rvc_enabled()}")
    assert not cpu.is_rvc_enabled(), "C extension should be disabled"
    print("  ✓ C extension disabled successfully")

    # Test 3: JALR to 2-byte aligned address (t0+2) with C disabled - should trap
    print("\nTest 3: JALR to 2-byte aligned address with C disabled")
    cpu.registers[5] = 0x100  # t0
    cpu.registers[6] = 0      # t1
    cpu.pc = 0x200
    cpu.next_pc = cpu.pc + 4
    cpu.csrs[0x305] = 0x1000  # Set trap handler address

    # JALR t1, t0, 2
    jalr_inst = (2 << 20) | (5 << 15) | (0 << 12) | (6 << 7) | 0x67
    cpu.execute(jalr_inst)
    print(f"  Target: 0x{0x102:08X} (2-byte aligned, NOT 4-byte aligned)")
    print(f"  next_pc: 0x{cpu.next_pc:08X}")
    print(f"  mepc: 0x{cpu.csrs[0x341]:08X}")
    print(f"  mcause: 0x{cpu.csrs[0x342]:08X}")
    print(f"  mtval: 0x{cpu.csrs[0x343]:08X}")

    # Should trap: mcause=0 (misaligned fetch), mepc=pc of JALR
    assert cpu.csrs[0x342] == 0, f"mcause should be 0 (misaligned), got {cpu.csrs[0x342]}"
    assert cpu.csrs[0x341] == 0x200, f"mepc should be 0x200, got 0x{cpu.csrs[0x341]:08X}"
    assert cpu.csrs[0x343] == 0x102, f"mtval should be 0x102, got 0x{cpu.csrs[0x343]:08X}"
    assert cpu.next_pc == 0x1000, f"Should trap to handler at 0x1000, got 0x{cpu.next_pc:08X}"
    print("  ✓ PASSED - Trapped as expected")

    # Test 4: Re-enable C extension
    print("\nTest 4: Re-enabling C extension")
    cpu.csrs[0x301] |= 0x4
    cpu.rvc_enabled = (cpu.csrs[0x301] & 0x4) != 0  # Update cache
    print(f"  misa after set: 0x{cpu.csrs[0x301]:08X}")
    print(f"  C bit (bit 2): {(cpu.csrs[0x301] >> 2) & 1}")
    print(f"  is_rvc_enabled(): {cpu.is_rvc_enabled()}")
    assert cpu.is_rvc_enabled(), "C extension should be enabled again"
    print("  ✓ C extension re-enabled successfully")

    # Test 5: JALR to 2-byte aligned address with C re-enabled - should NOT trap
    print("\nTest 5: JALR to 2-byte aligned address with C re-enabled")
    cpu.registers[5] = 0x100  # t0
    cpu.registers[6] = 0      # t1
    cpu.pc = 0x300

    # JALR t1, t0, 2
    jalr_inst = (2 << 20) | (5 << 15) | (0 << 12) | (6 << 7) | 0x67
    cpu.execute(jalr_inst)
    print(f"  Target: 0x{0x102:08X} (2-byte aligned)")
    print(f"  next_pc: 0x{cpu.next_pc:08X}")
    assert cpu.next_pc == 0x102, "Should jump to 0x102 (2-byte aligned is OK with C)"
    print("  ✓ PASSED - No trap, as expected")

    print("\n" + "=" * 60)
    print("All RVC toggle tests PASSED! ✓")
    return True

if __name__ == "__main__":
    test_rvc_toggle()
