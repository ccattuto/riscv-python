#!/usr/bin/env python3
"""
Diagnostic script to check test status
"""
import os
import glob

print("RISC-V Test Diagnostic")
print("=" * 70)

# Check for test sources
print("\n1. Test sources (assembly files):")
rv32ui_sources = glob.glob('riscv-tests/isa/rv32ui/*.S')
rv32mi_sources = glob.glob('riscv-tests/isa/rv32mi/*.S')
rv32uc_sources = glob.glob('riscv-tests/isa/rv32uc/*.S')
print(f"   rv32ui sources: {len(rv32ui_sources)}")
print(f"   rv32mi sources: {len(rv32mi_sources)}")
print(f"   rv32uc sources: {len(rv32uc_sources)}")

# Check for test binaries
print("\n2. Test binaries:")
rv32ui_bins = glob.glob('riscv-tests/isa/rv32ui-p-*')
rv32mi_bins = glob.glob('riscv-tests/isa/rv32mi-p-*')
rv32uc_bins = glob.glob('riscv-tests/isa/rv32uc-p-*')

# Filter out .dump files
rv32ui_bins = [f for f in rv32ui_bins if not f.endswith('.dump')]
rv32mi_bins = [f for f in rv32mi_bins if not f.endswith('.dump')]
rv32uc_bins = [f for f in rv32uc_bins if not f.endswith('.dump')]

print(f"   rv32ui binaries: {len(rv32ui_bins)}")
print(f"   rv32mi binaries: {len(rv32mi_bins)}")
print(f"   rv32uc binaries: {len(rv32uc_bins)}")

if rv32ui_bins:
    print(f"   Example: {rv32ui_bins[0]}")

# Check specifically for the failing tests
print("\n3. Specific test files:")
tests_to_check = [
    'riscv-tests/isa/rv32mi-p-ma_fetch',
    'riscv-tests/isa/rv32mi-p-sbreak',
    'riscv-tests/isa/rv32uc-p-rvc'
]

for test in tests_to_check:
    exists = os.path.exists(test)
    is_file = os.path.isfile(test) if exists else False
    size = os.path.getsize(test) if is_file else 0
    print(f"   {test}")
    print(f"      Exists: {exists}, Is file: {is_file}, Size: {size} bytes")

# Check for toolchain
print("\n4. RISC-V toolchain:")
import subprocess
compilers = ['riscv32-unknown-elf-gcc', 'riscv64-unknown-elf-gcc', 'riscv32-unknown-linux-gnu-gcc']
for compiler in compilers:
    try:
        result = subprocess.run([compiler, '--version'], capture_output=True, timeout=1)
        if result.returncode == 0:
            print(f"   ✓ {compiler} found")
        else:
            print(f"   ✗ {compiler} not working")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print(f"   ✗ {compiler} not found")

print("\n5. Instructions to build tests:")
print("   cd riscv-tests")
print("   autoconf")
print("   ./configure --prefix=$PWD/install")
print("   make")
print("   cd ..")

print("\n" + "=" * 70)
