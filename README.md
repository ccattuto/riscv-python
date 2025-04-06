# 🐍 RISC-V Emulator in Python (RV32I, user mode)

This is a simple and readable **RISC-V RV32I emulator** written in Python, targeting **user-mode** applications compiled with **Newlib** or **Newlib-nano**. It is designed for educational use, experimentation, and portability — not for high performance or full system emulation.

## ✅ Features

- 🧠 **Implements the full RV32I base integer ISA**
- 🚀 **Supports ELF and flat binary formats**
- 📞 **Supports Newlib's system calls**: `_write`, `_read`, `_exit`, `_sbrk`.
- 💾 **Supports `malloc`/`free()` via Newlib's `_sbrk()`**
- 🎨 **Supports terminal I/O**
- 🧪 **Passes all `rv32ui` unit tests** from [riscv-samples](https://gitlab.univ-lille.fr/michael.hauspie/riscv-samples/)
- 🧹 Compact and self-contained codebase (~300 lines code)

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
├── test_newlib*.C         # Example C programs with newlib support
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

## 🧪 Running Unit Tests
(on OSX, you might need to force `TOOLCHAIN=riscv64-unknown-elf` in the Makefile)
```
cd riscv-samples/unit-tests
make
cd -
```

```
./run_unit_tests.sh
```
This script automatically runs all RV32UI .bin tests in `riscv-samples/unit-tests/rv32ui/`.
All unit tests from [riscv-samples](https://gitlab.univ-lille.fr/michael.hauspie/riscv-samples/) pass.

## 🧩 Design Goals
- Simplicity over speed
- Minimal dependencies
- Good separation of concerns: core ISA, syscall emulation, and binary loading
- Useful for teaching, debugging, testing compiler output
