#!/usr/bin/env python3

import sys
from elftools.elf.elffile import ELFFile
from riscv import CPU, execute

cpu = CPU()

# handle different binary file formats
if sys.argv[1][-4:] == '.bin':
    # Load binary instructions into memory
    with open(sys.argv[1], 'rb') as f:
        binary = f.read()
        cpu.load_binary(binary, addr=0)
        cpu.pc = 0
elif sys.argv[1][-4:] == '.elf':
    # Load ELF file
    with open(sys.argv[1], 'rb') as f:
        elf = ELFFile(f)
        for segment in elf.iter_segments():
            if segment['p_type'] == 'PT_LOAD':
                addr = segment['p_paddr']
                data = segment.data()
                cpu.load_binary(data, addr=addr)
        cpu.pc = elf.header.e_entry
else:
    print("Unsupported file format. Please provide a .bin or .elf file.")
    sys.exit(-1)

# Run execution loop
while True:
    #print(f"PC={cpu.pc:08x}, ra={cpu.registers[1]:08x}, sp={cpu.registers[2]:08x}")
    inst = cpu.load_word(cpu.pc)
    continue_exec = execute(cpu, inst)
    if not continue_exec:
        break
