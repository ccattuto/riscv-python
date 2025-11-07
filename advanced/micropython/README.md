## Compiling MicroPython
```
cd port-riscv-emu.py

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

## Running MicroPython
```
./riscv-emu.py --raw-tty --ram-size=4096 prebuilt/micropython.elf 
```
