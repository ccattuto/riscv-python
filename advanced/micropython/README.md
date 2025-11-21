# MicroPython Port for RISC-V Emulator

This is a MicroPython port for the pure-Python RISC-V emulator, supporting multiple build modes for different embedded scenarios.

## Build Modes

The port supports 4 configurable modes, selected at compile time via the `MODE` variable:

| Mode | Description | I/O Method | Float Support | REPL | Frozen Script |
|------|-------------|------------|---------------|------|---------------|
| **REPL_SYSCALL** | Interactive development | read()/write() syscalls | ✅ Yes | ✅ Yes | ❌ No |
| **EMBEDDED_SILENT** | Embedded script only | Silent (no I/O) | ❌ No | ❌ No | ✅ Yes |
| **REPL_UART** | Interactive over UART | UART MMIO (0x10000000) | ❌ No | ✅ Yes | ❌ No |
| **EMBEDDED_UART** | Script + UART REPL | UART MMIO (0x10000000) | ❌ No | ✅ Yes | ✅ Yes |

All modes support:
- 64-bit integers (for uctypes and large values)
- uctypes module (memory-mapped I/O)
- struct, array, collections, re modules
- Full Python language features (except floats in non-REPL_SYSCALL modes)

---

## Quick Start

### Mode 1: REPL_SYSCALL (Default)

Standard interactive REPL with full float support.

**Build:**
```bash
cd port-riscv-emu.py
make
# or explicitly:
make MODE=REPL_SYSCALL
```

**Run:**
```bash
../../riscv-emu.py --raw-tty --ram-size=4096 build/firmware.elf
```

You'll see:
```
Welcome to MicroPython on RISC-V!
>>> print("Hello World!")
Hello World!
>>> import math
>>> math.pi
3.141593
```

---

### Mode 2: EMBEDDED_SILENT

Run a frozen Python script with no I/O (for pure computation tasks).

**Build with a script:**
```bash
make MODE=EMBEDDED_SILENT FROZEN_SCRIPT=startup.py clean all
```

**Run:**
```bash
../../riscv-emu.py --ram-size=4096 build/firmware.elf
```

The script runs silently and exits. Use this mode for:
- Computation-only tasks
- Environments without I/O devices
- Minimal binary size

**Example script (startup.py):**
```python
# Integer-only computation
result = sum([i**2 for i in range(100)])
# Result stored in memory, can be read by emulator
```

---

### Mode 3: REPL_UART

Interactive REPL over memory-mapped UART (no syscalls, integer-only).

**Build:**
```bash
make MODE=REPL_UART clean all
```

**Run:**
```bash
# Terminal 1: Start emulator with UART
../../riscv-emu.py --uart --ram-size=4096 build/firmware.elf

# Note the PTY device shown, e.g.: [UART] PTY created: /dev/pts/3

# Terminal 2: Connect to the UART
screen /dev/pts/3
# or
picocom /dev/pts/3
```

You'll see the MicroPython REPL over the UART:
```
Welcome to MicroPython on RISC-V!
>>> print([i*i for i in range(10)])
[0, 1, 4, 9, 16, 25, 36, 49, 64, 81]
>>> import uctypes
```

**Note:** This mode has no float support (integer-only), but is perfect for embedded systems with UART.

---

### Mode 4: EMBEDDED_UART

Run a frozen script, then start REPL over UART.

**Build:**
```bash
make MODE=EMBEDDED_UART FROZEN_SCRIPT=startup.py clean all
```

**Run:**
```bash
# Terminal 1: Start emulator
../../riscv-emu.py --uart --ram-size=4096 build/firmware.elf

# Terminal 2: Connect to UART
screen /dev/pts/3
```

The frozen script executes first, then you get an interactive REPL. Perfect for:
- Initialization scripts followed by debug console
- Automated setup with interactive testing
- Production systems with maintenance access

---

## Frozen Scripts

Frozen scripts are Python files compiled to bytecode and embedded in the firmware at build time.

### How It Works

1. **Specify script** via `FROZEN_SCRIPT` variable
2. **Build** - script is compiled to `.mpy` bytecode
3. **Embedded** - bytecode converted to C and linked into firmware
4. **Executed** - runs automatically at startup (modes 2 and 4)

