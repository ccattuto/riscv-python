#!/usr/bin/env python3
"""
Benchmark: 32-bit word fetch vs conditional 16-bit half-word fetch

Tests the performance difference between:
1. Single 32-bit word fetch (current run_fast approach)
2. Conditional 16-bit half-word fetch (run_timer/run_mmio approach)
"""

import time

# Minimal RAM implementation for benchmarking
class RAM:
    def __init__(self, size=1024*1024, padding=4):
        self.memory = bytearray(size + padding)
        self.memory32 = memoryview(self.memory).cast("I")  # word view
        self.size = size

    def load_half(self, addr, signed=True):
        val = self.memory[addr] | (self.memory[addr+1] << 8)
        return val if not signed or val < 0x8000 else val - 0x10000

    def load_word(self, addr):  # always unsigned (performance)
        if addr & 0x3 == 0:
            return self.memory32[addr >> 2]  # word aligned
        else:
            return self.memory[addr] | (self.memory[addr+1] << 8) | (self.memory[addr+2] << 16) | (self.memory[addr+3] << 24)

# Create test RAM with some instruction-like data
ram = RAM(size=1024*1024)  # 1MB

# Fill with test data simulating mixed RVC code
# Pattern: mostly 32-bit instructions (bits[1:0] == 0b11), some 16-bit (bits[1:0] != 0b11)
for i in range(0, len(ram.memory), 4):
    if i % 16 == 0:
        # 25% are 16-bit compressed instructions (lower 2 bits != 0b11)
        ram.memory[i] = 0x01  # bits[1:0] = 0b01 (compressed)
        ram.memory[i+1] = 0x00
        ram.memory[i+2] = 0x00
        ram.memory[i+3] = 0x00
    else:
        # 75% are 32-bit instructions (lower 2 bits == 0b11)
        ram.memory[i] = 0x13  # ADDI opcode (bits[1:0] = 0b11)
        ram.memory[i+1] = 0x00
        ram.memory[i+2] = 0x00
        ram.memory[i+3] = 0x00

ITERATIONS = 10_000_000
PC_RANGE = 0x10000  # 64KB range to test (avoid cache effects)

print(f"Benchmarking {ITERATIONS:,} instruction fetches...")
print(f"Testing over {PC_RANGE:,} byte range")
print()

# Test 1: 32-bit word fetch (current run_fast approach)
print("Test 1: Single 32-bit word fetch")
start = time.perf_counter()
pc = 0
for i in range(ITERATIONS):
    inst32 = ram.load_word(pc)
    # Simulate dispatch overhead
    is_32bit = (inst32 & 0x3) == 0x3
    if is_32bit:
        inst = inst32
        size = 4
    else:
        inst = inst32 & 0xFFFF
        size = 2
    pc = (pc + size) & (PC_RANGE - 1)

elapsed1 = time.perf_counter() - start
print(f"  Time: {elapsed1:.3f}s")
print(f"  Rate: {ITERATIONS/elapsed1:,.0f} fetches/sec")
print()

# Test 2: Conditional 16-bit half-word fetch (run_timer/run_mmio approach)
print("Test 2: Conditional 16-bit half-word fetch")
start = time.perf_counter()
pc = 0
for i in range(ITERATIONS):
    inst_low = ram.load_half(pc, signed=False)
    if (inst_low & 0x3) == 0x3:
        # 32-bit instruction: fetch upper 16 bits
        inst_high = ram.load_half(pc + 2, signed=False)
        inst = inst_low | (inst_high << 16)
        size = 4
    else:
        # 16-bit compressed instruction
        inst = inst_low
        size = 2
    pc = (pc + size) & (PC_RANGE - 1)

elapsed2 = time.perf_counter() - start
print(f"  Time: {elapsed2:.3f}s")
print(f"  Rate: {ITERATIONS/elapsed2:,.0f} fetches/sec")
print()

# Test 3: Pure 32-bit word fetch (no dispatch, for reference)
print("Test 3: Pure 32-bit word fetch (no dispatch, baseline)")
start = time.perf_counter()
pc = 0
for i in range(ITERATIONS):
    inst = ram.load_word(pc)
    pc = (pc + 4) & (PC_RANGE - 1)

elapsed3 = time.perf_counter() - start
print(f"  Time: {elapsed3:.3f}s")
print(f"  Rate: {ITERATIONS/elapsed3:,.0f} fetches/sec")
print()

# Results
print("=" * 60)
print("RESULTS:")
print(f"  32-bit word fetch:        {elapsed1:.3f}s  (baseline)")
print(f"  Conditional 16-bit fetch: {elapsed2:.3f}s  ({elapsed2/elapsed1*100:.1f}%)")
print(f"  Pure word fetch:          {elapsed3:.3f}s  ({elapsed3/elapsed1*100:.1f}%)")
print()
print(f"Performance difference: {(elapsed2-elapsed1)/elapsed1*100:+.1f}%")
if elapsed2 > elapsed1:
    print(f"  → Conditional 16-bit fetch is {elapsed2/elapsed1:.2f}x SLOWER")
else:
    print(f"  → Conditional 16-bit fetch is {elapsed1/elapsed2:.2f}x FASTER")
print()

# Correctness consideration
print("=" * 60)
print("CORRECTNESS ANALYSIS:")
print()
print("32-bit word fetch:")
print("  ✓ Simple, fewer memory accesses")
print("  ✓ Safe with 4-byte padding")
print("  ⚠ Reads beyond valid instruction for 16-bit at top-2")
print("  ⚠ Uses padding bytes for 32-bit instruction at top-2")
print()
print("Conditional 16-bit fetch:")
print("  ✓ Spec-compliant: only fetches what's needed")
print("  ✓ Correct for 16-bit instruction at top-2")
print("  ✓ Correct for 32-bit instruction (reads both halves)")
print("  ✗ More memory accesses for 32-bit instructions")
print()
print("Recommendation:")
if elapsed2 / elapsed1 < 1.10:  # Less than 10% slower
    print("  → Conditional fetch is <10% slower: USE IT for correctness!")
elif elapsed2 / elapsed1 < 1.25:  # Less than 25% slower
    print("  → Conditional fetch is <25% slower: Consider using it")
else:
    print("  → Conditional fetch is significantly slower: Keep 32-bit fetch")
    print("     (Document that 32-bit instruction at top-2 is program error)")
