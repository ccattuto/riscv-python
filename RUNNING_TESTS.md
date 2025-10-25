# Running RISC-V Unit Tests

The emulator includes support for running the official RISC-V compliance tests, including compressed instruction tests.

## Supported Test Suites

- **rv32ui**: User-level integer instructions (base RV32I ISA)
- **rv32mi**: Machine-mode integer instructions (traps, CSRs, etc.)
- **rv32uc**: User-level compressed instructions (RVC extension) ✨ **NEW**

## Prerequisites

### 1. RISC-V Toolchain

You need a RISC-V cross-compiler to build the tests. Install one of:

**Option A: Pre-built toolchain**
```bash
# For Ubuntu/Debian
sudo apt-get install gcc-riscv64-unknown-elf

# For macOS with Homebrew
brew tap riscv-software-src/riscv
brew install riscv-tools
```

**Option B: Build from source**
```bash
git clone https://github.com/riscv-collab/riscv-gnu-toolchain
cd riscv-gnu-toolchain
./configure --prefix=/opt/riscv --with-arch=rv32gc --with-abi=ilp32
make
export PATH=/opt/riscv/bin:$PATH
```

### 2. Initialize Test Submodule

```bash
cd riscv-python
git submodule update --init --recursive
cd riscv-tests
```

## Building the Tests

### Configure and Build All Tests

```bash
cd riscv-tests
autoconf
./configure --prefix=$PWD/install
make
make install
cd ..
```

This will build all test suites including:
- `riscv-tests/isa/rv32ui-p-*` - Base integer tests
- `riscv-tests/isa/rv32mi-p-*` - Machine mode tests
- `riscv-tests/isa/rv32uc-p-*` - **Compressed instruction tests**

### Build Only Specific Tests (Optional)

If you only want to build specific test suites:

```bash
cd riscv-tests/isa
make rv32ui    # Base integer only
make rv32mi    # Machine mode only
make rv32uc    # Compressed instructions only
cd ../..
```

## Running the Tests

### Run All Tests

```bash
./run_unit_tests.py
```

This will run all rv32ui, rv32mi, and rv32uc tests and report results:

```
Test rv32ui-p-add                  : PASS
Test rv32ui-p-addi                 : PASS
Test rv32ui-p-and                  : PASS
...
Test rv32mi-p-csr                  : PASS
Test rv32mi-p-mcsr                 : PASS
...
Test rv32uc-p-rvc                  : PASS  ✨ Compressed instructions!
```

### Run a Single Test

```bash
./run_unit_tests.py riscv-tests/isa/rv32uc-p-rvc
```

### Run Only Compressed Tests

```bash
for test in riscv-tests/isa/rv32uc-p-*; do
    ./run_unit_tests.py "$test"
done
```

## Understanding Test Results

- **PASS**: Test executed correctly
- **FAIL**: Test failed (indicates emulator bug)

Each test writes a result to a special `tohost` variable:
- `tohost = 1`: Test passed
- `tohost = <other>`: Test failed with error code

## Test Coverage

### RV32UI Tests (~40 tests)
Tests for all base integer instructions:
- Arithmetic: ADD, SUB, ADDI, etc.
- Logic: AND, OR, XOR, shifts
- Loads/Stores: LB, LH, LW, SB, SH, SW
- Branches: BEQ, BNE, BLT, BGE, etc.
- Jumps: JAL, JALR

### RV32MI Tests (~15 tests)
Tests for machine-mode features:
- CSR operations
- Traps and exceptions
- Illegal instructions
- Misaligned accesses
- ECALL, EBREAK, MRET

### RV32UC Tests ✨ NEW
Tests for compressed instructions:
- All C0, C1, C2 quadrant instructions
- Mixed compressed and standard code
- Alignment requirements
- Compressed branches and jumps

## Test Implementation Details

### Spec-Compliant Fetch

The test runner uses proper parcel-based instruction fetching:

```python
# Fetch 16 bits first to determine instruction length
inst_low = ram.load_half(cpu.pc, signed=False)
if (inst_low & 0x3) == 0x3:
    # 32-bit instruction: fetch upper 16 bits
    inst_high = ram.load_half(cpu.pc + 2, signed=False)
    inst = inst_low | (inst_high << 16)
else:
    # 16-bit compressed instruction
    inst = inst_low
```

This ensures:
- Correct behavior at memory boundaries
- No spurious memory accesses
- RISC-V spec compliance

### Test Execution Flow

1. Load ELF test binary
2. Find `tohost` symbol address
3. Write sentinel value (0xFFFFFFFF) to `tohost`
4. Execute instructions until `tohost` changes
5. Check `tohost` value: 1 = PASS, other = FAIL

## Troubleshooting

### Tests Not Found

```bash
# Make sure submodule is initialized
git submodule update --init riscv-tests

# Make sure tests are built
cd riscv-tests
make
```

### Compiler Not Found

```bash
# Check if RISC-V compiler is in PATH
which riscv32-unknown-elf-gcc
which riscv64-unknown-elf-gcc

# Add toolchain to PATH if needed
export PATH=/opt/riscv/bin:$PATH
```

### All Tests Fail

If all tests fail, there may be an issue with:
- Base address: Tests expect code at 0x80000000
- Instruction fetch: Make sure parcel-based fetching is used
- CSR implementation: Check misa, mstatus, etc.

### Compressed Tests Fail

If only rv32uc tests fail:
- Check that misa CSR has C bit set (bit 2)
- Verify compressed instruction expansion logic
- Check 2-byte alignment enforcement
- Ensure parcel-based fetch is working

## Current Test Status

As of the latest commit, the emulator passes:
- ✅ All rv32ui tests (100%)
- ✅ All rv32mi tests (100%)
- ✅ All rv32uc tests (100%) - **With compressed instruction support!**

## References

- [RISC-V Tests Repository](https://github.com/riscv-software-src/riscv-tests)
- [RISC-V ISA Specification](https://riscv.org/technical/specifications/)
- [Compressed Instruction Extension](https://five-embeddev.com/riscv-isa-manual/latest/c.html)
