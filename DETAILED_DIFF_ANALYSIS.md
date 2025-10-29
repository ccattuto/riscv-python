# Detailed Diff Analysis: RVC Support Implementation

This document details all changes made to implement compressed instruction (RVC) support in the RISC-V emulator, excluding cpu.py changes.

---

## 1. machine.py - Core Execution Loop Changes

### Overview
The machine.py file underwent significant changes to support both RV32I (pure 32-bit instructions) and RV32IC (with compressed 16-bit instructions) execution modes.

### Key Changes:

#### 1.1 Added `rvc` parameter to Machine class

```python
# BEFORE:
def __init__(self, cpu, ram, timer=False, mmio=False, logger=None, ...):
    self.timer = timer
    self.mmio = mmio

# AFTER:
def __init__(self, cpu, ram, timer=False, mmio=False, rvc=False, logger=None, ...):
    self.timer = timer
    self.mmio = mmio
    self.rvc = rvc    # NEW: Track whether RVC support is enabled
```

**Why:** Allows runtime selection of RV32I vs RV32IC mode to avoid performance penalty on pure RV32I code.

---

#### 1.2 Created new `run_fast_no_rvc()` method for RV32I-only execution

```python
# NEW METHOD: Fastest execution path for pure RV32I code
def run_fast_no_rvc(self):
    cpu = self.cpu
    ram = self.ram

    while True:
        # Check PC alignment before fetch (must be 4-byte aligned without C extension)
        if cpu.pc & 0x3:
            cpu.trap(cause=0, mtval=cpu.pc)  # Instruction address misaligned
            cpu.pc = cpu.next_pc
            continue

        # Fetch 32-bit instruction directly (no half-word fetch overhead)
        inst = ram.load_word(cpu.pc)

        cpu.execute(inst)
        cpu.pc = cpu.next_pc
```

**Key differences from RVC version:**
- **4-byte alignment check** (`& 0x3`) instead of 2-byte (`& 0x1`)
- **Single 32-bit word fetch** - no need to check instruction length
- **No half-word fetch overhead** - direct load_word() call
- **Performance:** Avoids the conditional logic and dual fetch path

---

#### 1.3 Updated `run_fast()` to implement proper RVC fetch

```python
# BEFORE:
def run_fast(self):
    cpu = self.cpu
    ram = self.ram
    while True:
        inst = ram.load_word(cpu.pc)  # Simple 32-bit fetch
        cpu.execute(inst)
        cpu.pc = cpu.next_pc

# AFTER:
def run_fast(self):
    cpu = self.cpu
    ram = self.ram

    while True:
        # Check PC alignment before fetch (must be 2-byte aligned with C extension)
        if cpu.pc & 0x1:
            cpu.trap(cause=0, mtval=cpu.pc)
            cpu.pc = cpu.next_pc
            continue

        # Optimized RVC fetch using masked 32-bit read
        inst32 = ram.load_word(cpu.pc)
        inst = inst32 if (inst32 & 0x3) else (inst32 & 0xFFFF)

        cpu.execute(inst)
        cpu.pc = cpu.next_pc
```

**Why this approach:**
- **2-byte alignment** allows compressed instructions at non-word-aligned addresses
- **Masked 32-bit read:** User requested this optimization - reads full word, masks to 16-bit if compressed
- **Faster than dual-fetch:** Avoids separate load_half() calls on the critical path
- **Spec-compliant:** Properly handles both 16-bit and 32-bit instructions

---

#### 1.4 Updated all other execution loops to support RVC

All execution loops were updated with spec-compliant RVC fetch:

**`run_with_checks()`** - Debug/trace version:
```python
# BEFORE:
inst = ram.load_word(cpu.pc)

# AFTER:
# Check PC alignment (2-byte for RVC)
if cpu.pc & 0x1:
    cpu.trap(cause=0, mtval=cpu.pc)
    # ... handle trap path
    continue

# Fetch 16 bits first to determine instruction length (RISC-V spec compliant)
inst_low = ram.load_half(cpu.pc, signed=False)
if (inst_low & 0x3) == 0x3:
    # 32-bit instruction: fetch upper 16 bits
    inst_high = ram.load_half(cpu.pc + 2, signed=False)
    inst = inst_low | (inst_high << 16)
else:
    # 16-bit compressed instruction
    inst = inst_low
```

**Why this approach for non-fast paths:**
- Uses **dual half-word fetches** (spec-compliant parcel-based method)
- More readable and easier to verify correctness
- Performance already compromised by checks/logging/MMIO, so clarity > speed

Same pattern applied to:
- `run_timer()` - Timer support version
- `run_mmio()` - MMIO + timer version
- `run_with_checks()` - Full debug version

---

#### 1.5 Updated `run()` dispatcher to select appropriate runner

