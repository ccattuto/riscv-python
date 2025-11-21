# MicroPython Port - Build Modes

This MicroPython port supports 4 configurable build modes, selectable at compile time via the `MODE` Makefile variable.

## Overview

| Mode | Description | Newlib | I/O Method | REPL | Frozen Script | Use Case |
|------|-------------|--------|------------|------|---------------|----------|
| **REPL_SYSCALL** | Interactive REPL with syscalls | ✅ Yes | read()/write() syscalls | ✅ Yes | ❌ No | Development, testing |
| **EMBEDDED_SILENT** | Run frozen script, no I/O | ❌ No | Silent (no-op) | ❌ No | ✅ Yes | Bare-metal, computation only |
| **REPL_UART** | Interactive REPL over UART | ❌ No | UART MMIO | ✅ Yes | ❌ No | Embedded with UART |
| **EMBEDDED_UART** | Frozen script + UART REPL | ❌ No | UART MMIO | ✅ Yes | ✅ Yes | Embedded init + debug |

---

## Mode 1: REPL_SYSCALL (Default)

**Current behavior** - Interactive REPL using system calls for I/O.

### Build
```bash
cd port-riscv-emu.py
make MODE=REPL_SYSCALL
# or just
make
```

### Run
```bash
../../riscv-emu.py --raw-tty --ram-size=4096 build/firmware.elf
```

### Features
- Full interactive REPL
- Uses `read(0)` and `write(1)` syscalls (ecall to emulator)
- Links against Newlib
- Welcome message on startup
- Standard Python print() and input()

### Memory Layout
- Newlib linked (includes printf, malloc stubs, etc.)
- Uses syscalls for all I/O
- GC heap: 2MB fixed (defined in linker)
- Stack: 512KB

---

## Mode 2: EMBEDDED_SILENT

**Zero syscalls** - Runs a frozen Python script with no I/O.

### Build
```bash
cd port-riscv-emu.py
make MODE=EMBEDDED_SILENT FROZEN_SCRIPT=startup.py clean all
```

### Run
```bash
../../riscv-emu.py --ram-size=4096 build/firmware.elf
```

### Features
- Executes embedded Python script at startup
- **No syscalls** - can run in completely bare-metal environment
- No Newlib - smaller binary
- Silent mode: all print() output discarded
- No REPL - exits after script completes
- Smallest binary size

### Use Cases
- Pure computation (crypto, algorithms, data processing)
- Environments without I/O devices
- ROM-based systems
- Deterministic embedded scripts

### Script Embedding
The Python script specified by `FROZEN_SCRIPT` is compiled to bytecode and embedded in the firmware binary at build time.

**Note**: Frozen module support (TODO) will be added to execute the embedded script.

---

## Mode 3: REPL_UART

**UART MMIO** - Interactive REPL over memory-mapped UART, no syscalls.

### Build
```bash
cd port-riscv-emu.py
make MODE=REPL_UART clean all
```

### Run
```bash
# Start emulator with UART peripheral
../../riscv-emu.py --uart --ram-size=4096 build/firmware.elf

# The emulator will print the PTY device name, e.g.:
# [UART] PTY created: /dev/pts/X

# In another terminal, connect to the UART:
screen /dev/pts/X
# or
picocom /dev/pts/X
```

### Features
- Full interactive REPL over UART
- **No syscalls** - all I/O via MMIO registers
- UART at memory address 0x10000000
- No Newlib - smaller binary
- Welcome message on startup
- Standard Python REPL experience

### UART Register Map
```
Base Address: 0x10000000

Offset  | Register | Access | Description
--------|----------|--------|---------------------------
0x00    | TX       | Write  | Write byte to transmit
0x04    | RX       | Read   | Read received byte
                             | Bit 31 = 1 if no data available
```

### Use Cases
- Embedded systems with UART
- Minimal I/O overhead
- Hardware without full syscall support
- Smaller binary than REPL_SYSCALL mode

---

## Mode 4: EMBEDDED_UART

**Init script + UART REPL** - Runs frozen script then drops to UART REPL.

### Build
```bash
cd port-riscv-emu.py
make MODE=EMBEDDED_UART FROZEN_SCRIPT=startup.py clean all
```

