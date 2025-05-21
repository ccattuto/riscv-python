# 🐍 RISC-V Emulator in Python (RV32I, machine mode, Newlib support)

This is a simple and readable **RISC-V RV32I emulator** written in pure Python. It supports machine mode, and can run programs compiled with **Newlib** or **Newlib-nano**. It is designed for educational use, experimentation, and portability — not for high performance or full system emulation.

## ✅ Features

- **Implements the full RV32I base integer ISA**
- **Implements all RV32MI machine-mode instructions and trap mechanisms**, including synchronous traps (`ecall`, `ebreak`, illegal instruction trap), asynchronous traps (machine timer interrupt), `mret`, and the **Zicsr (Control Status Registers) extension** and registers (`mstatus`, `mepc`, `mtvec`, `mcause`, `mscratch`, ...)
- **Supports loading ELF and flat binary formats**
- **Supports terminal I/O**, both "cooked" and raw
- **Provides most of the system calls needed by [Newlib](https://en.wikipedia.org/wiki/Newlib)**: `_write`, `_read`, `_exit`, **dynamic memory allocation** (`_sbrk`), **file I/O** (`_open`, `_close`, `_fstat`, `_lseek`, ...)
- **Supports argc/argv program arguments**
- **Supports memory-mapped IO** and provides a **UART peripheral** using a pseudo-terminal, and a **memory-mapped block device** backed by an image file
- **Passes all `rv32ui` and `rv32mi` unit tests** provided by [RISC-V International](https://github.com/riscv-software-src/riscv-tests)
- **Supports logging** of register values, function calls, system calls, traps, invalid memory accesses, and violations of invariants
- Runs [MicroPython](https://micropython.org/), [CircuitPython](https://circuitpython.org/) with emulated peripherals, and [FreeRTOS](https://www.freertos.org/) with preemptive multitasking
- Self-contained, modular, extensible codebase

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
├── ram.py                     # RAM emulation logic
├── machine.py                 # Host logic (executable loading, invariants check)
├── peripherals.py             # Peripherals (UART, block device)
├── syscalls.py                # System calls and terminal I/O
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
├── build/                     # Executable and binaries
├── prebuilt/                  # Pre-built examples
├── run_unit_tests.py          # Runs RISC-V unit tests (RV32UI and RV32MI)
├── riscv-tests/               # Git submodule with RISC-V unit tests
├── advanced/freertos/         # FreeRTOS port
├── advanced/micropython/      # MicroPython port
├── advanced/circuitpython/    # CircuitPython port
└── README.md                  # You're here!
```

## 🚀 Usage

### Compiling Examples
```
make all
```
If you just want to **test the emulator without installing a RISC-V compiler**, you will find pre-built binaries in `prebuilt/`.

To build the examples under `advanced/` (MicroPython, FreeRTOS, ...) you will need to initialize the submodules:
```
git submodule update --init --recursive
```

### ▶️ Running Programs

Assembly examples (starts at PC=0):
```
./risc-emu.py build/test_asm1.bin
```

Bare C examples (starts at PC=0, `_start` in `start_bare.S`):
```
./risc-emu.py build/test_bare1.bin
```
or
```
./risc-emu.py build/test_bare1.elf
```

Newlib C examples:
```
./riscv-emu.py build/test_newlib4.elf
                                                                                
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
./riscv-emu.py build/test_newlib7.elf -- arg1 arg2 arg3    
Number of arguments: 4
Argument 0: test_newlib7.elf
Argument 1: arg1
Argument 2: arg2
Argument 3: arg3
```

Run MicroPython:
```
./riscv-emu.py --raw-tty --ram-size=4096 prebuilt/micropython.elf 
Welcome to MicroPython on RISC-V!
MicroPython v1.25.0 on 2025-05-01; emulated with risc-emu.py
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
and connect to the serial device using your favorite terminal program:
```
screen /dev/ttys015 115200
```

Run an example using a file-backed block device:
```
./riscv-emu.py --blkdev=image.img prebuilt/test_peripheral_blkdev.elf 
```

### ▶️ Command-Line Options

`riscv-emu.py` accepts the following options:

| Option                  | Description                                                                 |
|-------------------------|-----------------------------------------------------------------------------|
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
| `--help`                | Show usage help and available options                                       |

## 🧪 Running Unit Tests
```
cd riscv-tests
./configure
make
cd -
```

The script automatically runs all RV32UI and RV32MI [RISC-V unit tests](https://github.com/riscv-software-src/riscv-tests) in `riscv-tests/`. The emulator passes all of them.
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
time ./riscv-emu.py prebuilt/test_newlib2.elf
./riscv-emu.py prebuilt/test_newlib2.elf  11.43s user 0.05s system 99% cpu 11.506 total
```
```
time ./riscv-emu.py prebuilt/test_newlib4.elf
./riscv-emu.py prebuilt/test_newlib4.elf  4.90s user 0.03s system 99% cpu 4.973 total
```
```
time ./riscv-emu.py prebuilt/test_newlib6.elf
./riscv-emu.py prebuilt/test_newlib6.elf  75.85s user 0.24s system 99% cpu 1:16.37 total
```

Running the emulator with [PyPy](https://pypy.org/) yields a speedup of almost 4x over CPython, achieving **over 9 MIPS**.
```
time pypy3 ./riscv-emu.py prebuilt/test_newlib2.elf
pypy3 ./riscv-emu.py prebuilt/test_newlib2.elf  2.76s user 0.06s system 97% cpu 2.891 total
```
```
time pypy3 ./riscv-emu.py prebuilt/test_newlib4.elf
pypy3 ./riscv-emu.py prebuilt/test_newlib4.elf  1.24s user 0.03s system 99% cpu 1.276 total
```
```
time pypy3 ./riscv-emu.py prebuilt/test_newlib6.elf
pypy3 ./riscv-emu.py prebuilt/test_newlib6.elf  19.82s user 0.15s system 99% cpu 20.046 total
```