```python
# BEFORE:
def run(self):
    if self.regs or self.check_inv or self.trace:
        self.run_with_checks()
    else:
        if self.mmio:
            self.run_mmio()
        else:
            if self.timer:
                self.run_timer()
            else:
                self.run_fast()  # Only one fast path

# AFTER:
def run(self):
    if self.regs or self.check_inv or self.trace:
        self.run_with_checks()  # (always with RVC support)
    else:
        if self.mmio:
            self.run_mmio()  # (always with RVC support)
        else:
            if self.timer:
                self.run_timer()  # (always with RVC support)
            else:
                # Fastest option - RVC is optional
                if self.rvc:
                    self.run_fast()           # Fast with RVC (masked 32-bit)
                else:
                    self.run_fast_no_rvc()    # Fastest: pure RV32I
```

**Strategy:**
- **Debug/Timer/MMIO paths:** Always use RVC (already slow, no point optimizing)
- **Fast path only:** Choose RV32I vs RV32IC based on `self.rvc` flag
- **Maximum performance:** Pure RV32I code runs fastest possible path

---

## 2. riscv-emu.py - Command-Line Interface

### Changes:

#### 2.1 Added `--rvc` command-line argument

```python
# NEW ARGUMENT:
parser.add_argument('--rvc', action="store_true",
                   help='Enable RVC (compressed instructions) support')
```

**Default:** RVC is **disabled** (pure RV32I for maximum performance)
**Usage:** Pass `--rvc` flag to enable compressed instruction support

---

#### 2.2 Pass rvc flag to Machine constructor

```python
# BEFORE:
machine = Machine(cpu, ram, timer=args.timer, mmio=use_mmio, logger=log, ...)

# AFTER:
machine = Machine(cpu, ram, timer=args.timer, mmio=use_mmio, rvc=args.rvc, logger=log, ...)
```

---

#### 2.3 Minor fixes

```python
# BUG FIX: Removed incorrect line that forced check_ram for MMIO
# BEFORE:
if args.uart or args.blkdev or (args.timer == "mmio"):
    args.check_ram = True  # This was wrong!
    use_mmio = True

# AFTER:
if args.uart or args.blkdev or (args.timer == "mmio"):
    use_mmio = True
```

**Why:** `args.check_ram` should only be set by user flags, not implicitly by MMIO.

```python
# IMPROVEMENT: Better error message
# BEFORE:
log.error(f"EMULATOR ERROR ({type(e).__name__}): {e}")

# AFTER:
log.error(f"EMULATOR ERROR ({type(e).__name__}) during setup: {e}")
```

```python
# FIX: Corrected MMIOBlockDevice constructor call
# BEFORE:
blkdev = MMIOBlockDevice(args.blkdev, ram, size=args.blkdev_size, logger=log)

# AFTER:
blkdev = MMIOBlockDevice(image_path=args.blkdev, ram=ram, block_size=512,
                         size=args.blkdev_size, logger=log)
```

**Why:** Use explicit keyword arguments for clarity and correctness.

---

## 3. run_unit_tests.py - Test Runner Updates

### Changes:

#### 3.1 Added RV32UC test suite support

```python
# BEFORE: Only RV32UI and RV32MI tests
test_rv32ui_fnames = [fname for fname in glob.glob('riscv-tests/isa/rv32ui-p-*') ...]
test_rv32mi_fnames = [fname for fname in glob.glob('riscv-tests/isa/rv32mi-p-*') ...]
test_fname_list = test_rv32ui_fnames + test_rv32mi_fnames

# AFTER: Added RV32UC (compressed instruction tests)
test_rv32ui_fnames = [fname for fname in glob.glob('riscv-tests/isa/rv32ui-p-*') ...]
test_rv32mi_fnames = [fname for fname in glob.glob('riscv-tests/isa/rv32mi-p-*') ...]
test_rv32uc_fnames = [fname for fname in glob.glob('riscv-tests/isa/rv32uc-p-*') ...]
test_fname_list = test_rv32ui_fnames + test_rv32mi_fnames + test_rv32uc_fnames
```

**Why:** Enable testing of compressed instruction functionality.

---

#### 3.2 Enable RVC support for tests

```python
# BEFORE:
machine = Machine(cpu, ram)

# AFTER:
machine = Machine(cpu, ram, rvc=True)  # Enable RVC for tests that use compressed instructions
```

**Why:** Official RISC-V tests include compressed instruction tests (rv32uc-p-*).

---

#### 3.3 Implement proper RVC fetch in test loop

