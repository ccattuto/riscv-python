# MicroPython Port - Build Modes

This MicroPython port supports 3 configurable build modes, selectable at compile time via the `MODE` Makefile variable.

## Overview

| Mode | Description | Float Support | I/O Method | REPL | Frozen Script | Use Case |
|------|-------------|---------------|------------|------|---------------|----------|
| **REPL_SYSCALL** | Interactive REPL with syscalls | ✅ Yes | read()/write() syscalls | ✅ Yes | ❌ No | Development, testing |
| **HEADLESS** | Run frozen script, no stdio REPL | ❌ No | Silent stdio (script can use machine.mem32, etc.) | ❌ No | ✅ Yes | Bare-metal, embedded apps |
| **UART** | Frozen init script + UART REPL | ❌ No | UART MMIO (machine.mem32) | ✅ Yes | ✅ Yes (optional) | Embedded with UART debug |

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

## Mode 2: HEADLESS

**No stdio REPL** - Runs a frozen Python script with no stdio interface. The script can still perform I/O via `machine.mem32` or other mechanisms.

### Build
```bash
cd port-riscv-emu.py
make MODE=HEADLESS FROZEN_SCRIPT=startup.py clean all
```

### Run
```bash
../../riscv-emu.py --ram-size=4096 build/firmware.elf
```

### Features
- Executes embedded Python script at startup
- Silent stdio: print() and input() are no-ops
- Script can still do I/O via `machine.mem32` for MMIO peripherals
- No REPL - exits after script completes
- Integer-only (no float support) - smaller binary

### Use Cases
- Embedded applications with custom I/O (UART, SPI, I2C via MMIO)
- Pure computation (crypto, algorithms, data processing)
- ROM-based systems
- Deterministic embedded scripts without interactive debugging

### Script Embedding
The Python script specified by `FROZEN_SCRIPT` is compiled to bytecode and embedded in the firmware binary at build time.

**Note**: Frozen module support (TODO) will be added to execute the embedded script.

---

## Mode 3: UART

**Frozen init script + UART REPL** - Optionally runs a frozen initialization script, then starts an interactive REPL over memory-mapped UART.

### Build
```bash
cd port-riscv-emu.py
# With initialization script:
make MODE=UART FROZEN_SCRIPT=startup.py clean all

# Without initialization script (REPL only):
make MODE=UART FROZEN_SCRIPT= clean all
```

### Run
```bash
# Start emulator with UART peripheral
../../riscv-emu.py --uart --ram-size=4096 build/firmware.elf

# Connect to PTY in another terminal
screen /dev/pts/X
```

### Features
- Optionally executes frozen initialization script first (can be empty/omitted)
- Then starts interactive REPL over UART
- **No syscalls** - all I/O via UART MMIO using `machine.mem32`
- Integer-only (no float support) - smaller binary
- Persistent state from init script available in REPL
- UART at memory address 0x10000000 (TX) and 0x10000004 (RX)

### UART Register Map
```
Base Address: 0x10000000

Offset  | Register | Access | Description
--------|----------|--------|---------------------------
0x00    | TX       | Write  | Write byte to transmit
0x04    | RX       | Read   | Read received byte
                             | Bit 31 = 1 if no data available
```

Access via `machine.mem32[]` for proper word-aligned MMIO operations.

### Use Cases
- Embedded systems requiring initialization
- Device configuration + interactive debug
- Boot scripts with fallback to REPL
- Production systems with debug console

### Example Workflow
1. `startup.py` initializes hardware, loads config, starts services
2. REPL starts for debugging/inspection
3. Can examine variables, test functions, modify behavior
4. Production build can disable REPL by switching to HEADLESS mode

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
   - `start_newlib.S` - Newlib initialization (all modes)

6. **Linker scripts**
   - `linker_newlib.ld` - All modes use Newlib

### File Map

