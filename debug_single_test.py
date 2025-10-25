#!/usr/bin/env python3
"""
Debug a single RISC-V test with detailed output
"""

import sys
from elftools.elf.elffile import ELFFile
from machine import Machine
from cpu import CPU
from ram import SafeRAMOffset

def get_symbol_address(filename, symbol_name):
    with open(filename, 'rb') as f:
        elf = ELFFile(f)
        symtab = elf.get_section_by_name('.symtab')
        if symtab is None:
            raise Exception("No symbol table found")
        for symbol in symtab.iter_symbols():
            if symbol.name == symbol_name:
                return symbol.entry['st_value']
    raise Exception(f"Symbol {symbol_name} not found")

if len(sys.argv) < 2:
    print("Usage: python3 debug_single_test.py <test_binary>")
    print("Example: python3 debug_single_test.py riscv-tests/isa/rv32mi-p-ma_fetch")
    sys.exit(1)

test_fname = sys.argv[1]
verbose = '--verbose' in sys.argv

print(f"Debugging: {test_fname}")
print("=" * 70)

# Setup
ram = SafeRAMOffset(1024*1024, base_addr=0x8000_0000)
cpu = CPU(ram)
machine = Machine(cpu, ram)

# Load test
machine.load_elf(test_fname)
tohost_addr = get_symbol_address(test_fname, "tohost")
ram.store_word(tohost_addr, 0xFFFFFFFF)

print(f"Entry point: 0x{cpu.pc:08X}")
print(f"tohost addr: 0x{tohost_addr:08X}")
print()

# Track execution
instr_count = 0
max_instr = 100000  # Safety limit

try:
    while True:
        # Check if test finished
        if ram.load_word(tohost_addr) != 0xFFFFFFFF:
            break

        if verbose and instr_count < 100:  # Only show first 100 instructions
            print(f"#{instr_count:05d} PC=0x{cpu.pc:08X}", end="")

        # Check PC alignment
        if cpu.pc & 0x1:
            if verbose and instr_count < 100:
                print(f" -> MISALIGNED PC TRAP")
            cpu.trap(cause=0, mtval=cpu.pc)
            cpu.pc = cpu.next_pc
            instr_count += 1
            continue

        # Fetch instruction
        inst_low = ram.load_half(cpu.pc, signed=False)
        if (inst_low & 0x3) == 0x3:
            inst_high = ram.load_half(cpu.pc + 2, signed=False)
            inst = inst_low | (inst_high << 16)
            inst_size = 4
        else:
            inst = inst_low
            inst_size = 2

        if verbose and instr_count < 100:
            print(f" inst=0x{inst:08X if inst_size==4 else inst:04X} ({inst_size}B)")

        # Execute
        cpu.execute(inst)
        cpu.pc = cpu.next_pc

        instr_count += 1
        if instr_count >= max_instr:
            print(f"\n✗ Exceeded {max_instr} instructions - infinite loop?")
            break

except KeyboardInterrupt:
    print("\n✗ Interrupted by user")
except Exception as e:
    print(f"\n✗ Exception: {e}")
    import traceback
    traceback.print_exc()

# Check result
test_result = ram.load_word(tohost_addr)
test_case = test_result >> 1

print()
print("=" * 70)
print(f"Instructions executed: {instr_count}")
print(f"Final PC: 0x{cpu.pc:08X}")
print(f"tohost value: 0x{test_result:08X}")

if test_result == 1:
    print("✓ Test PASSED")
elif test_result == 0xFFFFFFFF:
    print("✗ Test did not complete (tohost not written)")
else:
    print(f"✗ Test FAILED at test case #{test_case}")
    print(f"  (tohost = {test_result} = {test_result:#x})")
    print()
    print("To debug:")
    print(f"  1. Look at test case #{test_case} in the test source")
    print(f"  2. Run with --verbose to see instruction trace")
    print(f"  3. Add breakpoints around test case #{test_case}")
