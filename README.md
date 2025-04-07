# 🐍 RISC-V Emulator in Python (RV32I, user mode)

This is a simple and readable **RISC-V RV32I emulator** written in Python, targeting **user-mode** applications compiled with **Newlib** or **Newlib-nano**. It is designed for educational use, experimentation, and portability — not for high performance or full system emulation.

## ✅ Features

- 🧠 **Implements the full RV32I base integer ISA**
- 🚀 **Supports ELF and flat binary formats**
- 📞 **Supports [Newlib](https://en.wikipedia.org/wiki/Newlib)'s system calls**: `_write`, `_read`, `_exit`, `_sbrk`.
- 💾 **Supports `malloc`/`free()`** via Newlib's `_sbrk()`
- 🎨 **Supports terminal I/O**
- 🧪 **Passes all `rv32ui` unit tests** from [riscv-samples](https://gitlab.univ-lille.fr/michael.hauspie/riscv-samples/)
- 🧹 Compact and self-contained codebase (~300 lines for core logic, ~150 lines for emulation control)

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
├── riscv.py               # Core emulator logic
├── Makefile               # Builds ELF/binary targets
├── start_bare.S           # Minimal startup code
├── start_newlib.S         # Startup code for Newlib-nano
├── syscalls_newlib.S      # Newlib-compatible syscall stubs for Newlib-nano
├── linker_bare.ld         # Siple linker script, no heap support
├── linker_newlib.ld       # Linker script supporting newlib
├── test_asm*.S            # Example assembly programs
├── test_bare*.C           # Example C programs without newlib support
├── test_newlib*.C         # Example C programs with newlib-nano support
├── run_unit_tests.sh      # Run RISC-V unit tests (RV32I only, user-mode only)
├── riscv-samples/         # Git submodule with unit tests
└── README.md              # You're here!
```

## 🚀 Usage

### 🛠️ Compiling Examples

```
make all
```

### ▶️ Running Programs

Assembly examples (starts at PC=0):
```
./risc-emu.py test_asm1.bin
```

Bare C examples (starts at PC=0):
```
./risc-emu.py test_bare1.bin
```
or
```
./risc-emu.py test_bare1.elf
```

Newlib C examples:
```
./riscv-emu.py test_newlib4.elf
                                                                                
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

### ▶️ Command-Line Options

`riscv-emu.py` accepts the following options:

| Option             | Description                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| `--regs`           | Print selected registers (`pc`, `ra`, `sp`, `gp`, `a0`) at each instruction |
| `--check`          | Enable runtime invariant checks on stack/heap alignment and boundaries      |
| `--check-text`     | Ensure the `.text` segment remains unmodified during execution              |
| `--trace`          | Print the name of functions traversed during execution                      |
| `--help`           | Show usage help and available options                                       |

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

## 🧩 Design Goals
- Simplicity over speed
- Minimal dependencies
- Good separation of concerns: core ISA, syscall emulation, and binary loading
- Useful for teaching, debugging, testing compiler output

## Notes
- The provided examples were tested on OSX Sequoia using [Homebrew's RISC-V GNU Compiler Toolchain](https://github.com/riscv-software-src/homebrew-riscv), Python 3.12.4
- The provided Makefild build all Newlib examples selecting Newlib-nano (`--specs=nano.specs` linker option)

