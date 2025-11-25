# MicroPython port for riscv-emu.py

This is a MicroPython port that runs on the riscv-emu.py RISC-V emulator.

## Prerequisites

Before building, ensure the micropython-lib submodule is initialized:

```bash
cd micropython
git submodule update --init lib/micropython-lib
```

## Building

The port supports three build modes:

### 1. REPL_NEWLIB (default)
Interactive REPL on host's stdio:
```bash
make
# or explicitly
make MODE=REPL_NEWLIB
```

### 2. HEADLESS
Executes a frozen Python script with no stdio (requires `FROZEN_SCRIPT`, defaults to `startup.py`):
```bash
make MODE=HEADLESS FROZEN_SCRIPT=startup.py
```

### 3. REPL_UART
REPL over emulated UART, with an optional frozen initialization script (requires `FROZEN_SCRIPT`, defaults to `startup.py`):
```bash
make MODE=REPL_UART FROZEN_SCRIPT=startup.py
```

## Build Options

- `MODE` - Build mode: `REPL_NEWLIB` (default), `HEADLESS`, or `REPL_UART`
- `FROZEN_SCRIPT` - Python script to freeze into firmware (required for HEADLESS, optional for REPL_UART, defaults to `startup.py`)
- `RVM=1` - Enable RISC-V M extension (multiply/divide, default: enabled)
- `RVA=0` - Enable RISC-V A extension (atomics, default: disabled)
- `RVC=0` - Enable RISC-V C extension (compressed instructions, default: disabled)

## Build Characteristics

| Mode | Binary Size | Newlib | Float Support | Long Int Support |
|------|-------------|--------|---------------|------------------|
| REPL_NEWLIB | ~246 KB | Yes | Yes | Yes |
| HEADLESS | ~194 KB | No | No | No |
| REPL_UART | ~194 KB | No | No | No |

**HEADLESS and REPL_UART modes** are minimal builds with no Newlib dependencies (only libgcc). They use integer-only arithmetic and have no syscall overhead, resulting in smaller binaries.

**REPL_NEWLIB mode** uses full Newlib for syscall-based I/O and supports floating-point operations.

## Running

In the emulator's root directory. Prebuilt binary:
```bash
./riscv-emu.py --raw-tty --ram-size=4096 prebuilt/micropython.elf 
```

Compiled binary, REPL over stdio (REPL_NEWLIB default build mode):
```bash
./riscv-emu.py --raw-tty --ram-size=4096 advanced/micropython/port-riscv-emu.py/build/firmware.elf
```

Compiled binary, headless (HEADLESS build mode):
```bash
./riscv-emu.py ---ram-size=4096 advanced/micropython/port-riscv-emu.py/build/firmware.elf
```

Compiled binary, REPL over UART (REPL_UART build mode):
```bash
./riscv-emu.py ---ram-size=4096 --uart advanced/micropython/port-riscv-emu.py/build/firmware.elf
```
And connect to MicroPython using your favorite terminal program:
```bash
screen /dev/ttys007 115200
```