| File | REPL_SYSCALL | HEADLESS | UART |
|------|--------------|----------|------|
| main.c | ✅ | ✅ | ✅ |
| mphalport.c | ✅ | ❌ | ❌ |
| mphalport_uart.c | ❌ | ❌ | ✅ |
| mphalport_silent.c | ❌ | ✅ | ❌ |
| minimal_stubs.c | ✅ | ✅ | ✅ |
| shared/libc/printf.c | ✅ | ✅ | ✅ |
| start_newlib.S | ✅ | ✅ | ✅ |
| syscalls_newlib.S | ✅ | ✅ | ✅ |
| linker_newlib.ld | ✅ | ✅ | ✅ |

### Memory Allocation

All modes use **MicroPython's garbage collector** with a fixed 2MB heap:
- Defined in linker script: `.gc_heap` section
- Initialized with `gc_init(&_gc_heap_start, &_gc_heap_end)`
- **No sbrk dependency** - heap is pre-allocated
- Newlib's malloc/free are NOT used by MicroPython core

### Syscall Dependencies

| Component | REPL_SYSCALL | HEADLESS | UART |
|-----------|--------------|----------|------|
| GC/malloc | ❌ None | ❌ None | ❌ None |
| stdout | ✅ write(1) | ❌ No-op | ❌ UART MMIO |
| stdin | ✅ read(0) | ❌ No-op | ❌ UART MMIO |
| Newlib | ✅ Yes | ✅ Yes | ✅ Yes |

**Summary**: All modes use Newlib. REPL_SYSCALL mode uses syscalls for stdio. HEADLESS and UART modes use alternative I/O methods (no-op and MMIO respectively).

---

## Build System

### Makefile Variables

```makefile
MODE=<mode>          # REPL_SYSCALL, HEADLESS, UART
FROZEN_SCRIPT=<path> # Path to Python script to embed (HEADLESS, UART)
DEBUG=1              # Enable debug build (default: optimized)
RVM=1                # Enable RISC-V M extension (multiply/divide)
RVA=1                # Enable RISC-V A extension (atomic)
RVC=1                # Enable RISC-V C extension (compressed)
```

### Examples

```bash
# Default mode (REPL with syscalls)
make

# Headless mode with custom script
make MODE=HEADLESS FROZEN_SCRIPT=my_app.py clean all

# UART REPL with debug symbols
make MODE=UART DEBUG=1 clean all

# UART with initialization script and all RISC-V extensions
make MODE=UART FROZEN_SCRIPT=startup.py RVM=1 RVA=1 RVC=1 clean all
```

### Clean Builds

**Always use `clean all` when changing MODE** to ensure all source files are recompiled with correct configuration:

```bash
make MODE=UART clean all
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

| Mode | Float Support | Estimated Size | Notes |
|------|---------------|----------------|-------|
| REPL_SYSCALL | Yes | ~500 KB | Largest (float + math module) |
| HEADLESS | No | ~400 KB | Medium (integer-only) |
| UART | No | ~420 KB | Medium (integer-only + UART HAL) |

---

## Testing

### Mode 1 - REPL_SYSCALL
```bash
make clean all
../../riscv-emu.py --raw-tty --ram-size=4096 build/firmware.elf
# Should see: "Welcome to MicroPython on RISC-V!"
# Type: print("Hello")
```

### Mode 2 - HEADLESS
```bash
make MODE=HEADLESS FROZEN_SCRIPT=startup.py clean all
../../riscv-emu.py --ram-size=4096 build/firmware.elf
# Should run silently and exit after executing startup.py
```

### Mode 3 - UART
```bash
make MODE=UART FROZEN_SCRIPT=startup.py clean all
# Terminal 1:
../../riscv-emu.py --uart --ram-size=4096 build/firmware.elf
# Note the PTY device shown

# Terminal 2:
screen /dev/pts/X  # Replace X with actual number
# Should see startup script output (if provided), then REPL prompt
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
