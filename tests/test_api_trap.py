#!/usr/bin/env python3
# Example of programmatic access to the RISC-V Python emulator

from machine import Machine
from cpu import CPU
from ram import RAM

# instantiate CPU / RAM / machine
ram = RAM(1024 * 1024) # 1 MB of RAM
cpu = CPU(ram)
machine = Machine(cpu, ram)

# Load flat binary executable into memory
machine.load_flatbinary("prebuilt/test_bare1.bin")  # flat binary from the prebuilt examples
cpu.pc = 0x00000000
cpu.csrs[0x305] = 0xDEAD0000 # set MTVEC address

# Run the program
while True:
    inst = ram.load_word(cpu.pc)  # fetch
    cpu.execute(inst)             # decode and execute
    cpu.pc = cpu.next_pc          # update program counter

    # When pc == 0xDEAD0000 we know a trap (the ECALL in start_bare.S) has occurred and we stop execution.
    if cpu.pc == 0xDEAD0000:
        break

print ("Result =", cpu.registers[10])  # Print the return value (value of register a0/x10, should be 4950)

cpu.print_registers()
