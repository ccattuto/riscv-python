## Example user programs and tests

- `test_asm1.S`: Minimal assembly example with exit code.
  
- `test_bare1.c`:  Minimal "bare" C example (no Newlib).
  
- `test_newlib_stdio.c`: Minimal C example using Newlib (`printf()` and `getchar()`)

- `test_newlib_primes.c`: Computes and prints the first 1000 prime numbers.

- `test_newlib_malloc.c`: Tests dynamic memory allocation with Newlib's `malloc()` and `free()`.

- `test_newlib_mandelbrot.c`: Computes Mandelbrot's fractal and displays it using ASCII characters.

- `test_newlib_maze.c`: Generates a random maze using the recursive backtracking algorithm and prints it to terminal.

- `test_newlib_conway.c`: Conway's Game of Life. The state of the board is shown on terminal using ANSI escape codes. It accepts an optional command-line parameter for the seed of the random number generator used to initialize the board (e.g., `./riscv-emu.py tests/test_newlib_conway.elf -- 4242`).

- `test_newlib_args.c`: Demonstrates accessing command-line arguments via `argc` and `argv`.

- `test_newlib_fileio.c`: Stress tests Newlib's file I/O (`fread()`, `fseek()`, etc.)

- `test_newlib_traps.c`: Tests correct trap behavior for EBREAK, ECALL and illegal instructions.

- `test_newlib_timer.c`: Tests machine timer interrupt (`mtime` / `mtimecmp`), firing timer and handling timer traps while an idle loop is running. Run it with the `--timer=csr` option and check that the number of times the interrupt has fired is nonzero. Run it with `--traps`` to monitor timer-based trap generation.

- `test_newlib_scheduler.c`: Simple implementation of timer-based preemptive scheduling for two tasks. The first task increments a counter and prints it to console (using the debug macros in `risc-py.h`) every `0x10000` loops. The second task decrements a counter and prints it to console every `0x10000` loops. Run this example with the `--timer=csr` option. Use `--traps`` to see timer-based traps triggering task switching.

- `test_newlib_softfloat.c`: Soft floating point test.

- `test_newlib_setjmp.c`: Test using `setjump`/`longjump` C exception handling.

- `test_newlib_mext.c`: Test the RISC-V M extension (compile with RVM=1).

- `test_peripheral_uart.c`: Tests the memory-mapped UART implementation backed by a pseudo-terminal on the host. Run this example with the `--uart` option, and then connect to the indicated PTY using your preferred terminal program, e.g., `screen /dev/ttys015 115200`.

- `test_peripheral_blkdev.c`: Tests the memory-mapped block device implementation backed by a file on the host. Run this example with the `--blkdev=image` option, where `image` is the filename you want to use. If the file does not exist, it will be created by the emulator.

- `test_api_simple.py`: Python API example: loads and executes a simple program.

- `test_api_trap.py`: Python API example: loads a flat binary executable into RAM, runs it, intercepts a trap.