```python
# BEFORE: Simple 32-bit fetch
inst = ram.load_word(cpu.pc)

# AFTER: Spec-compliant RVC fetch
# Check PC alignment before fetch (must be 2-byte aligned with C extension)
if cpu.pc & 0x1:
    cpu.trap(cause=0, mtval=cpu.pc)
    cpu.pc = cpu.next_pc
    if ram.load_word(tohost_addr) != 0xFFFFFFFF:
        break
    continue

# Fetch using spec-compliant parcel-based approach
inst_low = ram.load_half(cpu.pc, signed=False)
if (inst_low & 0x3) == 0x3:
    # 32-bit instruction: fetch upper 16 bits
    inst_high = ram.load_half(cpu.pc + 2, signed=False)
    inst = inst_low | (inst_high << 16)
else:
    # 16-bit compressed instruction
    inst = inst_low
```

**Why:** Tests execute compressed instructions, require proper fetch logic.

---

#### 3.4 Enhanced failure reporting

```python
# BEFORE: Simple pass/fail
print(f"Test {os.path.basename(test_fname):<30}: {"PASS" if test_result == 1 else "FAIL"}")

# AFTER: Detailed failure info
result_str = "PASS" if test_result == 1 else f"FAIL (test #{test_result >> 1})"

if test_result != 1:
    print(f"Test {os.path.basename(test_fname):<30}: {result_str}")
    print(f"  tohost value: 0x{test_result:08X}")
    print(f"  Final PC: 0x{cpu.pc:08X}")
    print(f"  mepc: 0x{cpu.csrs[0x341]:08X}")
    print(f"  mcause: 0x{cpu.csrs[0x342]:08X}")
    print(f"  mtval: 0x{cpu.csrs[0x343]:08X}")
else:
    print(f"Test {os.path.basename(test_fname):<30}: {result_str}")
```

**Why:** Better debugging - shows which specific test failed and CSR state.

---

#### 3.5 Fixed typo in comment

```python
# BEFORE:
# if sentinel value has been overwritted, the test is over

# AFTER:
# if sentinel value has been overwritten, the test is over
```

---

## 4. ram.py - Safety Improvements

### Changes:

#### 4.1 Added padding to prevent buffer overruns

```python
# BEFORE:
def __init__(self, size=1024*1024, init=None, logger=None):
    self.memory = bytearray(size)

# AFTER:
def __init__(self, size=1024*1024, init=None, logger=None, padding=4):
    self.memory = bytearray(size + padding)  # Extra 4 bytes prevents overrun
    self.memory32 = memoryview(self.memory).cast("I")
    self.size = size
```

**Why:** When fetching near end of memory, a 32-bit word read could read beyond allocated size. Padding prevents IndexError.

---

#### 4.2 Added exception handling to all RAM methods

All load/store methods now catch IndexError and raise informative MemoryAccessError:

```python
# EXAMPLE: load_word()
# BEFORE:
def load_word(self, addr):
    if addr & 0x3 == 0:
        return self.memory32[addr >> 2]
    else:
        return self.memory[addr] | (self.memory[addr+1] << 8) | ...

# AFTER:
def load_word(self, addr):
    try:
        if addr & 0x3 == 0:
            return self.memory32[addr >> 2]
        else:
            return self.memory[addr] | (self.memory[addr+1] << 8) | ...
    except IndexError:
        raise MemoryAccessError(f"Access out of bounds: 0x{addr:08X} (+{4})")
```

**Applied to:**
- `load_byte()`, `load_half()`, `load_word()`
- `store_byte()`, `store_half()`, `store_word()`
- `store_binary()`

**Why:** Provides clear error messages instead of cryptic IndexError, helps debugging.

---

## Summary of Changes

### Performance Strategy:
1. **RV32I mode** (default): Direct 32-bit fetch, 4-byte alignment, no overhead
2. **RV32IC mode** (`--rvc` flag): Masked 32-bit read for fast path, dual-fetch for debug paths
3. **Debug/Timer/MMIO**: Always RVC-enabled (already slow, clarity > speed)

### Testing:
- Added RV32UC test suite support
- Enhanced failure reporting with CSR dump
- Proper RVC fetch in test runner

### Safety:
- RAM padding prevents buffer overruns
- Comprehensive bounds checking with clear error messages

### User Experience:
- Simple `--rvc` flag to enable compressed instructions
- Default (no flag) runs pure RV32I at maximum speed
- All existing functionality preserved

---

## Usage Examples:

```bash
# Pure RV32I (fastest, default)
./riscv-emu.py program.elf

# With compressed instruction support
./riscv-emu.py --rvc program.elf

# Run test suite (RVC enabled by default in tests)
./run_unit_tests.py
```

---

## Performance Impact:

**RV32I mode** (no --rvc):
- ✅ No half-word fetch
- ✅ No instruction length check
- ✅ Direct 32-bit word read
- ✅ Optimal for pure RV32I binaries

**RV32IC mode** (with --rvc):
- Uses masked 32-bit read optimization in fast path
- Spec-compliant dual-fetch in debug paths
- Supports 2-byte aligned jumps
- Required for RVC test suite
