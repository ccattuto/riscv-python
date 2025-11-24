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

### 1. REPL_SYSCALL (default)
Interactive REPL on host's stdio:
```bash
make
# or explicitly
make MODE=REPL_SYSCALL
```

### 2. HEADLESS
Executes a frozen Python script with no stdio (requires `FROZEN_SCRIPT`, defaults to `startup.py`):
```bash
make MODE=HEADLESS FROZEN_SCRIPT=startup.py
```

### 3. UART
REPL over emulated UART, with an optional frozen initialization script (requires `FROZEN_SCRIPT`, defaults to `startup.py`):
```bash
make MODE=UART FROZEN_SCRIPT=startup.py
```

## Build Options

- `MODE` - Build mode: `REPL_SYSCALL` (default), `HEADLESS`, or `UART`
- `FROZEN_SCRIPT` - Python script to freeze into firmware (required for HEADLESS, optional for UART, defaults to `startup.py`)
- `RVM=1` - Enable RISC-V M extension (multiply/divide, default: enabled)
- `RVA=0` - Enable RISC-V A extension (atomics, default: disabled)
- `RVC=0` - Enable RISC-V C extension (compressed instructions, default: disabled)

## Running

In the emulator's root directory. Prebuilt binary:
```bash
./riscv-emu.py --raw-tty --ram-size=4096 prebuilt/micropython.elf 
```

Compiled binary, REPL over stdio (REPL_SYSCALL default build mode):
```bash
./riscv-emu.py --raw-tty --ram-size=4096 advanced/micropython/port-riscv-emu.py/build/firmware.elf
```

Compiled binary, headless (HEADLESS build mode):
```bash
./riscv-emu.py ---ram-size=4096 advanced/micropython/port-riscv-emu.py/build/firmware.elf
```

Compiled binary, REPL over UART (UART build mode):
```bash
./riscv-emu.py ---ram-size=4096 --uart advanced/micropython/port-riscv-emu.py/build/firmware.elf
```
And connect to MicroPython using your favorite terminal program:
```bash
screen /dev/ttys007 115200
```
