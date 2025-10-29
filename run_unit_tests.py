#!/usr/bin/env python3
#
# Runs the RV32UI, RV32MI, and RV32UC RISC-V unit tests
#

import sys, os, glob, argparse
from elftools.elf.elffile import ELFFile

from machine import Machine
from cpu import CPU
from ram import SafeRAMOffset

def parse_args():
    parser = argparse.ArgumentParser(description="RISC-V Test Runner")
    parser.add_argument("executable", nargs="?", help="exexutable test file")
    args = parser.parse_args(sys.argv[1:])
    return args

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

# MAIN
if __name__ == '__main__':
    args = parse_args()
    
    # If the path of a test executable is provided on the command line, run *only* that test,
    # otherwise run them all.
    if args.executable is None:
        test_rv32ui_fnames = [fname for fname in glob.glob('riscv-tests/isa/rv32ui-p-*') if not '.dump' in fname]
        test_rv32mi_fnames = [fname for fname in glob.glob('riscv-tests/isa/rv32mi-p-*') if not '.dump' in fname]
        test_rv32uc_fnames = [fname for fname in glob.glob('riscv-tests/isa/rv32uc-p-*') if not '.dump' in fname]
        test_fname_list = test_rv32ui_fnames + test_rv32mi_fnames + test_rv32uc_fnames
    else:
        test_fname_list = [ args.executable ]

    # loop over tests
    for test_fname in test_fname_list:

        # Instantiate CPU + RAM + machine + syscall handler
        ram = SafeRAMOffset(1024*1024, base_addr=0x8000_0000)  # RAM base and entry point at 0x8000_0000
        cpu = CPU(ram)
        machine = Machine(cpu, ram)

        # Load ELF file of test
        machine.load_elf(test_fname)

        # get address of variable (tohost) used to communicate test results
        tohost_addr = get_symbol_address(test_fname, "tohost")
        ram.store_word(tohost_addr, 0xFFFFFFFF)  # store sentinel value

        # RUN
        test_num = 0
        test_regs = {}  # Store register snapshots for each test
        while True:
            # Track which test we're in and save register state when test starts
            current_testnum = cpu.registers[3]  # x3 is gp, used as TESTNUM
            if current_testnum != test_num:
                test_num = current_testnum
                # Save register state at start of each test
                test_regs[test_num] = list(cpu.registers)

            #print ('PC=%08X' % cpu.pc)

            # Check PC alignment before fetch (must be 2-byte aligned with C extension)
            if cpu.pc & 0x1:
                cpu.trap(cause=0, mtval=cpu.pc)  # Instruction address misaligned
                cpu.pc = cpu.next_pc
                if ram.load_word(tohost_addr) != 0xFFFFFFFF:
                    break
                continue

            # Fetch using spec-compliant parcel-based approach
            inst_low = ram.load_half(cpu.pc, signed=False)
            if (inst_low & 0x3) == 0x3:
                # 32-bit instruction: fetch upper 16 bits
                inst_high = ram.load_half(cpu.pc + 2, signed=False)
                inst = inst_low | (inst_high << 16)
            else:
                # 16-bit compressed instruction
                inst = inst_low

            cpu.execute(inst)
            cpu.pc = cpu.next_pc

            # if sentinel value has been overwritten, the test is over
            if ram.load_word(tohost_addr) != 0xFFFFFFFF:
                break

        # Load and check test result
        test_result = ram.load_word(tohost_addr)
        result_str = "PASS" if test_result == 1 else f"FAIL (test #{test_result >> 1})"

        # Debug output for failures
        if test_result != 1:
            failed_test_num = test_result >> 1
            print(f"Test {os.path.basename(test_fname):<30}: {result_str}")
            print(f"  tohost value: 0x{test_result:08X}")
            print(f"  Final PC: 0x{cpu.pc:08X}")
            print(f"  mepc: 0x{cpu.csrs[0x341]:08X}")
            print(f"  mcause: 0x{cpu.csrs[0x342]:08X}")
            print(f"  mtval: 0x{cpu.csrs[0x343]:08X}")

            # Show final register state for specific failing tests
            if 'rvc' in test_fname and failed_test_num == 12:
                print(f"  Final s0 (x8): 0x{cpu.registers[8]:08X} (expected: 0x000fffe1)")
                print(f"  Final x7: 0x{cpu.registers[7]:08X}")
            elif 'ma_fetch' in test_fname and failed_test_num == 4:
                print(f"  Final t0 (x5): 0x{cpu.registers[5]:08X}")
                print(f"  Final t1 (x6): 0x{cpu.registers[6]:08X}")
        else:
            print(f"Test {os.path.basename(test_fname):<30}: {result_str}")
