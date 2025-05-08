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
import logging, time

from machine import Machine, MachineError, SetupError, ExecutionTerminated
from cpu import CPU
from ram import RAM, SafeRAM, RAM_MMIO, SafeRAM_MMIO
from syscalls import SyscallHandler
from peripherals import PtyUART, MMIOBlockDevice

LOG_COLORS = {
    logging.DEBUG: "\033[36m",      # Cyan
    logging.INFO: "\033[32m",       # Green
    logging.WARNING: "\033[33m",    # Yellow
    logging.ERROR: "\033[31m"       # Red
}
RESET_COLOR = "\033[0m"

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
    parser.add_argument("--regs", metavar="REGS", default=None, help="Print selected registers at each instruction")
    parser.add_argument("--trace", action="store_true", help="Enable symbol-based call tracing")
    parser.add_argument("--syscalls", action="store_true", help="Enable Newlib syscall tracing")
    parser.add_argument("--traps", action="store_true", help="Enable trap tracing")
    parser.add_argument("--check-inv", action="store_true", help="Check invariants on each step")
    parser.add_argument("--check-ram", action="store_true", help="Check memory accesses")
    parser.add_argument("--check-text", action="store_true", help="Ensure text segment is not modified")
    parser.add_argument("--check-all", action="store_true", help="Enable all checks")
    parser.add_argument("--start-checks", metavar="WHEN", default="auto", help="Condition to enable checks (auto, early, main, first-call, 0xADDR)")
    parser.add_argument("--init-regs", metavar="VALUE", default="zero", help='Initial register state (zero, random, 0xDEADBEEF)')
    parser.add_argument('--init-ram', metavar='PATTERN', default='zero', help='Initialize RAM with pattern (zero, random, addr, 0xAA)')
    parser.add_argument('--ram-size', metavar="KBS", type=int, default=1024, help='Emulated RAM size (kB, default 1024)')
    parser.add_argument('--timer', action="store_true", help='Enable machine timer')
    parser.add_argument('--uart', action="store_true", help='Enable UART')
    parser.add_argument('--blkdev', metavar="PATH", default=None, help='Enable MMIO block device')
    parser.add_argument('--blkdev-size', metavar="NUM", type=int, default=1024, help='Emulated RAM size (512-byte blocks, default 1024)')
    parser.add_argument("--raw-tty", action="store_true", help="Raw terminal mode")
    parser.add_argument("--no-color", action="store_false", help="Remove ANSI colors in terminal output")
    parser.add_argument("--log", help="Path to log file")
    parser.add_argument("--log-level", default="DEBUG", help="Logging level: DEBUG, INFO, WARNING, ERROR")

    args = parser.parse_args(emulator_args)
    args.program_args = [os.path.basename(args.executable)] + program_args
    return args

class RawTTYStreamHandler(logging.StreamHandler):
    def __init__(self, stream=None, raw_tty=False):
        super().__init__(stream)
        self.raw_tty = raw_tty

    def emit(self, record):
        try:
            msg = self.format(record)
            if self.raw_tty:
                msg = msg.replace('\n', '\r\n')
            stream = self.stream
            stream.write(msg)
            stream.write('\r\n' if self.raw_tty else '\n')
            self.flush()
        except Exception:
            self.handleError(record)

class RelativeTimeFormatter(logging.Formatter):
    def __init__(self, stream=None, t0=0):
        super().__init__(stream)
        self.t0 = t0
    def formatTime(self, record, datefmt=None):
        elapsed = record.created - self.t0
        return f"{elapsed:07.3f}s"

class ColorFormatter(RelativeTimeFormatter):
    def __init__(self, fmt, t0=0, use_color=True):
        super().__init__(fmt, t0)
        self.use_color = use_color

    def format(self, record):
        message = super().format(record)
        if self.use_color and record.levelno in LOG_COLORS:
            color = LOG_COLORS[record.levelno]
            return f"{color}{message}{RESET_COLOR}"
        return message

# helper function to restore terminal from raw mode
def restore_terminal(fd, settings):
    termios.tcsetattr(fd, termios.TCSADRAIN, settings)


