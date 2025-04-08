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

import sys, argparse
from riscv import CPU
import logging

MEMORY_SIZE = 1024 * 1024 # 1MB

def parse_args():
    parser = argparse.ArgumentParser(description="RISC-V Emulator")
    parser.add_argument("executable", help=".elf or .bin file")
    parser.add_argument("--trace", action="store_true", help="Enable symbol-based call tracing")
    parser.add_argument("--regs", action="store_true", help="Print registers at each instruction")
    parser.add_argument("--check", action="store_true", help="Check invariants on each step")
    parser.add_argument("--check-text", action="store_true", help="Ensure text segment is not modified")
    parser.add_argument("--log", help="Path to log file (optional)")
    parser.add_argument("--log-level", default="DEBUG", help="Logging level: DEBUG, INFO, WARNING, ERROR")
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()

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
    cpu = CPU(memory_size=MEMORY_SIZE)

    # Load binary or ELF file
    if args.executable.endswith('.bin'):
        cpu.load_flatbinary(args.executable)
    elif args.executable.endswith('.elf'):
        cpu.load_elf(args.executable, load_symbols=args.trace, text_snapshot=args.check_text)
    else:
        print("Unsupported file format. Please provide a .bin or .elf file.")
        sys.exit(-1)

    # Execution loop
    try:
        while True:
            if args.regs:
                log.debug(f"PC={cpu.pc:08x}, ra={cpu.registers[1]:08x}, sp={cpu.registers[2]:08x}, gp={cpu.registers[3]:08x}, a0={cpu.registers[10]:08x}")
            if args.check:
                cpu.check_invariants()
            if args.check_text and (cpu.text_snapshot is not None):
                assert cpu.memory[cpu.text_start:cpu.text_end] == cpu.text_snapshot, "Text segment has been modified!"
            if args.trace and (cpu.pc in cpu.symbol_dict):
                log.debug(f"PC={cpu.pc:08x}, {cpu.symbol_dict[cpu.pc]}")

            inst = cpu.load_word(cpu.pc)
            continue_exec = cpu.execute(inst)
            if not continue_exec:
                break

    except KeyboardInterrupt:
        print("\nExecution interrupted by user.")
