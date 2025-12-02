## Compiling and running CoreMark

In `riscv-emu.py/core_portme.mak`, set `CC` to your RISC-V compiler.

```
cd coremark

# Build with default (RV32IM)
make PORT_DIR=../riscv-emu.py

# Build with all extensions (RV32IMAC)
make PORT_DIR=../riscv-emu.py RVM=1 RVA=1 RVC=1
```

Inspect the results in `run1.log` and `run2.log`:
```
2K performance run parameters for coremark.
CoreMark Size    : 666
Total ticks      : 12326926
Total time (secs): 12
Iterations/Sec   : 3
Iterations       : 40
Compiler version : GCC12.2.0
Compiler flags   : -march=rv32im_zicsr -mabi=ilp32 -O2 -D_REENT_SMALL -DPERFORMANCE_RUN=1
Memory location  : heap
seedcrc          : 0xe9f5
[0]crclist       : 0xe714
[0]crcmatrix     : 0x1fd7
[0]crcstate      : 0x8e3a
[0]crcfinal      : 0x65c5
Correct operation validated. See README.md for run and reporting rules.
```
