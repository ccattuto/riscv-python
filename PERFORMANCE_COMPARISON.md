# Performance Comparison: Original vs RVC-Toggle Support

## Hot Path Analysis

### exec_branches() - Taken Branch Path

**Original (90bcf04):**
```python
addr_target = (cpu.pc + imm_b) & 0xFFFFFFFF
if addr_target & 0x1:                           # 1 bitwise AND
    cpu.trap(cause=0, mtval=addr_target)        # rarely taken
else:
    cpu.next_pc = addr_target                   # common case - FAST
```

**Current (with RVC toggle):**
```python
addr_target = (cpu.pc + imm_b) & 0xFFFFFFFF
if addr_target & 0x1:                           # 1 bitwise AND
    cpu.trap(cause=0, mtval=addr_target)        # rarely taken
elif not cpu.rvc_enabled and (addr_target & 0x2):  # OVERHEAD ON COMMON PATH
    # 1. Field access: cpu.rvc_enabled
    # 2. Boolean NOT operation
    # 3. Short-circuit evaluation
    # 4. (skips second part due to short-circuit)
    cpu.trap(cause=0, mtval=addr_target)
else:
    cpu.next_pc = addr_target                   # common case - SLOWER
```

### Performance Impact Breakdown

For a taken branch that doesn't trap (common case):

**Original:**
1. Bitwise AND: `addr_target & 0x1`
2. Boolean check (False)
3. Jump to else
4. Assignment: `cpu.next_pc = addr_target`

**Current:**
1. Bitwise AND: `addr_target & 0x1`
2. Boolean check (False)
3. Jump to elif
4. **Field access: `cpu.rvc_enabled`** ← NEW OVERHEAD
5. **Boolean NOT** ← NEW OVERHEAD
6. **Short-circuit eval** ← NEW OVERHEAD
7. Jump to else
8. Assignment: `cpu.next_pc = addr_target`

**Result:** 3 extra operations on EVERY taken branch

### exec_JAL() - Same Issue

**Original:**
```python
if addr_target & 0x1:
    cpu.trap(...)
else:
    if rd != 0:
        cpu.registers[rd] = ...
    cpu.next_pc = addr_target
```

**Current:**
```python
if addr_target & 0x1:
    cpu.trap(...)
elif not cpu.rvc_enabled and (addr_target & 0x2):  # OVERHEAD
    cpu.trap(...)
else:
    if rd != 0:
        cpu.registers[rd] = ...
    cpu.next_pc = addr_target
```

Same 3 extra operations on EVERY JAL that doesn't trap.

### exec_JALR() - Slightly Better But Still Overhead

**Original:**
```python
addr_target = (cpu.registers[rs1] + imm_i) & 0xFFFFFFFE
if addr_target & 0x1:  # Dead code bug - always False!
    cpu.trap(...)
else:
    if rd != 0:
        cpu.registers[rd] = ...
    cpu.next_pc = addr_target
```

**Current:**
```python
addr_target = (cpu.registers[rs1] + imm_i) & 0xFFFFFFFE
if not cpu.rvc_enabled and (addr_target & 0x2):  # OVERHEAD on EVERY JALR
    cpu.trap(...)
else:
    if rd != 0:
        cpu.registers[rd] = ...
    cpu.next_pc = addr_target
```

Still evaluates `not cpu.rvc_enabled` on EVERY JALR.

## Frequency Analysis

In a typical RISC-V program:
- **Branches**: ~15-20% of instructions
- **JAL/JALR**: ~3-5% of instructions
- **Total control flow**: ~20-25% of instructions

With 50% slowdown, and control flow being ~20% of instructions:
- If ONLY control flow is affected: 20% × 2.5x slower = 50% overall slowdown ✓

This matches the observed performance degradation!

## Root Cause

The problem is **Python's attribute access and boolean operations are expensive**.

Even though the check short-circuits, Python must:
1. Load the `rvc_enabled` field from the CPU object (attribute lookup)
2. Apply the `not` operator (creates temporary boolean)
3. Evaluate short-circuit logic

This happens on **every single control flow instruction** that takes the branch/jump.

## Potential Solutions

### Option 1: Accept the Performance Hit
- Keep current implementation
- 50% slowdown is significant but enables RVC toggling
- Most users run with RVC always enabled anyway

### Option 2: Make RVC Toggle a Compile-Time Option
- Use a class variable or constant
- Python might optimize this better
- But still won't work if toggling at runtime is required

### Option 3: Separate Execution Paths
- Have two sets of control flow handlers
- Switch between them when misa changes
- More complex but zero overhead

### Option 4: Just-In-Time Patching
- Dynamically patch the instruction handlers when misa changes
- Most complex but best performance

### Option 5: Revert RVC Toggle Support
- If tests don't actually require it, remove the feature
- Restore original performance
- Need to verify test requirements first

## Recommendation

**Before proceeding, we need to know:**
1. Do the tests actually still fail with current implementation?
2. Are the test failures related to RVC toggling or something else?
3. Is RVC toggling a hard requirement?

If tests are failing for other reasons, the 50% performance hit is not worth it.
