# 🐍 RISC-V Emulator in Python (RV32I, user mode)

This is a simple and readable **RISC-V RV32I emulator** written in Python, targeting **user-mode** applications compiled with **Newlib** or **Newlib-nano**. It is designed for educational use, experimentation, and portability — not for high performance or full system emulation.

## ✅ Features

- **Implements the full RV32I base integer ISA**
- **Supports ELF and flat binary formats**
- **Supports terminal I/O**, both "cooked" and raw
- **Supports most of [Newlib](https://en.wikipedia.org/wiki/Newlib)'s system calls** (`_write`, `_read`, `_exit`, ...)
- **Supports `malloc`/`free()`** via Newlib's `_sbrk()`
- **Supports file I/O system calls** (`_open`, `_close`, `_fstat`, `_lseek`, `_unlink`, `_mkdir`, `_rmdir`)
- **Supports argc/argv program arguments**
- **Passes all `rv32ui` unit tests** from [riscv-samples](https://gitlab.univ-lille.fr/michael.hauspie/riscv-samples/)
- **Supports logging** of register values, call traces, system calls, invalid memory accesses, violations of invariants
- Compact, self-contained, modular codebase

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

Bare C examples (starts at PC=0):
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

| Option               | Description                                                                 |
|----------------------|-----------------------------------------------------------------------------|
| `--regs`             | Print selected registers (`pc`, `ra`, `sp`, `gp`, `a0`) at each instruction |
| `--trace`            | Log the names of functions traversed during execution                       |
| `--syscalls`         | Log Newlib syscalls                                                         |
| `--check-inv`        | Enable runtime invariant checks on stack/heap alignment and boundaries      |
| `--check-ram`        | Check validity of memory accesses                                           |
| `--check-text`       | Ensure the `.text` segment remains unmodified during execution              |
| `--check-all`        | Enable all checks                                                           |
| `--check-start WHEN` | Condition to enable checks (default, early, main, first-call, 0xADDR)       |
| `--init-regs VALUE`  | Initial register state (zero, random, 0xDEADBEEF)                           |
| `--init-ram PATTERN` | Initialize RAM with pattern (random, addr, 0xAA)                            |
| `--raw-tty`          | Enable raw terminal mode                                                    |
| `--no-color`         | Remove ANSI colors in debugging output                                      |
| `--log LOG_FILE`     | Log debug information to file `LOG_FILE`                                    |
| `--help`             | Show usage help and available options                                       |

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
- Minimal dependencies
- Good separation of concerns: core ISA, syscalls, binary loading, and emulation control
- Useful for teaching, debugging, testing compiler output

## Notes
- The provided examples were tested on OSX Sequoia using [Homebrew's RISC-V GNU Compiler Toolchain](https://github.com/riscv-software-src/homebrew-riscv) and Python 3.12. The emulator can run complex code such as, e.g., minimal [MicroPython](https://micropython.org/)
- The provided Makefile builds all Newlib examples using Newlib-nano (`--specs=nano.specs` linker option)
- The linker scripts and emulator assume 1Mb of RAM (addresses `0x00000000` - `0x000FFFFF`). If you change RAM size, make sure you update both the linker scripts and the `MEMORY_SIZE` constant in `risc-emu.py`
- The emulator relies on ELF symbols for heap management and call tracing: do not strip ELF binaries.

###  Performance notes
```
time ./riscv-emu.py build/test_newlib4.elf
./riscv-emu.py build/test_newlib4.elf  7.29s user 0.04s system 99% cpu 7.362 total
```
```
time ./riscv-emu.py build/test_newlib6.elf
./riscv-emu.py build/test_newlib6.elf  115.87s user 0.49s system 99% cpu 1:56.55 total
```
