#!/usr/bin/env python3
"""Test JALR alignment checking"""

from cpu import CPU
from ram import RAM

def test_jalr_odd_address():
    """
    Test JALR to odd address (like ma_fetch test #4)
    jalr t1, t0, 3 should jump to (t0 + 3)
    After clearing LSB: (t0 + 3) & ~1 = t0 + 2
    """
    print("Testing JALR alignment")
    print("=" * 60)

    ram = RAM(1024)
    cpu = CPU(ram)

    # Set up: t0 (x5) = 0x100, t1 (x6) = 0
    cpu.registers[5] = 0x100
    cpu.registers[6] = 0
    cpu.pc = 0x00

    # JALR t1, t0, 3
    # Format: imm[11:0] rs1[4:0] 000 rd[4:0] 1100111
    # imm = 3, rs1 = 5 (t0), rd = 6 (t1)
    jalr_inst = (3 << 20) | (5 << 15) | (0 << 12) | (6 << 7) | 0x67

    print(f"JALR instruction: 0x{jalr_inst:08X}")
    print(f"  Before: t0=0x{cpu.registers[5]:08X}, t1=0x{cpu.registers[6]:08X}")
    print(f"  Target address: 0x{cpu.registers[5] + 3:08X} (odd)")
    print(f"  After clearing LSB: 0x{(cpu.registers[5] + 3) & 0xFFFFFFFE:08X}")

    try:
        cpu.execute(jalr_inst)
        print(f"  After: next_pc=0x{cpu.next_pc:08X}, t1=0x{cpu.registers[6]:08X}")
        print("  No trap occurred")
    except Exception as e:
        print(f"  Exception: {e}")

    # Check trap status
    if hasattr(cpu, 'trap_taken') and cpu.trap_taken:
        print(f"  Trap taken: cause={cpu.csrs[0x342]:08X}, mtval={cpu.csrs[0x343]:08X}")

if __name__ == "__main__":
    test_jalr_odd_address()
