#!/usr/bin/env python3
"""Debug test case #12 from rv32uc-p-rvc"""

from cpu import CPU, expand_compressed
from ram import RAM

def test_case_12():
    """
    RVC_TEST_CASE (12, s0, 0x000fffe1, c.lui s0, 0xfffe1; c.srli s0, 12)
    For RV32: Expected result s0 = 0x000fffe1
    """
    print("Testing RVC test case #12: c.lui s0, 0xfffe1; c.srli s0, 12")
    print("=" * 60)

    ram = RAM(1024)
    cpu = CPU(ram)

    # Test C.LUI encoding for 0xfffe1
    # The immediate 0xfffe1 should be encoded as bits [17:12]
    # 0xfffe1 when placed in [31:12] gives 0xfffe1000
    # Bits [17:12] of 0xfffe1 are: (0xfffe1 >> 0) & 0x3F = 0x21
    # But we need to figure out what the assembler actually encodes

    # Let's manually construct c.lui s0, nzimm where we want s0 = 0xfffe1000
    # s0 = x8, rd = 8
    # C.LUI format: 011 nzimm[17] rd[4:0] nzimm[16:12] 01
    # We want nzimm = 0xfffe1, but C.LUI only has 6 bits for nzimm[17:12]

    # For 0xfffe1000 to be the result, we need:
    # nzimm[17:12] when sign-extended to give 0xfffe1 in the upper 20 bits
    # 0xfffe1000 >> 12 = 0xfffe1 (20-bit value)
    # We need the 6-bit signed representation that extends to 0xfffe1

    # 0xfffe1 = 0000 1111 1111 1110 0001 (20 bits)
    # Taking bits [5:0]: 0x21 = 100001
    # As 6-bit signed: bit 5 = 1, so negative: 0x21 - 0x40 = -31
    # -31 sign-extended to 20 bits: 0xFFFE1
    # Shifted left 12: 0xFFFE1000

    # So nzimm bits in instruction should be 0x21
    # C.LUI format: 011 nzimm[5] rd[4:0] nzimm[4:0] 01
    #              011   1      01000     00001     01
    # rd = 8 (s0) = 01000
    # nzimm = 0x21 = 100001
    # Instruction: 011 1 01000 00001 01 = 0111010000000101 = 0x7405
    c_lui_inst = 0x7405

    print(f"C.LUI instruction: 0x{c_lui_inst:04X}")
    expanded_lui, success = expand_compressed(c_lui_inst)
    print(f"  Expanded: 0x{expanded_lui:08X}, success={success}")
    if success:
        cpu.execute(expanded_lui)
        cpu.pc = cpu.next_pc
        s0_after_lui = cpu.registers[8]
        print(f"  s0 after C.LUI: 0x{s0_after_lui:08X}")

    # Now test C.SRLI s0, 12
    # C.SRLI format: 100 shamt[5] 00 rs1'/rd' shamt[4:0] 01
    # rs1'/rd' = 0 for s0 (s0 = x8 = prime register 0)
    # shamt = 12 = 001100
    # Instruction: 100 0 00 000 01100 01 = 1000000000110001 = 0x8031
    c_srli_inst = 0x8031

    print(f"\nC.SRLI instruction: 0x{c_srli_inst:04X}")
    expanded_srli, success = expand_compressed(c_srli_inst)
    print(f"  Expanded: 0x{expanded_srli:08X}, success={success}")
    if success:
        cpu.execute(expanded_srli)
        cpu.pc = cpu.next_pc
        s0_after_srli = cpu.registers[8]
        print(f"  s0 after C.SRLI: 0x{s0_after_srli:08X}")

        expected = 0x000fffe1
        if s0_after_srli == expected:
            print(f"\n✓ TEST PASSED: Got expected value 0x{expected:08X}")
            return True
        else:
            print(f"\n✗ TEST FAILED: Expected 0x{expected:08X}, got 0x{s0_after_srli:08X}")
            return False

if __name__ == "__main__":
    test_case_12()
