#!/usr/bin/env python3
# Example of programmatic access to the RISC-V Python emulator

from cpu import CPU
from ram import RAM

# instantiate CPU / RAM / machine
ram = RAM(1024)
cpu = CPU(ram)

# Load program into RAM
# (a simple RISC-V program that sums integers from 1 to 100 and returns the result in t0)
ram.store_word(0x00000000, 0x00000293)  # li t0, 0
ram.store_word(0x00000004, 0x00100313)  # li t1, 1
ram.store_word(0x00000008, 0x06400393)  # li t2, 100
ram.store_word(0x0000000c, 0x006282b3)  # <loop> add t0, t0, t1
ram.store_word(0x00000010, 0x00130313)  # addi t1, t1, 1
ram.store_word(0x00000014, 0xfe63dce3)  # bge t2, t1, c <loop>
ram.store_word(0x00000018, 0x00100073)  # ebreak

cpu.pc = 0x00000000

# Run the program
while True:
    inst = ram.load_word(cpu.pc)  # fetch
    cpu.execute(inst)             # decode and execute
    cpu.pc = cpu.next_pc          # update program counter

    # Print pc, t1, and t0 registers
    print (f"pc={cpu.pc:08X}, t1={cpu.registers[6]}, t0={cpu.registers[5]}")

    # When pc == 0x00000018 we know the program has reached the end (we don't execute the ebreak)
    if cpu.pc == 0x00000018:
        break

print ("Result =", cpu.registers[5])  # Print the value in register t0/x5 (should be 5050)
