#!/usr/bin/env python3
"""
Benchmark: Function call overhead in execution loop

Compares:
1. Inline execution (origin/main style)
2. Wrapper + separate function (current style)
"""

import time

class RAM:
    def __init__(self, size=1024*1024, padding=4):
        self.memory = bytearray(size + padding)
        self.memory32 = memoryview(self.memory).cast("I")
        self.size = size

    def load_half(self, addr, signed=False):
        val = self.memory[addr] | (self.memory[addr+1] << 8)
        return val

    def load_word(self, addr):
        if addr & 0x3 == 0:
            return self.memory32[addr >> 2]
        else:
            return self.memory[addr] | (self.memory[addr+1] << 8) | (self.memory[addr+2] << 16) | (self.memory[addr+3] << 24)

ram = RAM(size=1024*1024)

# Fill with RV32I instructions (all 32-bit)
for i in range(0, len(ram.memory), 4):
    ram.memory[i] = 0x13  # ADDI opcode (bits[1:0] = 0b11)

ITERATIONS = 5_000_000
PC_RANGE = 0x10000

print(f"Benchmarking {ITERATIONS:,} instruction executions (pure RV32I)")
print()

# Simulate instruction decode cache
decode_cache = {}

def decode_inst(inst):
    """Simulate instruction decoding"""
    try:
        return decode_cache[inst >> 2]
    except KeyError:
        opcode = inst & 0x7F
        rd = (inst >> 7) & 0x1F
        funct3 = (inst >> 12) & 0x7
        result = (opcode, rd, funct3)
        decode_cache[inst >> 2] = result
        return result

# Test 1: Origin/main style - inline execution
print("Test 1: Inline execution (origin/main style)")
start = time.perf_counter()
pc = 0
for i in range(ITERATIONS):
    # Fetch
    inst = ram.load_word(pc)

    # Decode and execute (inline)
    opcode, rd, funct3 = decode_inst(inst)

    # Simulate execution (minimal work)
    result = opcode + rd + funct3

    pc = (pc + 4) & (PC_RANGE - 1)

elapsed1 = time.perf_counter() - start
print(f"  Time: {elapsed1:.3f}s")
print(f"  Rate: {ITERATIONS/elapsed1:,.0f} inst/sec")
print()

# Test 2: Current style - wrapper + execute_32()
def execute_32_separate(inst):
    """Separate function call for 32-bit execution"""
    opcode, rd, funct3 = decode_inst(inst)
    return opcode + rd + funct3

print("Test 2: Wrapper + separate execute_32 (current style, word fetch)")
start = time.perf_counter()
pc = 0
inst_size = 4
for i in range(ITERATIONS):
    # Fetch
    inst = ram.load_word(pc)

    # Execute via separate function
    result = execute_32_separate(inst)

    pc = (pc + 4) & (PC_RANGE - 1)

elapsed2 = time.perf_counter() - start
print(f"  Time: {elapsed2:.3f}s")
print(f"  Rate: {ITERATIONS/elapsed2:,.0f} inst/sec")
print(f"  Overhead: {(elapsed2/elapsed1-1)*100:+.1f}%")
print()

# Test 3: Current style with 16-bit conditional fetch
print("Test 3: Conditional 16-bit fetch + separate execute_32")
start = time.perf_counter()
pc = 0
inst_size = 4
for i in range(ITERATIONS):
    # Conditional 16-bit fetch
    inst_low = ram.load_half(pc)
    if (inst_low & 0x3) == 0x3:
        inst_high = ram.load_half(pc + 2)
        inst = inst_low | (inst_high << 16)
    else:
        inst = inst_low

    # Execute via separate function
    result = execute_32_separate(inst)

    pc = (pc + 4) & (PC_RANGE - 1)

elapsed3 = time.perf_counter() - start
print(f"  Time: {elapsed3:.3f}s")
print(f"  Rate: {ITERATIONS/elapsed3:,.0f} inst/sec")
print(f"  Overhead: {(elapsed3/elapsed1-1)*100:+.1f}%")
print()

print("=" * 60)
print("RESULTS:")
print(f"  Inline execution:                {elapsed1:.3f}s  (baseline)")
print(f"  Separate function (word fetch):  {elapsed2:.3f}s  ({(elapsed2/elapsed1-1)*100:+.1f}%)")
print(f"  Separate + 16-bit fetch:         {elapsed3:.3f}s  ({(elapsed3/elapsed1-1)*100:+.1f}%)")
print()
print("Breakdown:")
print(f"  Function call overhead:   {(elapsed2/elapsed1-1)*100:+.1f}%")
print(f"  16-bit fetch overhead:    {(elapsed3/elapsed2-1)*100:+.1f}%")
print(f"  Total overhead:           {(elapsed3/elapsed1-1)*100:+.1f}%")