# MAIN
if __name__ == '__main__':

    args = parse_args()

    use_mmio = False
    if args.check_all:
        args.check_inv = True
        args.check_ram = True
        args.check_text = True
    if args.uart:
        args.check_ram = True
        use_mmio = True
    if args.blkdev is not None:
        args.check_ram = True
        use_mmio = True

    MEMORY_SIZE = 1024 * args.ram_size  # (default 1 Mb)

    log = logging.getLogger("riscv-emu")
    log.setLevel(logging.DEBUG)

    if args.log:
        # Log to file only
        file_handler = logging.FileHandler(args.log)
        file_handler.setLevel(getattr(logging, args.log_level.upper(), logging.DEBUG))
        file_handler.setFormatter(RelativeTimeFormatter('%(asctime)s [%(levelname)s] %(message)s', t0=time.time()))
        log.addHandler(file_handler)
    else:
        # Log to terminal (handle both raw and "cooked" terminal modes)
        is_tty = sys.stdout.isatty()
        console_handler = RawTTYStreamHandler(raw_tty=args.raw_tty)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(ColorFormatter('%(asctime)s [%(levelname)s] %(message)s', t0=time.time(), use_color=is_tty and args.no_color))
        log.addHandler(console_handler)
    
    # Instantiate CPU + RAM  + machine + peripherals + syscall handler

    # Select RAM implementation
    if not use_mmio and not args.check_ram:
        ram = RAM(MEMORY_SIZE, init=args.init_ram, logger=log)
    elif use_mmio and not args.check_ram:
        ram = RAM_MMIO(MEMORY_SIZE, init=args.init_ram, logger=log)
    elif not use_mmio and args.check_ram:
        ram = SafeRAM(MEMORY_SIZE, init=args.init_ram, logger=log)
    else:
        ram = SafeRAM_MMIO(MEMORY_SIZE, init=args.init_ram, logger=log)

    # CPU
    cpu = CPU(ram, init_regs=args.init_regs, logger=log, trace_traps=args.traps)

    # System architecture
    machine = Machine(cpu, ram, timer=args.timer, mmio=use_mmio, logger=log,
                      trace=args.trace, regs=args.regs, check_inv=args.check_inv, start_checks=args.start_checks)
    
    # MMIO peripherals
    if args.uart:  # create and register UART peripheral
        uart = PtyUART(logger=log)
        ram.register_peripheral(uart)
        machine.register_peripheral(uart)

    if args.blkdev:  # create and register block device peripheral
        blkdev = MMIOBlockDevice(args.blkdev, ram, size=args.blkdev_size, logger=log)
        ram.register_peripheral(blkdev)
        machine.register_peripheral(blkdev)

    # Create and register syscall handler
    syscall_handler = SyscallHandler(cpu, ram, machine, logger=log, raw_tty=args.raw_tty, trace_syscalls=args.syscalls)
    cpu.set_ecall_handler(syscall_handler.handle)  # Set syscall handler

    # Load binary or ELF file
    try:
        if args.executable.endswith('.bin'):
            machine.load_flatbinary(args.executable)
        elif args.executable.endswith('.elf'):
            machine.load_elf(args.executable, load_symbols=args.trace, check_text=args.check_text)
            if machine.heap_end is not None and args.program_args:  # pass command-line arguments
                machine.setup_argv(args.program_args)
        else:
            log.error("Unsupported file format. Please provide a .bin or .elf file")
            sys.exit(1)
    except MachineError as e:
        log.error(f"EMULATOR ERROR ({type(e).__name__}): {e}")
        sys.exit(1)

    # If requested, set raw terminal mode
    if args.raw_tty:
        stdin_fd = sys.stdin.fileno()
        tty_old_settings = termios.tcgetattr(stdin_fd)
        tty.setraw(stdin_fd)

    # RUN
    try:
        machine.run()

    except KeyboardInterrupt:
        if args.raw_tty: # Restore terminal settings
            restore_terminal(stdin_fd, tty_old_settings)
        print()
        log.info(f"Execution interrupted by user at PC=0x{cpu.pc:08X}")

    except MachineError as e:
        if args.raw_tty:
            restore_terminal(stdin_fd, tty_old_settings)
            print()
        if type(e) == ExecutionTerminated:
            log.info(f"Execution terminated: {e}")
            sys.exit(0)
        else:
            log.error(f"EMULATOR ERROR ({type(e).__name__}) at PC=0x{cpu.pc:08X}: {e}")
            if type(e) != SetupError:
                cpu.print_registers()
            sys.exit(1)

    except Exception:
        if args.raw_tty:
            restore_terminal(stdin_fd, tty_old_settings)
        print()
        raise
    
    finally:
        if args.raw_tty:
            restore_terminal(stdin_fd, tty_old_settings)
        print()