### Run
```bash
# Start emulator with UART peripheral
../../riscv-emu.py --uart --ram-size=4096 build/firmware.elf

# Connect to PTY in another terminal
screen /dev/pts/X
```

### Features
- Executes embedded initialization script first
- Then starts interactive REPL over UART
- **No syscalls** - all I/O via UART MMIO
- No Newlib - smaller binary
- Persistent state from init script available in REPL

### Use Cases
- Embedded systems requiring initialization
- Device configuration + interactive debug
- Boot scripts with fallback to REPL
- Production systems with debug console

### Example Workflow
1. `startup.py` initializes hardware, loads config, starts services
2. REPL starts for debugging/inspection
3. Can examine variables, test functions, modify behavior
4. Production build can disable REPL by switching to EMBEDDED_SILENT

---

## Implementation Details

### Architecture

The mode system is implemented through:

1. **Compile-time selection** (`Makefile`)
   - `MODE` variable selects configuration
   - Conditional source file inclusion
   - Different linker scripts
   - MODE flag passed to C preprocessor

2. **Configuration** (`mpconfigport.h`)
   - Mode constants defined
   - Frozen module support enabled for embedded modes
   - Conditional feature flags

3. **Conditional execution** (`main.c`)
   - Welcome message for REPL modes only
   - Frozen script execution for embedded modes
   - REPL started based on mode

4. **HAL abstraction** (mphalport_*.c)
   - `mphalport.c` - syscalls (Mode 1)
   - `mphalport_uart.c` - UART MMIO (Modes 3, 4)
   - `mphalport_silent.c` - no-op stubs (Mode 2)

5. **Startup code**
   - `start_newlib.S` - Newlib initialization (Mode 1)
   - `start_nolib.S` - Minimal startup (Modes 2, 3, 4)

6. **Linker scripts**
   - `linker_newlib.ld` - With Newlib heap (Mode 1)
   - `linker_nolib.ld` - No Newlib, simpler layout (Modes 2, 3, 4)

### File Map

| File | Mode 1 | Mode 2 | Mode 3 | Mode 4 |
|------|--------|--------|--------|--------|
| main.c | ✅ | ✅ | ✅ | ✅ |
| mphalport.c | ✅ | ❌ | ❌ | ❌ |
| mphalport_uart.c | ❌ | ❌ | ✅ | ✅ |
| mphalport_silent.c | ❌ | ✅ | ❌ | ❌ |
| minimal_stubs.c | ✅ | ❌ | ❌ | ❌ |
| minimal_nolib.c | ❌ | ✅ | ✅ | ✅ |
| start_newlib.S | ✅ | ❌ | ❌ | ❌ |
| start_nolib.S | ❌ | ✅ | ✅ | ✅ |
| syscalls_newlib.S | ✅ | ❌ | ❌ | ❌ |
| linker_newlib.ld | ✅ | ❌ | ❌ | ❌ |
| linker_nolib.ld | ❌ | ✅ | ✅ | ✅ |

### Memory Allocation

All modes use **MicroPython's garbage collector** with a fixed 2MB heap:
- Defined in linker script: `.gc_heap` section
- Initialized with `gc_init(&_gc_heap_start, &_gc_heap_end)`
- **No sbrk dependency** - heap is pre-allocated
- Newlib's malloc/free are NOT used by MicroPython core

### Syscall Dependencies

| Component | Mode 1 | Mode 2 | Mode 3 | Mode 4 |
|-----------|--------|--------|--------|--------|
| GC/malloc | ❌ None | ❌ None | ❌ None | ❌ None |
| stdout | ✅ write(1) | ❌ None | ❌ None | ❌ None |
| stdin | ✅ read(0) | ❌ None | ❌ None | ❌ None |
| Newlib | ✅ sbrk, etc | ❌ None | ❌ None | ❌ None |

**Summary**: Modes 2, 3, 4 have **zero syscall dependencies** and can run in completely bare-metal environments.

---

## Build System

### Makefile Variables

```makefile
MODE=<mode>          # REPL_SYSCALL, EMBEDDED_SILENT, REPL_UART, EMBEDDED_UART
FROZEN_SCRIPT=<path> # Path to Python script to embed (Modes 2, 4)
DEBUG=1              # Enable debug build (default: optimized)
RVM=1                # Enable RISC-V M extension (multiply/divide)
RVA=1                # Enable RISC-V A extension (atomic)
RVC=1                # Enable RISC-V C extension (compressed)
```

