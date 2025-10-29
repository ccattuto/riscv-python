#!/usr/bin/env python3
"""
Performance test to ensure decode cache optimization is working
"""

import time
from cpu import CPU
from ram import SafeRAMOffset

# Create CPU and RAM
ram = SafeRAMOffset(64*1024, base_addr=0x8000_0000)
cpu = CPU(ram)

# Write a sequence of C.ADDI instructions
# C.ADDI x10, x10, 1  (0x0505)
for i in range(1000):
    ram.store_half(0x8000_0000 + i*2, 0x0505)

cpu.pc = 0x8000_0000
cpu.next_pc = 0x8000_0000

# Warm up cache
for _ in range(100):
    inst = ram.load_half(cpu.pc, signed=False)
    cpu.execute(inst)
    cpu.pc = cpu.next_pc

# Reset for actual test
cpu.registers[10] = 0
cpu.pc = 0x8000_0000
cpu.next_pc = 0x8000_0000

# Time 1,000 iterations (we have 1000 instructions written)
iterations = 1_000
start = time.time()

for _ in range(iterations):
    inst = ram.load_half(cpu.pc, signed=False)
    cpu.execute(inst)
    cpu.pc = cpu.next_pc

elapsed = time.time() - start

print(f"Executed {iterations} compressed instructions in {elapsed:.4f}s")
print(f"Rate: {iterations/elapsed:.0f} inst/sec")
print(f"Average: {elapsed/iterations*1e6:.2f} µs/inst")
print(f"\nFinal register a0: {cpu.registers[10]}")
print(f"Cache size: {len(cpu.decode_cache)} entries")
print(f"\nNote: All instructions are identical, so cache should have 1 entry")
print(f"      This tests the cache hit path performance")
