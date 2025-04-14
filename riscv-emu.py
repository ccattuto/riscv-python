#!/usr/bin/env python3

# Copyright (2025) Ciro Cattuto <ciro.cattuto@gmail.com>
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

import sys, os, argparse
import tty, termios
import logging

from machine import Machine, MachineError
from cpu import CPU
from ram import RAM, SafeRAM

MEMORY_SIZE = 1024 * 1024  # 1 Mb

def parse_args():
    if "--" in sys.argv:
        split_index = sys.argv.index("--")
        emulator_args = sys.argv[1:split_index]
        program_args = sys.argv[split_index + 1:]
    else:
        emulator_args = sys.argv[1:]
        program_args = []

    parser = argparse.ArgumentParser(
        description="RISC-V Emulator",
        epilog=("For ELF executables, arguments after '--' are passed to the emulated program as argv[], "
                "with argv[0] set to the basename of the executable.") )
    parser.add_argument("executable", help=".elf or .bin file")
    parser.add_argument("--regs", action="store_true", help="Print registers at each instruction")
    parser.add_argument("--check-inv", action="store_true", help="Check invariants on each step")
    parser.add_argument("--check-ram", action="store_true", help="Check memory accesses")
    parser.add_argument("--check-text", action="store_true", help="Ensure text segment is not modified")
    parser.add_argument("--check-all", action="store_true", help="Enable all checks")
    parser.add_argument("--trace", action="store_true", help="Enable symbol-based call tracing")
    parser.add_argument("--syscalls", action="store_true", help="Enable Newlib syscall tracing")
    parser.add_argument("--raw-tty", action="store_true", help="Raw terminal mode")
    parser.add_argument("--log", help="Path to log file (optional)")
    parser.add_argument("--log-level", default="DEBUG", help="Logging level: DEBUG, INFO, WARNING, ERROR")

    args = parser.parse_args(emulator_args)
    args.program_args = [os.path.basename(args.executable)] + program_args
    return args

# MAIN
if __name__ == '__main__':
    args = parse_args()
    if args.check_all:
        args.check_inv = True
        args.check_ram = True
        args.check_text = True

    log = logging.getLogger("riscv-emu")
    log.setLevel(logging.DEBUG)

    if args.log:
        # Log to file only
        file_handler = logging.FileHandler(args.log)
        file_handler.setLevel(getattr(logging, args.log_level.upper(), logging.DEBUG))
        file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
        log.addHandler(file_handler)
    else:
        # Log to terminal
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
        log.addHandler(console_handler)
    
    # Instantiate CPU + RAM
    ram = RAM(MEMORY_SIZE, logger=log) if not args.check_ram else SafeRAM(MEMORY_SIZE, logger=log)
    cpu = CPU(ram, logger=log)
    machine = Machine(cpu, ram, logger=log, raw_tty=args.raw_tty, trace_syscalls=args.syscalls)
    cpu.set_ecall_handler(machine.handle_ecall)  # Set syscall handler

    # Load binary or ELF file
    if args.executable.endswith('.bin'):
        machine.load_flatbinary(args.executable)
    elif args.executable.endswith('.elf'):
        machine.load_elf(args.executable, load_symbols=args.trace, check_text=args.check_text)
        if machine.heap_end is not None and args.program_args:
            machine.setup_argv(args.program_args)
    else:
        print("Unsupported file format. Please provide a .bin or .elf file.")
        sys.exit(-1)

    # If requested, set raw terminal mode
    if args.raw_tty:
        fd = sys.stdin.fileno()
        tty_old_settings = termios.tcgetattr(fd)
        tty.setraw(fd)

    # Execution loop
    try:
        while True:
            if args.regs:
                log.debug(f"REGS: PC={cpu.pc:08x}, ra={cpu.registers[1]:08x}, sp={cpu.registers[2]:08x}, gp={cpu.registers[3]:08x}, a0={cpu.registers[10]:08x}")
            if args.check_inv:
                machine.check_invariants()
            if args.trace and (cpu.pc in machine.symbol_dict):
                log.debug(f"FUNC {machine.symbol_dict[cpu.pc]}, PC={cpu.pc:08x}")

            inst = machine.ram.load_word(cpu.pc)
            continue_exec = machine.cpu.execute(inst)
            if not continue_exec:
                break

    except KeyboardInterrupt:
        if args.raw_tty: # Restore terminal settings
            termios.tcsetattr(fd, termios.TCSADRAIN, tty_old_settings)
        print("\nExecution interrupted by user.")

    except MachineError as e:
        if args.raw_tty:
            termios.tcsetattr(fd, termios.TCSADRAIN, tty_old_settings)
        print(f"\nEMULATOR ERROR [{type(e).__name__}] at PC=0x{cpu.pc:08x}: {e}")
        cpu.print_registers()
        sys.exit(1)

    except Exception:
        if args.raw_tty:
            termios.tcsetattr(fd, termios.TCSADRAIN, tty_old_settings)
        print()
        raise
    
    finally:
        if args.raw_tty:
            termios.tcsetattr(fd, termios.TCSADRAIN, tty_old_settings)
        print()
