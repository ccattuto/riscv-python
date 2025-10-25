# Analysis of Test Failures

## Test rv32mi-p-ma_fetch Test #4

### What the test does (lines 53-64 of rv64si/ma_fetch.S):
```asm
li TESTNUM, 4
li t1, 0
la t0, 1f
jalr t1, t0, 3     # Jump to (t0 + 3)
1:
  .option rvc
  c.j 1f           # Compressed jump forward
  c.j 2f           # Second compressed jump (target)
  .option norvc
1:
  j fail           # Should not reach here
2:                 # Success point
```

### Expected behavior:

1. **JALR execution**:
   - Target address = (t0 + 3)
   - After clearing LSB per spec: target = (t0 + 2)  [bit 0 cleared]

2. **With C extension enabled** (initial state):
   - Address (t0 + 2) is 2-byte aligned → OK, no trap
   - PC jumps to (t0 + 2), which is the second compressed instruction `c.j 2f`
   - Executes `c.j 2f` → jumps to label 2 → test passes

3. **With C extension disabled**:
   - Address (t0 + 2) is NOT 4-byte aligned (bit 1 = 1) → should trap
   - Trap handler (stvec_handler) is called
   - Handler verifies it's test #4, checks trap cause, and skips ahead
   - Test passes

###  My implementation (after fixes):

```python
def exec_JALR(cpu, ram, inst, rd, funct3, rs1, rs2, funct7):
    imm_i = inst >> 20
    if imm_i >= 0x800: imm_i -= 0x1000
    addr_target = (cpu.registers[rs1] + imm_i) & 0xFFFFFFFE  # clear bit 0 per RISC-V spec

    # Check alignment based on whether RVC is enabled
    misaligned = False
    if not cpu.is_rvc_enabled():
        misaligned = (addr_target & 0x2) != 0  # Check bit 1 for 4-byte alignment

    if misaligned:
        cpu.trap(cause=0, mtval=addr_target)  # instruction address misaligned
    else:
        if rd != 0:
            cpu.registers[rd] = (cpu.pc + 4) & 0xFFFFFFFF
        cpu.next_pc = addr_target
```

**Analysis**: This should handle both cases correctly:
- ✅ With C enabled: (t0+2) has bit 1=1 but that's OK, no misalignment check needed
- ✅ With C disabled: (t0+2) has bit 1=1, detected as misaligned, traps correctly

---

## Test rv32uc-p-rvc Test #12

### What the test does (line 57 of rv64uc/rvc.S):
```asm
RVC_TEST_CASE (12, s0, 0x000fffe1, c.lui s0, 0xfffe1; c.srli s0, 12)
```

### Expected behavior:

1. **c.lui s0, 0xfffe1**:
   - Immediate value 0xfffe1 must be encoded in 6 bits [17:12]
   - 0xfffe1 bits [17:12] = 111111 = -1 (6-bit signed)
   - Actually: 0xfffe1 = 0b11111111111100001
   - Bits [17:12] = 0b111111 = 0x3F = 63
   - As 6-bit signed: 0x3F = -1, extends to 0xFFFFF (20 bits)

   Wait, that's wrong! Let me recalculate:
   - 0xfffe1 = 0b00001111111111100001 (20 bits, bit 19=0, bit 17=1)
   - Bits [17:12] = 0b111110 = 0x3E = 62
   - NO wait: 0xfffe1 in binary is 1111111111100001 (17 bits minimum)
   - With bit 19=0, bit 18=0, bits [17:12] = 111111 = 0x3F

   Actually, the key insight: 0xfffe1 is a NEGATIVE number in 20-bit signed representation
   - 0xfffe1 = 1048545 unsigned, or -32287 signed? No...
   - Let me think: 0xfffe1 with bit 19 = 0, so it's positive in 20-bit arithmetic
   - But we need to extract bits [17:12]: Taking 0xfffe1 >> 12 = 0xF (but that's only 4 bits)

   I'm confusing myself. Let me look at what my test showed:
   - c.lui instruction 0x7405 worked correctly
   - It produced s0 = 0xfffe1000
   - So the encoding must be right

2. **c.srli s0, 12**:
   - Logical shift right by 12
   - 0xfffe1000 >> 12 = 0x000fffe1 ✅

### My implementation:

My manual test `test_debug_rvc12.py` showed this works correctly, producing the expected result 0x000fffe1.

**Analysis**: ✅ Implementation appears correct

---

## Possible Issues

### 1. Test framework interaction
The tests use macros (RVC_TEST_CASE, TEST_CASE) that set up state and check results. If there's an issue with:
- Register initialization
- Test numbering
- tohost write-back
- State from previous tests

The test could fail even if instruction execution is correct.

### 2. Memory layout
The ma_fetch test relies on specific memory layout of compressed instructions. If the addresses don't align as expected, the test could fail.

### 3. Trap handler state
The ma_fetch test has a sophisticated trap handler. If CSRs (mepc, mcause, mtval) aren't set correctly, the handler could fail.

---

## Current Status

Without access to test binaries, I cannot verify these fixes. However, based on:
- ✅ RISC-V specification compliance
- ✅ Test source code analysis
- ✅ Custom test verification

The implementation should now correctly handle:
1. Dynamic C extension toggling
2. Alignment checks based on C enabled/disabled state
3. Proper JALR LSB clearing and alignment checking
4. Proper MRET mepc masking per spec
5. Compressed instruction expansion (C.LUI, C.SRLI)

## To Verify

To verify these fixes work with the official tests, you would need to:

```bash
# Build RISC-V toolchain and tests (on a system with the toolchain)
cd riscv-tests
autoconf
./configure --prefix=$PWD/install
make

# Run the specific failing tests
cd ..
./run_unit_tests.py riscv-tests/isa/rv32mi-p-ma_fetch
./run_unit_tests.py riscv-tests/isa/rv32uc-p-rvc
```

The expected output should be:
```
Test rv32mi-p-ma_fetch : PASS
Test rv32uc-p-rvc      : PASS
```