### Example: Custom Frozen Script

Create `my_app.py`:
```python
import struct
import array

print("My Application Starting...")

# Configuration
config = {
    'version': 1,
    'mode': 'production',
    'buffer_size': 1024
}

print(f"Config: {config}")

# Do work
data = array.array('i', range(100))
total = sum(data)
print(f"Computed sum: {total}")

print("Application complete")
```

Build and run:
```bash
make MODE=EMBEDDED_UART FROZEN_SCRIPT=my_app.py clean all
../../riscv-emu.py --uart --ram-size=4096 build/firmware.elf
# Connect via screen - see app output, then get REPL
```

---

## Using uctypes for Hardware Access

The `uctypes` module allows direct memory-mapped I/O access from Python, perfect for embedded systems.

### Example: UART via uctypes

The included `uart_demo.py` demonstrates uctypes for UART control:

```python
import uctypes

# Define UART registers at 0x10000000
UART_BASE = 0x10000000
uart_layout = {
    "TX": uctypes.UINT32 | 0x00,  # Transmit
    "RX": uctypes.UINT32 | 0x04,  # Receive
}

# Create UART structure
uart = uctypes.struct(UART_BASE, uart_layout, uctypes.LITTLE_ENDIAN)

# Write to UART
def uart_print(s):
    for c in s:
        uart.TX = ord(c)

uart_print("Hello from Python!\r\n")

# Read from UART (non-blocking)
rx_val = uart.RX
if not (rx_val & 0x80000000):
    print(f"Received: {chr(rx_val & 0xFF)}")
```

**Run the demo:**
```bash
make MODE=EMBEDDED_SILENT FROZEN_SCRIPT=uart_demo.py clean all
../../riscv-emu.py --uart --ram-size=4096 build/firmware.elf
# Connect via screen to see output
```

### Python REPL via uctypes

The included `uart_repl.py` implements a full REPL using only uctypes (no C-level I/O):

```bash
make MODE=EMBEDDED_SILENT FROZEN_SCRIPT=uart_repl.py clean all
../../riscv-emu.py --uart --ram-size=4096 build/firmware.elf
# Connect via screen - get a Python-implemented REPL!
```

This demonstrates pure-Python hardware control without any syscalls.

---

## Advanced Build Options

### RISC-V Extensions

```bash
# Default: RV32IM (Integer + Multiply/Divide)
make

# Enable Compressed instructions (RV32IMC)
make RVC=1

# Enable Atomic instructions (RV32IMA)
make RVA=1

# All extensions (RV32IMAC)
make RVM=1 RVA=1 RVC=1
```

### Debug Build

```bash
make DEBUG=1
```

### Custom Frozen Script

```bash
make MODE=EMBEDDED_UART FROZEN_SCRIPT=/path/to/my_script.py clean all
```

**Important:** Always use `clean all` when changing modes to ensure proper rebuild.

---

## Examples

### 1. Interactive Math (REPL_SYSCALL)

```bash
make MODE=REPL_SYSCALL
../../riscv-emu.py --raw-tty --ram-size=4096 build/firmware.elf
```

```python
>>> import math
>>> math.sqrt(2)
1.414214
>>> [math.sin(x/10) for x in range(10)]
```

### 2. Data Processing Script (EMBEDDED_SILENT)

Create `process.py`:
```python
import array

# Process sensor data
readings = array.array('i', [23, 45, 67, 12, 89, 34])
average = sum(readings) // len(readings)
maximum = max(readings)
minimum = min(readings)

# Results in memory for emulator to read
```

```bash
make MODE=EMBEDDED_SILENT FROZEN_SCRIPT=process.py clean all
../../riscv-emu.py --ram-size=4096 build/firmware.elf
```

### 3. Hardware Control (REPL_UART + uctypes)

```bash
make MODE=REPL_UART clean all
../../riscv-emu.py --uart --ram-size=4096 build/firmware.elf
# In another terminal:
screen /dev/pts/X
```

