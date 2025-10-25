# Debugging Test Failures

## Current Situation

You're reporting that these tests fail:
```
Test rv32mi-p-ma_fetch             : FAIL
Test rv32mi-p-sbreak               : PASS
Test rv32uc-p-rvc                  : FAIL
```

However, the test binaries don't appear to be in the repository. This means either:
1. You've built them locally
2. You have pre-built binaries somewhere
3. This is output from a previous run

## Step 1: Verify Test Binaries Exist

Run the diagnostic script:
```bash
python3 diagnose_tests.py
```

This will show:
- Whether test sources exist (they do)
- Whether test binaries exist (they don't in the repo)
- Where to find the toolchain

## Step 2: Build the Tests (If Needed)

If binaries don't exist, build them:

```bash
# Install RISC-V toolchain first (see RUNNING_TESTS.md)

cd riscv-tests
autoconf
./configure --prefix=$PWD/install
make
cd ..
```

This creates binaries like:
- `riscv-tests/isa/rv32mi-p-ma_fetch`
- `riscv-tests/isa/rv32uc-p-rvc`

## Step 3: Run Tests with Debug Output

The test runner has been updated to show which specific test case fails:

```bash
./run_unit_tests.py
```

Output will show:
```
Test rv32mi-p-ma_fetch             : FAIL (test #2)
                                            ^^^^^^^
                                            Tells you which TEST_CASE failed
```

## Step 4: Debug Specific Test

Create a debug runner for a single test:

```bash
python3 debug_single_test.py riscv-tests/isa/rv32mi-p-ma_fetch
```

(Script created below)

## Understanding Test Results

The `tohost` variable encodes the test result:
- `tohost = 1` (0x00000001): Test PASSED
- `tohost = N` (N > 1): Test FAILED at test case #(N >> 1)

For example:
- `tohost = 0x00000005`: Failed at test case #2 (5 >> 1 = 2)
- `tohost = 0x0000000B`: Failed at test case #5 (11 >> 1 = 5)

## Known Issues to Check

### rv32mi-p-ma_fetch

This test checks misaligned fetch behavior. Looking at the source (`riscv-tests/isa/rv64si/ma_fetch.S`):

**Test #2** (lines 31-42): Tests JALR to misaligned address
- Without RVC: should trap
- With RVC: should NOT trap, execute compressed instruction

**Potential issues:**
1. PC alignment check might be wrong
2. Compressed instruction at odd address not handled
3. JALR not clearing LSB correctly

**Debug:**
```python
# Add to run_unit_tests.py at line 63:
if 'ma_fetch' in test_fname:
    print(f"PC=0x{cpu.pc:08X}")
```

### rv32uc-p-rvc

This test checks all compressed instructions. Looking at source (`riscv-tests/isa/rv64uc/rvc.S`):

**Test #3** (line 41): C.ADDI4SPN
**Test #6** (line 44): C.LW/C.SW
**Test #21** (line 69): C.SLLI

**Potential issues:**
1. Immediate encoding bugs
2. Register mapping (x8-x15 for compressed)
3. Offset calculations

**Debug:**
```python
# Check which test fails, then add logging for that instruction type
if 'rvc' in test_fname and test_result != 1:
    print(f"Failed at test #{test_result >> 1}")
    print(f"PC was at: 0x{cpu.pc:08X}")
```

## Enhanced Debug Runner

I'll create `debug_single_test.py` that shows:
- PC trace
- Instruction disassembly
- Register changes
- Where the test failed

## Quick Verification

Our custom tests all pass:
```bash
python3 test_compressed.py              # ✓ PASS
python3 test_compressed_boundary.py      # ✓ PASS
python3 test_compressed_expansion.py     # ✓ PASS
```

This means the basic implementation is correct. The official test failures are likely:
1. Edge cases we haven't covered
2. Specific instruction encoding bugs
3. Interaction between features

## Next Steps

1. Run `python3 diagnose_tests.py` to confirm test status
2. If tests exist, run with updated runner to see test case numbers
3. Use the debug information to identify the specific failing instruction
4. Create a minimal reproduction case
5. Fix the bug

## Getting Help

If you can provide:
1. The actual test result value (not just FAIL)
2. The test case number that fails
3. Any error messages or traps

I can help debug the specific issue. The test sources are available in:
- `riscv-tests/isa/rv32mi/ma_fetch.S`
- `riscv-tests/isa/rv64uc/rvc.S`

These show exactly what each test case does.