### Examples

```bash
# Default mode (REPL with syscalls)
make

# Embedded silent mode with custom script
make MODE=EMBEDDED_SILENT FROZEN_SCRIPT=my_app.py clean all

# UART REPL with debug symbols
make MODE=REPL_UART DEBUG=1 clean all

# Embedded UART with all RISC-V extensions
make MODE=EMBEDDED_UART RVM=1 RVA=1 RVC=1 clean all
```

### Clean Builds

**Always use `clean all` when changing MODE** to ensure all source files are recompiled with correct configuration:

```bash
make MODE=REPL_UART clean all
```

---

## TODO: Frozen Module Support

Currently, the frozen script execution is marked as TODO in `main.c:32-33`. To complete this:

1. Enable MicroPython's mpy-tool.py integration
2. Generate `_frozen_mpy.c` from `FROZEN_SCRIPT`
3. Link frozen bytecode into binary
4. Call `pyexec_frozen_module()` in main.c

Alternative approaches:
- Use `mp_lexer_new_from_str_len()` with script embedded as C string
- Implement simple script loader from memory

---

## Binary Size Comparison

Estimated sizes (to be measured after building):

| Mode | Newlib | Estimated Size | Notes |
|------|--------|---------------|-------|
| REPL_SYSCALL | Yes | ~500 KB | Largest (Newlib + printf) |
| EMBEDDED_SILENT | No | ~350 KB | Smallest (no I/O, no Newlib) |
| REPL_UART | No | ~400 KB | Medium (UART HAL, no Newlib) |
| EMBEDDED_UART | No | ~420 KB | Medium (frozen + UART) |

---

## Testing

### Mode 1 - REPL_SYSCALL
```bash
make clean all
../../riscv-emu.py --raw-tty --ram-size=4096 build/firmware.elf
# Should see: "Welcome to MicroPython on RISC-V!"
# Type: print("Hello")
```

### Mode 2 - EMBEDDED_SILENT
```bash
make MODE=EMBEDDED_SILENT FROZEN_SCRIPT=startup.py clean all
../../riscv-emu.py --ram-size=4096 build/firmware.elf
# Should run silently and exit (once frozen module support is complete)
```

### Mode 3 - REPL_UART
```bash
make MODE=REPL_UART clean all
# Terminal 1:
../../riscv-emu.py --uart --ram-size=4096 build/firmware.elf
# Note the PTY device shown

# Terminal 2:
screen /dev/pts/X  # Replace X with actual number
# Should see REPL prompt
```

### Mode 4 - EMBEDDED_UART
```bash
make MODE=EMBEDDED_UART FROZEN_SCRIPT=startup.py clean all
# Terminal 1:
../../riscv-emu.py --uart --ram-size=4096 build/firmware.elf

# Terminal 2:
screen /dev/pts/X
# Should see startup script output, then REPL prompt
```

---

## Troubleshooting

### MicroPython submodule not initialized
```bash
cd ../micropython
git submodule update --init
```

### Build errors about missing files
Ensure you're in the correct directory:
```bash
cd port-riscv-emu.py
```

### UART connection issues
Check the PTY device name in emulator output and ensure screen/picocom has permissions:
```bash
ls -l /dev/pts/X
sudo usermod -a -G dialout $USER  # If needed
```

### MODE changes not taking effect
Always clean before switching modes:
```bash
make MODE=<new_mode> clean all
```

---

## Future Enhancements

1. **Frozen module system** - Complete the script embedding
2. **Multiple frozen modules** - Support importing frozen libraries
3. **Dynamic script loading** - Option 2A from original analysis (file-based loading)
4. **Flash emulation** - Persistent storage for scripts
5. **Additional peripherals** - GPIO, SPI, I2C via MMIO
6. **Power management** - WFI-based sleep in silent mode
7. **Custom allocators** - Fine-tune memory for constrained environments

---

## References

- MicroPython documentation: https://docs.micropython.org/
- RISC-V specifications: https://riscv.org/technical/specifications/
- Newlib documentation: https://sourceware.org/newlib/
- Emulator source: ../../riscv-emu.py
- Peripheral implementations: ../../peripherals.py
