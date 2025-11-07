## Compiling and running CoreMark

In `riscv-emu.py/core_portme.mak`, set `CC` to your RISC-V compiler.

```
cd coremark

# Build with default extensions (RV32IA)
make PORT_DIR=../riscv-emu.py

# Build with all extensions (RV32IMAC)
make PORT_DIR=../riscv-emu.py RVC=1 MUL=1

# Build with specific combinations
make PORT_DIR=../riscv-emu.py RVC=1          # RV32IAC (+ compressed)
make PORT_DIR=../riscv-emu.py MUL=1          # RV32IMA (+ multiply/divide)
make PORT_DIR=../riscv-emu.py RVA=0          # RV32I (no atomics)
```

Inspect the results in `run1.log` and `run2.log`:
```
2K performance run parameters for coremark.
CoreMark Size    : 666
Total ticks      : 14828555
Total time (secs): 14
Iterations/Sec   : 1
Iterations       : 20
Compiler version : GCC12.2.0
Compiler flags   : -march=rv32i_zicsr -mabi=ilp32 -O2 -D_REENT_SMALL -DPERFORMANCE_RUN=1  
Memory location  : heap
seedcrc          : 0xe9f5
[0]crclist       : 0xe714
[0]crcmatrix     : 0x1fd7
[0]crcstate      : 0x8e3a
[0]crcfinal      : 0x4983
Correct operation validated. See README.md for run and reporting rules.
```
