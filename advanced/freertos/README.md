## Compiling the FreeRTOS examples
```
# Build with default (RV32I base ISA only)
make

# Build with all extensions (RV32IMAC)
make RVC=1 MUL=1 RVA=1

# Build with specific combinations
make RVC=1          # RV32IC (+ compressed)
make MUL=1          # RV32IM (+ multiply/divide)
make RVA=1          # RV32IA (+ atomics)
make RVC=1 MUL=1    # RV32IMC
```
In `Makefile`, set `MTIMER_MMIO = 1` to use the memory-mapped timer registers (standard, requires memory-mapped IO, uses the unmodified FreeRTOS RISC-V trap handler) or `MTIMER_MMIO = 1` to use the CSR-based timer registers (faster, it doesn't need memory-mapped IO, uses a custom trap handler).

## Running the examples

```
./riscv-emu.py --timer=csr prebuilt/freertos_app1.elf
```
The pre-built examples are compiled with `MTIMER_MMIO = 0`. To run examples compiled with `MTIMER_MMIO = 1`, use `--timer=mmio`.