In the REPL:
```python
>>> import uctypes
>>> # Define memory-mapped LED at 0x20000000
>>> led = uctypes.struct(0x20000000, {"ctrl": uctypes.UINT32 | 0}, uctypes.LITTLE_ENDIAN)
>>> led.ctrl = 1  # Turn on LED
>>> led.ctrl = 0  # Turn off LED
```

### 4. Bootloader + Debug Console (EMBEDDED_UART)

Create `bootloader.py`:
```python
import struct

print("Bootloader v1.0")
print("Checking system...")

# Check configuration
config_addr = 0x1000
config = struct.unpack_from('III', bytes(12), 0)
print(f"Config: {config}")

print("Boot complete. Entering debug mode...")
```

```bash
make MODE=EMBEDDED_UART FROZEN_SCRIPT=bootloader.py clean all
../../riscv-emu.py --uart --ram-size=4096 build/firmware.elf
# Bootloader runs, then get interactive REPL for debugging
```

---

## Troubleshooting

### Build Errors

**"micropython submodule not initialized"**
```bash
cd ../micropython
git submodule update --init
cd ../port-riscv-emu.py
```

**"mpy-cross not found"**
Build mpy-cross tool:
```bash
cd ../micropython/mpy-cross
make
cd ../../port-riscv-emu.py
```

### Runtime Issues

**"UART not working"**
- Ensure emulator is started with `--uart` flag
- Check the PTY device name in emulator output
- Verify terminal has correct permissions

**"Frozen script not executing"**
- Verify FROZEN_SCRIPT path is correct
- Ensure you did `make clean all` after changing script
- Check script has no syntax errors (test locally first)

**"Out of memory"**
- Increase RAM: `--ram-size=8192` (8MB)
- GC heap is fixed at 2MB in linker script
- Reduce script complexity or data structures

---

## Technical Details

### Memory Layout

```
0x00000000: .text (code)
0x0000xxxx: .rodata (constants)
0x0000xxxx: .data (initialized globals)
0x0000xxxx: .bss (uninitialized globals)
0x0000xxxx: GC heap (2MB for MicroPython)
0x00200000: Newlib heap start
0x003C0000: Stack (512KB from top of 4MB RAM)
0x00400000: Top of RAM (4MB default)
```

### UART Register Map

```
Base: 0x10000000

+0x00  TX (write-only)  - Write byte to transmit
+0x04  RX (read-only)   - Read received byte
                        - Bit 31: 1 = no data, 0 = data available
                        - Bits 7-0: received byte
```

### Frozen Module Details

1. **Python → .mpy**: `mpy-cross` compiles Python to bytecode
2. **.mpy → C**: `mpy-tool.py` generates `_frozen_mpy.c`
3. **C → binary**: Compiled and linked into firmware
4. **Runtime**: `pyexec_frozen_module("startup", false)` executes it

Module name is derived from filename: `startup.py` → `"startup"`

---

## File Structure

```
port-riscv-emu.py/
├── main.c                  # Entry point, mode-conditional execution
├── mpconfigport.h          # MicroPython configuration, mode definitions
├── Makefile                # Build system with MODE selection
│
├── mphalport.c             # HAL: syscall I/O (Mode 1)
├── mphalport_uart.c        # HAL: UART MMIO (Modes 3,4)
├── mphalport_silent.c      # HAL: silent/no-op (Mode 2)
│
├── start_newlib.S          # Startup code (Newlib initialization)
├── syscalls_newlib.S       # Syscall interface
├── linker_newlib.ld        # Linker script
│
├── startup.py              # Example frozen script
├── uart_demo.py            # uctypes UART demo
├── uart_repl.py            # Python REPL via uctypes
│
└── README.md               # This file
```

---

## Resources

- **MicroPython Documentation**: https://docs.micropython.org/
- **uctypes module**: https://docs.micropython.org/en/latest/library/uctypes.html
- **Frozen modules**: https://docs.micropython.org/en/latest/reference/manifest.html
- **Emulator**: ../../riscv-emu.py
- **Detailed mode docs**: README_MODES.md

---

## License

This port follows the MicroPython license (MIT). See the MicroPython repository for details.
