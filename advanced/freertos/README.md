## Compiling the FreeRTOS examples
```
make
```
In `Makefile`, set `MTIMER_MMIO = 1` to use the memory-mapped timer registers (standard, requires memory-mapped IO, uses the unmodified FreeRTOS RISC-V trap handler) or `MTIMER_MMIO = 1` to use the CSR-based timer registers (faster, it doesn't need memory-mapped IO, uses a custom trap handler).

## Running the examples

```
./riscv-emu.py --timer=csr prebuilt/freertos_app1.elf
```
The pre-built examples are compiled with `MTIMER_MMIO = 0`. To run examples compiled with `MTIMER_MMIO = 1`, use `--timer=mmio`.
