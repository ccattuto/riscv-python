# 🐍 RISC-V Emulator in Python (RV32I, User Mode)

This is a simple and readable **RISC-V RV32I emulator** written in Python, targeting **user-mode** applications compiled with **Newlib** or **Newlib-nano**. It is designed for educational use, experimentation, and portability — not for high performance or full system emulation.

## ✅ Features

- 🧠 **Implements the full RV32I base integer ISA**
- 🚀 **Supports ELF and flat binary formats**
- 📞 **Emulates system calls**: `_write`, `_read`, `_exit`, `_sbrk`.
- 💾 **Supports `malloc`/`free()` via Newlib's `_sbrk()`**
- 🎨 **Supports terminal output (e.g., Mandelbrot ASCII art)**
- 🧪 **Passes all `rv32ui` unit tests** from [riscv-samples](https://gitlab.univ-lille.fr/michael.hauspie/riscv-samples/)
- 🧹 Compact and self-contained codebase (~300 lines core)

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
├── start_bare.S           # Minimal RISC-V startup code
├── start_newlib.S         # Minimal RISC-V startup code
├── syscalls_newlib.S      # Newlib-compatible syscall stubs for newlib
├── linker_bare.ld         # Siple linker script, no heap support
├── linker_newlib.ld       # Linker script supporting newlib
├── test_asm*.S            # Example assembly programs
├── test_bare*.C           # Example C programs without newlib support
├── test_newlib*.C         # Example C programs with newlib support
├── run-unit-tests.sh      # Run RISC-V unit tests (RV32I only, user-mode only)
├── riscv-samples/         # Git submodule with unit tests
└── README.md              # You're here!
```

## 🚀 Usage

### 🛠️ Compiling Examples

### ▶️ Running Programs


## 🧪 Running Unit Tests

