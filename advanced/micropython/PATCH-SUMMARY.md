# MicroPython 4-Mode Implementation Patch

**File:** `micropython-4-modes-implementation.patch`
**Size:** 48KB (1695 lines)
**Base Commit:** e58127f (MicroPython: added uctypes support)
**Final Commit:** 7c60bcb (MicroPython: use CORE_FEATURES ROM level)

## Overview

This patch implements 4 configurable build modes for the MicroPython RISC-V emulator port, enabling both interactive development and embedded script execution with different I/O backends.

## What's Included

### 1. New Build Modes (4 total)

- **REPL_SYSCALL**: Interactive REPL with syscalls and float support (original behavior)
- **EMBEDDED_SILENT**: Frozen script execution, no I/O, integer-only
- **REPL_UART**: Interactive REPL over memory-mapped UART, integer-only
- **EMBEDDED_UART**: Frozen script + UART REPL, integer-only

### 2. New Source Files

#### HAL Implementations
- `mphalport_silent.c` - Silent I/O for embedded mode (no output)
- `mphalport_uart.c` - UART MMIO I/O (memory-mapped at 0x10000000)

#### Demo Scripts
- `uart_demo.py` - Simple UART output demo using uctypes
- `uart_repl.py` - Full Python REPL implemented in Python using uctypes
- `startup.py` - Default startup script for embedded modes

### 3. Modified Files

#### Core Configuration
- `mpconfigport.h` - Mode-specific configurations:
  - Float support only for REPL_SYSCALL
  - Frozen module support for embedded modes
  - CORE_FEATURES ROM level with explicit module enablement
  - Math module conditional compilation

#### Build System
- `Makefile` - Mode selection and frozen module compilation:
  - MODE variable (REPL_SYSCALL, EMBEDDED_SILENT, REPL_UART, EMBEDDED_UART)
  - FROZEN_SCRIPT variable for script embedding
  - HAL selection based on mode
  - mpy-cross integration for frozen modules

#### Runtime
- `main.c` - Mode-dependent execution flow:
  - Execute frozen module in embedded modes
  - Start REPL in interactive modes
  - Combined execution for EMBEDDED_UART

### 4. Documentation
- `README.md` - Comprehensive 469-line guide covering:
  - All 4 build modes with examples
  - Frozen script compilation and usage
  - uctypes UART programming examples
  - Troubleshooting guide
  - Technical reference (memory layout, UART registers)

## Key Technical Decisions

### 1. Float Support Strategy
- Only REPL_SYSCALL mode includes float support (avoids libm dependency in embedded builds)
- Integer-only modes use CORE_FEATURES ROM level to exclude math module
- Explicit module configuration prevents accidental math module inclusion

### 2. Newlib Usage
- All modes use Newlib for consistency and to provide:
  - libgcc (for 64-bit integer operations)
  - libc (for standard functions like strtoll)
  - libm (only used by REPL_SYSCALL for float operations)
- Simplified from initial multi-startup-file approach

### 3. Frozen Module System
- Uses MicroPython's standard frozen .mpy bytecode system
- Python script → .mpy bytecode → C code → linked into binary
- Enables zero-overhead script embedding

### 4. UART MMIO Design
- Memory-mapped UART at 0x10000000 (matches emulator --uart mode)
- Simple register interface: TX at +0x00, RX at +0x04
- Accessible from both C (HAL) and Python (uctypes)

## Build Sizes (Approximate)

- REPL_SYSCALL: ~180KB (with float support)
- EMBEDDED_SILENT: ~160KB (integer-only, minimal I/O)
- REPL_UART: ~165KB (integer-only with UART)
- EMBEDDED_UART: ~165KB (integer-only with UART + frozen script)

## Applying the Patch

From the repository root:

```bash
# Review the patch
cat advanced/micropython/micropython-4-modes-implementation.patch

# Apply the patch
git apply advanced/micropython/micropython-4-modes-implementation.patch

# Or use patch command
patch -p1 < advanced/micropython/micropython-4-modes-implementation.patch
```

## Testing the Implementation

### Build All Modes
```bash
cd advanced/micropython/port-riscv-emu.py

# Mode 1: REPL with syscalls
make MODE=REPL_SYSCALL clean all

# Mode 2: Embedded silent
make MODE=EMBEDDED_SILENT FROZEN_SCRIPT=uart_demo.py clean all

# Mode 3: UART REPL
make MODE=REPL_UART clean all

# Mode 4: Embedded + UART REPL
make MODE=EMBEDDED_UART FROZEN_SCRIPT=startup.py clean all
```

### Run Examples
```bash
# Mode 1: Standard REPL
../../riscv-emu.py --raw-tty --ram-size=4096 build/firmware.elf

# Mode 2: Silent embedded script
../../riscv-emu.py --uart --ram-size=4096 build/firmware.elf
# Connect to PTY shown in emulator output

# Mode 3: UART REPL (integer-only)
../../riscv-emu.py --uart --ram-size=4096 build/firmware.elf
# Connect to PTY, test: >>> 2**100

# Mode 4: Startup script then REPL
../../riscv-emu.py --uart --ram-size=4096 build/firmware.elf
# Connect to PTY, see startup message, then REPL
```

## Commit History

The patch encompasses these commits:

1. `81429c2` - Add 4 configurable build modes for script embedding
2. `3d88f2e` - Implement frozen module script execution
3. `c45d166` - Fix linking for non-Newlib modes
4. `be3ad81` - Disable floats for non-Newlib modes
5. `d11afcf` - Fix float macro redefinition errors
6. `b5614c8` - Add libc and libgcc for non-Newlib modes
7. `adb3a53` - Fix start_bare.S to initialize BSS and GP
8. `6963ea7` - Simplify build to use Newlib for all modes
9. `369c848` - Add uctypes UART demos for embedded mode
10. `d529fc3` - Comprehensive README with build modes and examples
11. `5a53516` - Fix math module config for non-float modes
12. `f581dc0` - Add multiple layers of math module override
13. `7c60bcb` - Use CORE_FEATURES ROM level to prevent math module

## Known Limitations

1. **macOS mpy-cross Build**: May require `-Wno-error=gnu-folding-constant` flag
2. **PTY Access**: Requires appropriate permissions for `/dev/pts/` devices
3. **Float Operations**: Not available in EMBEDDED_SILENT, REPL_UART, EMBEDDED_UART modes
4. **Frozen Scripts**: Require mpy-cross to be built first

## Architecture Notes

### Mode Configuration Flow
```
Makefile (MODE variable)
    ↓
CFLAGS (-DMICROPY_PORT_MODE=MODE_XXX)
    ↓
mpconfigport.h (conditional compilation)
    ↓
main.c (runtime behavior)
```

### Frozen Module Flow
```
script.py
    ↓ mpy-cross
script.mpy (bytecode)
    ↓ mpy-tool.py
_frozen_mpy.c (C code)
    ↓ gcc
firmware.elf (linked binary)
```

## Future Enhancements

Potential additions not included in this patch:

- Additional HAL backends (SPI, I2C MMIO)
- Power management modes
- Interrupt handling framework
- Flash emulation for persistent storage
- Watchdog timer support

## Questions or Issues?

Refer to the comprehensive README.md for detailed documentation, or check the commit history for implementation rationale.
