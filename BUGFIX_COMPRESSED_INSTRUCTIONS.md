# Bug Fix: Compressed Instruction Decode Cache Issue

## Problem Summary

Test rv32uc-p-rvc #12 was failing with register s0 containing 0x00007000 instead of the expected 0x000FFFE1 after executing:
```assembly
c.lui s0, 0xfffe1    # Should set s0 = 0xFFFE1000
c.srli s0, 12        # Should shift right to get s0 = 0x000FFFE1
```

## Root Cause

The bug was in the instruction decode cache implementation in `cpu.py:execute()`.

### The Issue

When a compressed instruction was executed:

1. **First execution (cache miss)**:
   - Compressed instruction (e.g., 0x7405) was expanded to 32-bit equivalent (0xFFFE1437)
   - The expanded instruction was decoded to extract opcode, rd, rs1, etc.
   - These decoded fields were cached
   - The opcode handler (e.g., `exec_LUI`) was called with the **expanded** instruction ✓

2. **Subsequent executions (cache hit)**:
   - Decoded fields were retrieved from cache
   - **BUT** the `inst` variable was never updated to the expanded instruction
   - The opcode handler received the **compressed** instruction (0x7405) instead of expanded (0xFFFE1437) ✗

3. **Result**:
   - `exec_LUI` extracted immediate from compressed instruction: `imm_u = 0x7405 >> 12 = 0x7`
   - Final value: `0x7 << 12 = 0x7000` (wrong!)
   - Expected: `0xFFFE1 << 12 = 0xFFFE1000` (correct)

## The Fix

Modified `cpu.py:execute()` to cache the expanded instruction along with the decoded fields:

**Before:**
```python
self.decode_cache[cache_key] = (opcode, rd, funct3, rs1, rs2, funct7, inst_size)
```

**After:**
```python
self.decode_cache[cache_key] = (opcode, rd, funct3, rs1, rs2, funct7, inst_size, expanded_inst)
```

On cache hit, the expanded instruction is now retrieved and used:
```python
try:
    opcode, rd, funct3, rs1, rs2, funct7, inst_size, expanded_inst = self.decode_cache[cache_key]
    if is_compressed:
        inst = expanded_inst  # Use cached expanded instruction
```

## Performance Impact

The fix maintains performance by:
- Expanding compressed instructions only once (on cache miss)
- Reusing the cached expanded instruction on subsequent executions
- No additional overhead for the cache hit path (most common case)

Performance test shows ~1.1 million compressed instructions/second with proper caching.

## Related Fix: C.LUI Sign Extension

Also fixed C.LUI immediate encoding (cpu.py:418):
```python
imm_20bit = nzimm & 0xFFFFF  # Mask to 20 bits before shifting
```

This ensures negative immediates are properly masked to 20 bits before being shifted into the instruction encoding.

## Testing

Test case `test_debug_rvc12.py` now passes, correctly producing:
- After `c.lui s0, 0xfffe1`: s0 = 0xFFFE1000 ✓
- After `c.srli s0, 12`: s0 = 0x000FFFE1 ✓

## Files Modified

- `cpu.py` (lines 650-697): Fixed decode cache to store and use expanded instructions
- `cpu.py` (line 418): Fixed C.LUI immediate masking

## Test Files Created

- `test_expansion_debug.py`: Tests C.LUI expansion logic
- `test_performance.py`: Validates decode cache performance
- `test_debug_rvc12.py`: Standalone test for RVC test case #12
