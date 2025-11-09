## Compiling MicroPython
```
cd port-riscv-emu.py

# Build with default (RV32IM)
make

# Build with all extensions (RV32IMAC)
make RVM=1 RVA=1 RVC=1
```

## Running MicroPython
```
./riscv-emu.py --raw-tty --ram-size=4096 prebuilt/micropython.elf 
```
