# MicroPython port for riscv-emu.py

This is a MicroPython port that runs on the riscv-emu.py RISC-V emulator.

## Prerequisites

Before building, ensure the micropython-lib submodule is initialized:

```bash
cd ..
git submodule update --init lib/micropython-lib
```

Or use the MicroPython make target:

```bash
cd /path/to/micropython
make submodules
```

## Building

The port supports three build modes:

### 1. REPL_SYSCALL (default)
Interactive REPL using syscalls for I/O:
```bash
make
# or explicitly
make MODE=REPL_SYSCALL
```

### 2. HEADLESS
Executes a frozen Python script with no stdio (requires `FROZEN_SCRIPT`):
```bash
make MODE=HEADLESS FROZEN_SCRIPT=startup.py
```

### 3. UART
Frozen initialization script followed by UART REPL:
```bash
make MODE=UART FROZEN_SCRIPT=startup.py
```

## Build Options

- `MODE` - Build mode: `REPL_SYSCALL` (default), `HEADLESS`, or `UART`
- `FROZEN_SCRIPT` - Python script to freeze into firmware (required for HEADLESS, optional for UART)
- `DEBUG=1` - Build with debug symbols and no optimization
- `CROSS=1` - Cross-compile for RISC-V (default)
- `RVM=1` - Enable RISC-V M extension (multiply/divide, default: enabled)
- `RVA=0` - Enable RISC-V A extension (atomics, default: disabled)
- `RVC=0` - Enable RISC-V C extension (compressed instructions, default: disabled)

## Running

```bash
# Run the built firmware
build/firmware.elf
```

## Freezing Python Modules

To freeze Python scripts into the firmware, create or modify `manifest.py` in this directory. The manifest uses MicroPython's standard manifest system. See [MicroPython manifest documentation](https://docs.micropython.org/en/latest/reference/manifest.html) for details.

Example `manifest.py`:
```python
# Freeze a single script
freeze("$(PORT_DIR)", "startup.py")

# Freeze multiple scripts from a directory
freeze("$(PORT_DIR)/modules")

# Include modules from micropython-lib
require("asyncio")
```
