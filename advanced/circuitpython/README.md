## Compiling CircuitPython
```
cd port-riscv-emu.py
make
```

## Running CircuitPython
```
./riscv-emu.py --timer=mmio --ram-size=4096 --uart --blkdev=advanced/circuitpython/riscv-emu.py/build-riscv-emu.py/circuitpy.img advanced/circuitpython/riscv-emu.py/build-riscv-emu.py/firmware.elf
```

