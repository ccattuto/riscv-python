"""
Minimal Peripherals for Browser - Timer only
Based on the parent directory's peripherals.py
"""

from ram import MemoryAccessError

# Base class for peripherals with memory-mapped IO
class MMIOPeripheral:
    REG_BASE = None
    REG_END = None

    def read32(self, addr):
        return 0

    def write32(self, addr, value):
        pass

    # a run() method, if defined, will be registered and called periodically by the emulator
    # def run(self):
    #     pass

# Machine Timer (mtime/mtimecmp)
class MMIOTimer(MMIOPeripheral):
    REG_BASE  = 0x0200_4000
    REG_MTIMECMP_LO = REG_BASE + 0x00
    REG_MTIMECMP_HI = REG_MTIMECMP_LO + 0x04
    REG_MTIME_LO = 0x0200_BFF8
    REG_MTIME_HI = REG_MTIME_LO + 0x04
    REG_END = REG_MTIME_HI + 0x04

    def __init__(self, cpu):
        super().__init__()
        self.cpu = cpu

        self.mtime_lo = 0
        self.mtime_hi = 0
        self.mtime_lo_updated = False
        self.mtime_hi_updated = False

    def read32(self, addr):
        if addr == self.REG_MTIME_LO:
            return self.cpu.mtime & 0xFFFFFFFF
        elif addr == self.REG_MTIME_HI:
            return self.cpu.mtime >> 32
        elif addr == self.REG_MTIMECMP_LO:
            return self.cpu.mtimecmp & 0xFFFFFFFF
        elif addr == self.REG_MTIMECMP_HI:
            return self.cpu.mtimecmp >> 32
        else:
            raise MemoryAccessError(f"Invalid MMIO register read at 0x{addr:08X}")

    def write32(self, addr, value):
        if addr == self.REG_MTIMECMP_LO:
            self.cpu.mtimecmp = (self.cpu.mtimecmp & 0xFFFFFFFF_00000000) | (value & 0xFFFFFFFF)
        elif addr == self.REG_MTIMECMP_HI:
            self.cpu.mtimecmp = (self.cpu.mtimecmp & 0x00000000_FFFFFFFF) | ((value & 0xFFFFFFFF) << 32)
        elif addr == self.REG_MTIME_LO:
            self.mtime_lo = value
            self.mtime_lo_updated = True
        elif addr == self.REG_MTIME_HI:
            self.mtime_hi = value
            self.mtime_hi_updated = True
        else:
            raise MemoryAccessError(f"Invalid MMIO register write at 0x{addr:08X}")

        # Atomic update of mtime after writing both high and low words
        if self.mtime_lo_updated and self.mtime_hi_updated:
            self.cpu.mtime = (self.mtime_hi << 32) | self.mtime_lo
            self.mtime_lo_updated = False
            self.mtime_hi_updated = False
