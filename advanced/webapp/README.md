# RISC-V Emulator - Browser Edition

A pure browser-based RISC-V (RV32IMAC) emulator powered by Pyodide and xterm.js.

## Features

- **Pure client-side**: No backend server needed, runs entirely in your browser
- **Full RV32IMAC support**: Base instruction set plus M (multiply/divide), A (atomics), and C (compressed instructions)
- **Interactive terminal**: Character-at-a-time input via xterm.js with raw TTY support
- **ELF and binary loading**: Load compiled programs directly from your filesystem
- **Debugging tools**: Optional tracing for syscalls, traps, and function calls
- **Timer support**: Machine timer interrupts for time-based programming
- **Performance**: ~200K-2M instructions/second typical performance

## Quick Start

1. **Serve the webapp directory**:
   ```bash
   cd advanced/webapp
   python3 -m http.server 8000
   ```

2. **Open in browser**:
   Navigate to `http://localhost:8000`

3. **Load a program**:
   - Click "Load ELF/BIN" and select a compiled RISC-V program
   - Programs must be compiled for RV32I (optionally with M, A, C extensions)

4. **Run**:
   - Click "Run" to start execution
   - Interact with the program via the terminal
   - Click "Stop" to interrupt execution
   - Click "Reset" to clear emulator state

## Building Programs

Programs must be compiled for RISC-V RV32I. Example using the riscv-gnu-toolchain:

```bash
# Simple program
riscv64-unknown-elf-gcc -march=rv32i -mabi=ilp32 \
    -nostartfiles -static -Tlinker.ld \
    --specs=nosys.specs -o program.elf program.c

# With multiply/divide support
riscv64-unknown-elf-gcc -march=rv32im -mabi=ilp32 \
    -nostartfiles -static -Tlinker.ld \
    --specs=nosys.specs -o program.elf program.c
```

See `../../tests/` for example programs.

## UI Controls

### Tracing Options
- **Syscalls**: Log all syscall operations (exit, read, write, sbrk, etc.)
- **Traps**: Log exceptions and interrupts
- **Functions**: Log function calls (requires ELF with symbols)

### Checking Options
- **Invariants**: Check CPU invariants (x0=0, PC bounds, stack bounds)
- **Memory bounds**: Validate all memory accesses
- **Text integrity**: Detect self-modifying code

### Features
- **Timer**: Enable machine timer interrupts (CSR mode)
- **RVC**: Enable compressed 16-bit instructions

### Configuration
- **Registers**: Comma-separated list of registers to log (e.g., "pc,sp,ra,a0")
- **RAM Size**: Emulated RAM in kilobytes (default: 1024 KB)

## Architecture

### Files Structure

```
webapp/
├── index.html              # Main page
├── css/
│   └── styles.css          # UI styling
├── js/
│   ├── main.js             # Pyodide orchestration & execution loop
│   ├── terminal.js         # Xterm.js terminal with I/O bridging
│   ├── fileloader.js       # FileAPI for loading ELF/bin files
│   └── controls.js         # UI option management
└── py/
    ├── browser_entry.py    # Python entry point for browser
    ├── browser_syscalls.py # Browser-adapted syscall handler
    ├── browser_logger.py   # Logger outputting to JS console
    └── peripherals.py      # Minimal peripherals (timer only)
```

### Dependencies

- **Pyodide** (v0.24.1+): Python runtime for WebAssembly
- **pyelftools**: ELF file parsing
- **xterm.js** (v5.3.0): Terminal emulator
- **Parent directory modules**: cpu.py, ram.py, machine.py, rvc.py (imported dynamically)

## Syscall Support

### Implemented Syscalls
- `exit` (93): Program termination
- `write` (64): Write to stdout/stderr → terminal
- `read` (63): Read from stdin ← terminal
- `sbrk` (214): Heap expansion
- `fstat` (80): File status (faked for stdin/stdout/stderr)
- `isatty` (89): TTY check (returns true for 0/1/2)
- `getpid` (172): Get PID (returns 1)
- `umask` (60): File creation mask

### Stubbed Syscalls (return -ENOSYS)
- File operations: `openat`, `close`, `lseek`, `mkdirat`, `unlinkat`
- Process control: `kill`

Programs relying on file I/O will fail. Future versions may support virtual filesystem.

## Performance

- **Chunked execution**: 10,000 instructions per frame (configurable in main.js)
- **Frame rate**: Target 60 FPS = ~600K instructions/second
- **Actual performance**: 200K - 2M IPS depending on browser and options enabled
- **Tracing overhead**: ~3x slower when logging is enabled

## Limitations (Pilot Version)

1. **No file I/O**: `open()`, `read()`, `write()` on files return `-ENOSYS`
2. **No block device**: No persistent storage emulation
3. **Single-threaded**: Execution on main thread (Web Worker support planned)
4. **No debugging UI**: No step-through or breakpoints yet
5. **No save/restore**: Cannot snapshot emulator state

## Browser Compatibility

Tested on:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

Requires modern JavaScript (ES6+) and WebAssembly support.

## Troubleshooting

### "Failed to initialize Pyodide"
- Check browser console for detailed errors
- Ensure internet connection (Pyodide loads from CDN)
- Try reloading the page

### "Error loading file"
- Verify file is valid ELF or binary
- Check file was compiled for RV32I (not RV64)
- Ensure file size < RAM size

### Terminal not responding
- Check browser console for errors
- Try clicking Reset and reloading the program
- Verify Ctrl-C works to stop execution

### Slow performance
- Disable tracing and checking options
- Reduce RAM size if not needed
- Try a different browser (Chrome typically fastest)

## Development

To modify the emulator:

1. **JavaScript changes**: Edit files in `js/` and reload page
2. **Python changes**: Edit files in `py/` and reload page (Pyodide fetches on startup)
3. **Core emulator changes**: Modify parent directory files (cpu.py, ram.py, machine.py)

## Future Enhancements

- Web Worker execution for better performance
- Virtual filesystem (IndexedDB-backed)
- Block device support
- Step-through debugging UI
- Breakpoints and memory inspector
- State save/restore to localStorage
- Preloaded example programs

## License

Same as parent project (see root directory).

## Credits

Built on the RISC-V emulator by Ciro Cattuto.
Uses Pyodide, xterm.js, and pyelftools.
