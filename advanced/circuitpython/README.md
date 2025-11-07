## Compiling CircuitPython

Check out the following submodule, only:
```
cd circuitpython
git submodule update --init lib/tlsf
cd ..
```

Compile CircuitPython (requires GCC 14):
```
cd riscv-emu.py

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

## Running CircuitPython

Run the emulator:
```
cd ../../..
./riscv-emu.py --timer=mmio --ram-size=4096 --uart --blkdev=advanced/circuitpython/riscv-emu.py/build-riscv-emu.py/circuitpy.img advanced/circuitpython/riscv-emu.py/build-riscv-emu.py/firmware.elf
000.001s [INFO] [UART] PTY created: /dev/ttys007
000.002s [INFO] [BLOCK] Opening block device image: advanced/circuitpython/riscv-emu.py/build-riscv-emu.py/circuitpy.img
```

If you want to use the pre-built binaries, run the emulator like this:
```
./riscv-emu.py --timer=mmio --ram-size=4096 --uart --blkdev=prebuilt/circuitpy_fatfs.img prebuilt/circuitpython.elf 
```

Connect to CircuitPython using your favorite terminal program:
```
screen /dev/ttys007 115200
```

This CircuitPython port supports an emulated serial backed by a pseudoterminal, an emulated block device backed by a filesystem image, interrupt-driven timer and tick support, CTRL+C support for tight Python loops, and more:
```
Adafruit CircuitPython 9.2.7 on 2025-05-20; riscv-emu.py with riscv-emu.py
>>> import sys
>>> sys.platform
'riscv-emu.py'
>>> import os
>>> os.listdir("/")
['code.py']
>>> import time
>>> time.monotonic()
23.779
>>> time.monotonic()
24.765
>>> time.sleep(1)
>>> while True:
...     pass
...     
...     
... 
Traceback (most recent call last):
  File "<stdin>", line 2, in <module>
KeyboardInterrupt: 
>>> help("modules")
__future__        busio             micropython       struct
__main__          collections       os                supervisor
array             gc                rainbowio         sys
board             math              random            time
builtins          microcontroller   storage
Plus any modules on the filesystem
>>> 
```
