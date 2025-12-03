# 🐍 RISC-V Emulator in Python (RV32IMAC, machine mode, Newlib support)

This is a simple and readable **RISC-V RV32IMAC emulator** written in pure Python. It supports machine mode, multiply/divide instructions (M extension), atomic instructions (A extension), compressed instructions (C extension), and can run programs compiled with **Newlib** or **Newlib-nano**. It is designed for educational use, experimentation, and portability — not for high performance or full system emulation.

## ✅ Features

- **Implements the full RV32I base integer ISA** with the **M extension** (multiply and divide instructions) and the **A extension** (atomic memory operations)
- **Implements the C extension** (compressed instructions), switchable at run time
- **Implements all RV32MI machine-mode instructions and trap mechanisms**, including synchronous traps (`ecall`, `ebreak`, illegal instruction trap), asynchronous traps (machine timer interrupt), `mret`, and the **Zicsr (Control Status Registers) extension** and registers (`mstatus`, `mepc`, `mtvec`, `mcause`, `mscratch`, ...)
- **Supports loading ELF and flat binary formats**
- **Supports terminal I/O**, both "cooked" and raw
- **Provides most of the system calls needed by [Newlib](https://en.wikipedia.org/wiki/Newlib)**: `_write`, `_read`, `_exit`, **dynamic memory allocation** (`_sbrk`), **file I/O** (`_open`, `_close`, `_fstat`, `_lseek`, ...)
- **Supports argc/argv program arguments**
- **Supports memory-mapped IO** and provides a **UART peripheral** using a pseudo-terminal, and a **memory-mapped block device** backed by an image file
- **Passes all `rv32ui`, `rv32mi`, `rv32um`, `rv32ua`, and `rv32uc` unit tests** provided by [RISC-V International](https://github.com/riscv-software-src/riscv-tests)
- **Supports logging** of register values, function calls, system calls, traps, invalid memory accesses, and violations of invariants
- **GDB remote debugging support** via GDB Remote Serial Protocol (RSP) with breakpoints, single-stepping, register/memory inspection
- Runs [MicroPython](https://micropython.org/), [CircuitPython](https://circuitpython.org/) with emulated peripherals, and [FreeRTOS](https://www.freertos.org/) with preemptive multitasking
- **Browser-based emulation** via [Pyodide](https://pyodide.org/), try it [here](https://ccattuto.github.io/riscv-python/)
- Self-contained, modular, extensible codebase. Provides a **Python API** enabling users to control execution, inspect state, and script complex tests directly in Python.

## 🔧 Requirements

- Python 3.8+
- `pyelftools` for ELF parsing
- [RISC-V GNU Compiler Toolchain](https://github.com/riscv-collab/riscv-gnu-toolchain) (for building examples or compiling your own code)

```bash
pip install -r requirements.txt
```

## File Structure

```
├── riscv-emu.py               # Emulator
├── cpu.py                     # CPU emulation logic
├── rvc.py                     # RVC logic
├── ram.py                     # RAM emulation logic
├── machine.py                 # Host logic (executable loading, invariants check)
├── peripherals.py             # Peripherals (UART, block device)
├── syscalls.py                # System calls and terminal I/O
├── gdbstub.py                 # GDB Remote Serial Protocol implementation
├── Makefile                   # Builds ELF/binary targets
├── start_bare.S               # Minimal startup code
├── start_newlib.S             # Startup code for Newlib-nano
├── syscalls_newlib.S          # Syscall stubs for Newlib-nano
├── linker_bare.ld             # Simple linker script, no heap support
├── linker_newlib.ld           # Linker script supporting Newlib-nano
├── riscv-py.h                 # Emulator macros for user programs
├── tests/README.md            # Documentation for example programs
├── tests/test_asm*.S          # Example assembly programs
├── tests/test_bare*.c         # Example C programs without Newlib support
├── tests/test_newlib*.c       # Example C programs with Newlib-nano support
├── tests/test_peripheral*.c   # Example C programs using emulated peripherals
├── tests/test_api*.py         # Examples of programmatic control of the emulator in Python
├── build/                     # Executable and binaries
├── prebuilt/                  # Pre-built examples
├── run_unit_tests.py          # Runs RISC-V unit tests (RV32UI, RV32MI, RV32UM, RV32UA, and RV32UC)
├── riscv-tests/               # Git submodule with RISC-V unit tests
├── advanced/freertos/         # FreeRTOS port
├── advanced/micropython/      # MicroPython port
├── advanced/circuitpython/    # CircuitPython port
├── advanced/coremark/         # CoreMark port
├── advanced/webapp/           # Browser-based port powered by Pyodide
└── README.md                  # You're here!
```

## 🚀 Usage

### ▶️ Command-Line Options

`riscv-emu.py` accepts the following options:

| Option                  | Description                                                                 |
|-------------------------|-----------------------------------------------------------------------------|
| `--rvc`                 | Enable RVC support (compressed instructions)                                |
| `--regs REGS`           | Print selected registers at each instruction                                |
| `--trace`               | Log the names of functions traversed during execution                       |
| `--syscalls`            | Log Newlib syscalls                                                         |
| `--traps`               | Enable trap tracing                                                         |
| `--check-inv`           | Enable runtime invariant checks on stack/heap alignment and boundaries      |
| `--check-ram`           | Check validity of memory accesses                                           |
| `--check-text`          | Ensure the `.text` segment remains unmodified during execution              |
| `--check-all`           | Enable all checks                                                           |
| `--start-checks WHEN`   | Condition to enable checks (auto, early, main, first-call, 0xADDR)          |
| `--init-regs VALUE`     | Initial register state (zero, random, 0xDEADBEEF)                           |
| `--init-ram PATTERN`    | Initialize RAM with pattern (zero, random, addr, 0xAA)                      |
| `--ram-size KBS`        | Emulated RAM size (kB, default 1024)                                        |
| `--timer {csr,mmio}`    | Enable machine timer                                                        |
| `--uart`                | Enable PTY UART                                                             |
| `--blkdev PATH`         | Enable MMIO block device                                                    |
| `--blkdev-size NUM`     | Block device size in 512-byte blocks (default 1024)                         |
| `--raw-tty`             | Enable raw terminal mode                                                    |
| `--no-color`            | Remove ANSI colors in debugging output                                      |
| `--log LOG_FILE`        | Log debug information to file `LOG_FILE`                                    |
| `--gdb`                 | Enable GDB remote debugging (integrates with all other features)            |
| `--gdb-port PORT`       | GDB server port (default: 1234)                                             |
| `--gdb-host HOST`       | GDB server host (default: localhost)                                        |
| `--help`                | Show usage help and available options                                       |

### Compiling Examples
```
make all
```

The Makefile supports building with different RISC-V extensions, e.g., to build with rv32iac_zicsr (RV32IMAC):
```
make RVM=1 RVA=1 RVC=1 all
```

If you just want to **test the emulator without installing a RISC-V compiler**, you will find pre-built binaries in `prebuilt/`.

To build the examples under `advanced/` (MicroPython, FreeRTOS, ...) you will need to initialize the submodules:
```
git submodule update --init --recursive
```

### ▶️ Running Programs

Assembly examples (starts at PC=0):
```
./riscv-emu.py build/test_asm1.bin
```

Bare C examples (starts at PC=0, `_start` in `start_bare.S`):
```
./riscv-emu.py build/test_bare1.bin
```
or
```
./riscv-emu.py build/test_bare1.elf
```

Newlib C examples:
```
./riscv-emu.py build/test_newlib_mandelbrot.elf

                        .................................
                  .............................................
              .....................................................
           ...........................................................
        ..........................::::::.................................
      .....................::::::::::===@:::::.............................
    ...................:::::::::::=++@@++=:::::::............................
   ................:::::::::*+===++++@@+=+=+=::=:::...........................
  ............::::::::::::===@@@@@@@@@@@@@@@@@@+::::...........................
 ....::::::::::+==========*@@@@@@@@@@@@@@@@@@@@@@+:::...........................
 :::::::::::===+*@@@@@@@#+@@@@@@@@@@@@@@@@@@@@@@=:::::..........................
 @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@==::::::..........................
 :::::::::::===+*@@@@@@@#+@@@@@@@@@@@@@@@@@@@@@@=:::::..........................
 ....::::::::::+==========*@@@@@@@@@@@@@@@@@@@@@@+:::...........................
  ............::::::::::::===@@@@@@@@@@@@@@@@@@+::::...........................
   ................:::::::::*+===++++@@+=+=+=::=:::...........................
    ...................:::::::::::=++@@++=:::::::............................
      .....................::::::::::===@:::::.............................
        ..........................::::::.................................
           ...........................................................
              .....................................................
                  .............................................
                        .................................

```

Use the `--` separator to pass command-line arguments to the emulated program (the basename of the executable is automatically passed as `argv[0]`):
```
./riscv-emu.py build/test_newlib_args.elf -- arg1 arg2 arg3
Number of arguments: 4
Argument 0: test_newlib_args.elf
Argument 1: arg1
Argument 2: arg2
Argument 3: arg3
```

Run MicroPython:
```
./riscv-emu.py --raw-tty --ram-size=4096 prebuilt/micropython.elf 
Welcome to MicroPython on RISC-V!
MicroPython v1.25.0 on 2025-05-01; emulated with riscv-emu.py
Type "help()" for more information.
>>> 
```

Run a sample FreeRTOS application:
```
./riscv-emu.py --timer=csr prebuilt/freertos_app1.elf
```

Run an example using the memory-mapped UART,
```
./riscv-emu.py --uart prebuilt/test_peripheral_uart.elf 
000.001s [INFO] [UART] PTY created: /dev/ttys015
```
and connect to the serial device using your favorite terminal program, e.g., `screen /dev/ttys015 115200`.

Run an example using a file-backed block device:
```
./riscv-emu.py --blkdev=image.img prebuilt/test_peripheral_blkdev.elf 
```

Run CircuitPython:
```
./riscv-emu.py --timer=mmio --ram-size=4096 --uart --blkdev=prebuilt/circuitpy_fatfs.img prebuilt/circuitpython.elf 
000.001s [INFO] [UART] PTY created: /dev/ttys015
000.002s [INFO] [BLOCK] Opening block device image: prebuilt/circuitpy.img
```
and connect to the console using your favorite terminal program, e.g., `screen /dev/ttys015 115200`.

### Using the Python API

The emulator provides a Python API that allows users to control execution, set and inspect state, and run complex tests directly from Python programs. Here is an example of how you can load and run a simple RV32I program:
```python
from cpu import CPU
from ram import RAM

ram = RAM(1024)
cpu = CPU(ram)

# Store into RAM a simple program that sums integers from 1 to 100 and returns the result in t0
ram.store_word(0x00000000, 0x00000293)  #        li t0, 0
ram.store_word(0x00000004, 0x00100313)  #        li t1, 1
ram.store_word(0x00000008, 0x06400393)  #        li t2, 100
ram.store_word(0x0000000c, 0x006282b3)  # <loop> add t0, t0, t1
ram.store_word(0x00000010, 0x00130313)  #        addi t1, t1, 1
ram.store_word(0x00000014, 0xfe63dce3)  #        bge t2, t1, c <loop>
ram.store_word(0x00000018, 0x00100073)  #        ebreak

# Run the program
cpu.pc = 0x00000000               # set initial PC
while True:
    inst = ram.load_word(cpu.pc)  # fetch
    cpu.execute(inst)             # decode & execute
    cpu.pc = cpu.next_pc          # update PC

    if cpu.pc == 0x00000018:  # when we reach this address, the program has finished
        break

print (cpu.registers[5])  # Print result stored in t0/x5
```

Example Python programs using programmatic access to the emulator are provided in the `tests` directory. Run them from the top-level directory of the emulator, e.g.:
```
PYTHONPATH=. python tests/test_api_simple.py
```

### 🐛 GDB Remote Debugging

The emulator includes GDB remote debugging support. Add the `--gdb` flag to enable it:

```bash
./riscv-emu.py --gdb prebuilt/test_bare1.elf
```

Then connect with GDB, e.g.:
```bash
riscv64-unknown-elf-gdb prebuilt/test_bare1.elf
(gdb) target remote localhost:1234
```

All standard GDB commands work (breakpoints, stepping, register/memory inspection). CSRs can be accessed via monitor commands: `monitor csr mstatus`, `monitor csr mtvec 0x1000`.

### 🌐 Running Programs in the Browser

The emulator can run in a web browser thanks to [Pyodide](https://pyodide.org/). See `advanced/webapp/`.

You can [try it out here](https://ccattuto.github.io/riscv-python/) using the binaries available in `prebuilt/`.

## 🧪 Running Unit Tests
```
cd riscv-tests
./configure
make
cd -
```

The script automatically runs all RV32UI, RV32MI, RV32UM, RV32UA, and RV32UC [RISC-V unit tests](https://github.com/riscv-software-src/riscv-tests) in `riscv-tests/`. The emulator passes all of them.
```
./run_unit_tests.py
Test rv32ui-p-bltu                 : PASS
Test rv32ui-p-xori                 : PASS
Test rv32ui-p-blt                  : PASS
Test rv32ui-p-add                  : PASS
Test rv32ui-p-and                  : PASS
Test rv32ui-p-srli                 : PASS
Test rv32ui-p-sub                  : PASS
Test rv32ui-p-sh                   : PASS
Test rv32ui-p-srai                 : PASS
Test rv32ui-p-srl                  : PASS
Test rv32ui-p-ld_st                : PASS
Test rv32ui-p-or                   : PASS
Test rv32ui-p-lbu                  : PASS
Test rv32ui-p-bge                  : PASS
Test rv32ui-p-lhu                  : PASS
Test rv32ui-p-lh                   : PASS
Test rv32ui-p-jal                  : PASS
Test rv32ui-p-slt                  : PASS
Test rv32ui-p-bne                  : PASS
Test rv32ui-p-sltiu                : PASS
Test rv32ui-p-beq                  : PASS
Test rv32ui-p-slli                 : PASS
Test rv32ui-p-slti                 : PASS
Test rv32ui-p-sltu                 : PASS
Test rv32ui-p-fence_i              : PASS
Test rv32ui-p-sb                   : PASS
Test rv32ui-p-xor                  : PASS
Test rv32ui-p-andi                 : PASS
Test rv32ui-p-addi                 : PASS
Test rv32ui-p-sw                   : PASS
Test rv32ui-p-auipc                : PASS
Test rv32ui-p-lui                  : PASS
Test rv32ui-p-simple               : PASS
Test rv32ui-p-ma_data              : PASS
Test rv32ui-p-sra                  : PASS
Test rv32ui-p-lb                   : PASS
Test rv32ui-p-bgeu                 : PASS
Test rv32ui-p-lw                   : PASS
Test rv32ui-p-sll                  : PASS
Test rv32ui-p-st_ld                : PASS
Test rv32ui-p-jalr                 : PASS
Test rv32ui-p-ori                  : PASS
Test rv32mi-p-mcsr                 : PASS
Test rv32mi-p-illegal              : PASS
Test rv32mi-p-shamt                : PASS
Test rv32mi-p-scall                : PASS
Test rv32mi-p-sw-misaligned        : PASS
Test rv32mi-p-zicntr               : PASS
Test rv32mi-p-ma_addr              : PASS
Test rv32mi-p-lw-misaligned        : PASS
Test rv32mi-p-breakpoint           : PASS
Test rv32mi-p-lh-misaligned        : PASS
Test rv32mi-p-sh-misaligned        : PASS
Test rv32mi-p-csr                  : PASS
Test rv32mi-p-pmpaddr              : PASS
Test rv32mi-p-instret_overflow     : PASS
Test rv32mi-p-ma_fetch             : PASS
Test rv32mi-p-sbreak               : PASS
Test rv32um-p-rem                  : PASS
Test rv32um-p-mulhsu               : PASS
Test rv32um-p-remu                 : PASS
Test rv32um-p-divu                 : PASS
Test rv32um-p-mulhu                : PASS
Test rv32um-p-div                  : PASS
Test rv32um-p-mul                  : PASS
Test rv32um-p-mulh                 : PASS
Test rv32ua-p-amomax_w             : PASS
Test rv32ua-p-amoxor_w             : PASS
Test rv32ua-p-amoor_w              : PASS
Test rv32ua-p-amomaxu_w            : PASS
Test rv32ua-p-lrsc                 : PASS
Test rv32ua-p-amomin_w             : PASS
Test rv32ua-p-amoand_w             : PASS
Test rv32ua-p-amominu_w            : PASS
Test rv32ua-p-amoadd_w             : PASS
Test rv32ua-p-amoswap_w            : PASS
Test rv32uc-p-rvc                  : PASS
```

## Design Goals
- Simplicity over speed (though it is highly optimized for speed and performs near the limit of what is possible in pure Python)
- Emphasis on correctness and compliance with RISC-V specifications
- Minimal dependencies
- Separation of concerns: core ISA, syscalls, binary loading, peripherals, and emulation control
- Useful for teaching, debugging, and testing compiler output

## Notes
- The provided examples were tested on macOS Sequoia using [Homebrew's RISC-V GNU Compiler Toolchain](https://github.com/riscv-software-src/homebrew-riscv) and Python 3.12.
- The provided Makefile builds all Newlib examples using Newlib-nano (`--specs=nano.specs` linker option).
- The linker scripts and emulator assume 1Mb of RAM (addresses `0x00000000` - `0x000FFFFF`). If you change the RAM size, ensure you also update the linker scripts and specify the new size using the `--ram-size` option.
- The emulator relies on ELF symbols for heap management and call tracing: do not strip ELF binaries if you need dynamic memory allocation via Newlib or call tracing.
- When a trap condition is triggered, if `mtvec` is zero, the emulator's internal trap handler is invoked, which supports Newlib's system calls. If you install a custom trap handler (by setting a non-zero `mtvec`), your handler becomes responsible for all trap behavior including managing system calls.
- `EBREAK` traps with `a7 >= 0xFFFF0000` are used as a debug bridge, regardless of `mtvec`. See `riscv-py.h` for simple logging macros using this feature. These logging macros do not depend on Newlib.
- The emulated architecture supports unaligned memory accesses and will not trap when they occur.
- The 64-bit registers `mtime` and `mtimecmp` are either memory mapped (`--timer=mmio`) at the standard addresses (`0x0200BFF8` and `0x02004000`, respectively) or accessible via CSR instructions (`--timer=csr`) at addresses `0x7C0` (low 32 bits of `mtime`), `0x7C1` (high 32 bits of `mtime`), `0x7C2` (low 32 bits of `mtimecmp`), and `0x7C3` (high 32 bits of `mtimecmp`). Writes to `mtime` are atomic for the whole 64-bit register and occur when the second word of the register is written to (in any order). For applications needing the machine timer, but not needing MMIO peripherals, the CSR implementation is preferrable for performance reasons.
- Certain features of the emulator rely on POSIX-specific functionalities and may not work as expected on native Windows environments. The emulated UART uses a pseudo-terminal (PTY), which depends on POSIX-specific Python modules (`os.openpty`, `tty`, `fcntl`) and is unlikely to work correctly on Windows. Raw Terminal Mode (`--raw-tty`) also utilizes POSIX-specific modules (`tty`, `termios`) and will not function as intended on Windows. Some emulated system calls (e.g., `_openat`, `_mkdirat` using `AT_FDCWD`) are modeled closely on POSIX standards: discrepancies in behavior or support for specific flags might occur on Windows.

###  Performance notes
The emulator achieves **over 2 MIPS** (million instructions per second) using Python 3.12 (Anaconda distribution) on a Macbook Pro (M1, 2020) running macOS Sequoia. Execution times for some binaries in `prebuilt/`:
```
time ./riscv-emu.py prebuilt/test_newlib_primes.elf
./riscv-emu.py prebuilt/test_newlib_primes.elf  1.71s user 0.03s system 98% cpu 1.772 total
```
```
time ./riscv-emu.py prebuilt/test_newlib_mandelbrot.elf
./riscv-emu.py prebuilt/test_newlib_mandelbrot.elf  0.37s user 0.03s system 94% cpu 0.416 total
```
```
time ./riscv-emu.py prebuilt/test_newlib_conway.elf
./riscv-emu.py prebuilt/test_newlib_conway.elf  76.19s user 0.29s system 99% cpu 1:16.56 total
```

Running the emulator with [PyPy](https://pypy.org/) yields a speedup of almost 4x over CPython, achieving **over 9 MIPS**.
```
time pypy3 ./riscv-emu.py prebuilt/test_newlib_conway.elf
pypy3 ./riscv-emu.py prebuilt/test_newlib_conway.elf  19.77s user 0.11s system 99% cpu 20.009 total
```

## Acknowledgements

**Danh** and **Tannewt** from [Adafruit's Discord server](http://adafru.it/discord) for help with the CircuitPython port.  **Onur Toker** for identifing an issue with the Newlib initialization sequence. [ChatGPT Pro](https://chatgpt.com) for debugging the initial implementation. [Claude Code](https://www.claude.com/product/claude-code) for RVC support and for the development of the Web app and the GDB stub.
