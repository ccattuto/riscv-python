# 🐍 RISC-V Emulator in Python (RV32I, machine mode, Newlib support)

This is a simple and readable **RISC-V RV32I emulator** written in pure Python. It supports machine mode, and can run programs compiled with **Newlib** or **Newlib-nano**. It is designed for educational use, experimentation, and portability — not for high performance or full system emulation.

## ✅ Features

- **Implements the full RV32I base integer ISA**
- **Supports machine mode**, including synchronous traps (`ecall`, `ebreak`, illegal instruction trap), asynchronous traps (machine timer interrupt), `mret`, CSR instructions and registers (`mstatus`, `mepc`, `mtvec`, `mcause`, `mscratch`, ...)
- **Supports ELF and flat binary formats**
- **Supports terminal I/O**, both "cooked" and raw
- **Supports most of [Newlib](https://en.wikipedia.org/wiki/Newlib)'s system calls** (`_write`, `_read`, `_exit`, ...)
- **Supports dynamic memory allocation** via Newlib (`_sbrk`)
- **Supports file I/O system calls** (`_open`, `_close`, `_fstat`, `_lseek`, `_unlink`, `_mkdir`, `_rmdir`, ...)
- **Supports argc/argv program arguments**
- **Passes all `rv32ui` unit tests** from [riscv-samples](https://gitlab.univ-lille.fr/michael.hauspie/riscv-samples/)
- **Supports logging** of register values, function calls, system calls, traps, invalid memory accesses, violations of invariants
- Runs [MicroPython](https://micropython.org/) and [FreeRTOS](https://www.freertos.org/)
- Self-contained, modular, extensible codebase

## 🔧 Requirements

- Python 3.8+
- `pyelftools` for ELF parsing:
  ```bash
  pip install pyelftools
  ```
- [RISC-V GNU Compiler Toolchain](https://github.com/riscv-collab/riscv-gnu-toolchain)


## File Strucure

```
├── riscv-emu.py           # Emulator
├── cpu.py                 # CPU emulation logic
├── ram.py                 # RAM emulation logic
├── machine.py             # Host logic (executable loading, invariants check)
├── syscalls.py            # System calls and terminal I/O
├── Makefile               # Builds ELF/binary targets
├── start_bare.S           # Minimal startup code
├── start_newlib.S         # Startup code for Newlib-nano
├── syscalls_newlib.S      # Syscall stubs for Newlib-nano
├── linker_bare.ld         # Simple linker script, no heap support
├── linker_newlib.ld       # Linker script supporting Newlib-nano
├── riscv-py.h             # Emulator macros for user programs
├── tests/README.md        # Documentation for example programs
├── tests/test_asm*.S      # Example assembly programs
├── tests/test_bare*.C     # Example C programs without Newlib support
├── tests/test_newlib*.C   # Example C programs with Newlib-nano support
├── build/                 # Executable and binaries
├── prebuilt/              # Pre-built examples
├── run_unit_tests.sh      # Runs RISC-V unit tests (RV32I only, user-mode only)
├── riscv-samples/         # Git submodule with unit tests
└── README.md              # You're here!
```

## 🚀 Usage

### Compiling Examples

```
make all
```

(if you just want to test the emulator without installing a RISC-V compiler, you will find pre-built binaries in `prebuilt/`)

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

Use the `--` separator to pass command-line arguments to the emulated program (the basename of the executable is automatically passed as argument 0):
```
./riscv-emu.py build/test_newlib7.elf -- arg1 arg2 arg3    
Number of arguments: 4
Argument 0: test_newlib7.elf
Argument 1: arg1
Argument 2: arg2
Argument 3: arg3
```

### ▶️ Command-Line Options

`riscv-emu.py` accepts the following options:

| Option                | Description                                                                 |
|-----------------------|-----------------------------------------------------------------------------|
| `--regs REGS`         | Print selected registers at each instruction                                |
| `--trace`             | Log the names of functions traversed during execution                       |
| `--syscalls`          | Log Newlib syscalls                                                         |
| `--traps`             | Enable trap tracing                                                         |
| `--check-inv`         | Enable runtime invariant checks on stack/heap alignment and boundaries      |
| `--check-ram`         | Check validity of memory accesses                                           |
| `--check-text`        | Ensure the `.text` segment remains unmodified during execution              |
| `--check-all`         | Enable all checks                                                           |
| `--start-checks WHEN` | Condition to enable checks (auto, early, main, first-call, 0xADDR)          |
| `--init-regs VALUE`   | Initial register state (zero, random, 0xDEADBEEF)                           |
| `--init-ram PATTERN`  | Initialize RAM with pattern (zero, random, addr, 0xAA)                      |
| `--ram-size KBS`      | Emulated RAM size (kB, default 1024)                                        |
| `--timer`             | Enable machine timer                                                        |
| `--raw-tty`           | Enable raw terminal mode                                                    |
| `--no-color`          | Remove ANSI colors in debugging output                                      |
| `--log LOG_FILE`      | Log debug information to file `LOG_FILE`                                    |
| `--help`              | Show usage help and available options                                       |

## 🧪 Running Unit Tests
(on OSX, you might need to force `TOOLCHAIN=riscv64-unknown-elf` in the Makefile)
```
cd riscv-samples/unit-tests
make
cd -
```

```
./run_unit_tests.sh
[PASS] add.bin
[PASS] addi.bin
[PASS] and.bin
[PASS] andi.bin
[PASS] auipc.bin
[PASS] beq.bin
[PASS] bge.bin
[PASS] bgeu.bin
[PASS] blt.bin
[PASS] bltu.bin
[PASS] bne.bin
[PASS] jal.bin
[PASS] jalr.bin
[PASS] lb.bin
[PASS] lbu.bin
[PASS] lh.bin
[PASS] lhu.bin
[PASS] lui.bin
[PASS] lw.bin
[PASS] ma_data.bin
[PASS] or.bin
[PASS] ori.bin
[PASS] sb.bin
[PASS] sh.bin
[PASS] simple.bin
[PASS] sll.bin
[PASS] slli.bin
[PASS] slt.bin
[PASS] slti.bin
[PASS] sltiu.bin
[PASS] sltu.bin
[PASS] sra.bin
[PASS] srai.bin
[PASS] srl.bin
[PASS] srli.bin
[PASS] sub.bin
[PASS] sw.bin
[PASS] xor.bin
[PASS] xori.bin
Summary: 39 passed, 0 failed
```
This script automatically runs all RV32UI .bin tests in `riscv-samples/unit-tests/rv32ui/`.
All unit tests from [riscv-samples](https://gitlab.univ-lille.fr/michael.hauspie/riscv-samples/) pass.

## Design Goals
- Simplicity over speed (but highly optimized for speed, it performs at the limit of what is possible in pure Python)
- Emphasis on correctness and compliance with RISC-V specifications
- Minimal dependencies
- Separation of concerns: core ISA, syscalls, binary loading, and emulation control
- Useful for teaching, debugging, testing compiler output

## Notes
- The provided examples were tested on OSX Sequoia using [Homebrew's RISC-V GNU Compiler Toolchain](https://github.com/riscv-software-src/homebrew-riscv) and Python 3.12.
- The provided Makefile builds all Newlib examples using Newlib-nano (`--specs=nano.specs` linker option).
- The linker scripts and emulator assume 1Mb of RAM (addresses `0x00000000` - `0x000FFFFF`). If you change RAM size, make sure you update the linker scripts and specify RAM size using the `--ram-size` option.
- The emulator relies on ELF symbols for heap management and call tracing: do not strip ELF binaries.
- When a trap condition is triggered, if `mtvec` is set to zero, the emulator's trap handler is invoked and supports Newlib's system calls. If you install your own trap handler (non-zero `mtvec`), you are responsible for all trap behavior including system calls.
- `EBREAK` traps with `a7 >= 0xFFFF0000` are used as a debug bridge, regardless of `mtvec`. See `riscv-py.h` for simple logging macros using this feature. These logging macros do not depend on Newlib.
- The emulated architecture supports unaligned memory accesses and will not trap when they occur.
- The 64-bit registers `mtime` and `mtimecmp` are accessible via CSR instructions (rather than being memory-mapped) at addresses `0x7C0` (low 32 bits of `mtime`), `0x7C1` (high 32 bits of `mtime`), `0x7C2` (low 32 bits of `mtimecmp`), and `0x7C3` (high 32 bits of `mtimecmp`). Writes to `mtime` and `mtimecmp` are atomic for the whole 64-bit register and occur when the second word of the register is written.

###  Performance notes
The emulator achieves **~1.5 MIPS** (million instructions per second) using Python 3.12 (Anaconda) on a Macbook Pro (M1, 2020) running OSX Sequoia. Execution times for some binaries in `prebuilt/`:
```
time ./riscv-emu.py build/test_newlib2.elf
./riscv-emu.py build/test_newlib2.elf  16.86s user 0.04s system 98% cpu 17.103 total
```
```
time ./riscv-emu.py build/test_newlib4.elf
./riscv-emu.py build/test_newlib4.elf  7.29s user 0.04s system 99% cpu 7.362 total
```
```
time ./riscv-emu.py build/test_newlib6.elf
./riscv-emu.py build/test_newlib6.elf  115.87s user 0.49s system 99% cpu 1:56.55 total
```
