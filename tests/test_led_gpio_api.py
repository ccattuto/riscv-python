#!/usr/bin/env python3
"""
Test the LED_GPIO peripheral directly via Python API
This demonstrates the LED GPIO functionality without needing compiled C code
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from cpu import CPU
from ram import RAM_MMIO
from machine import Machine
from peripherals import LED_GPIO, TerminalStatusLine

# LED color constants
LED_OFF   = 0b00
LED_RED   = 0b01
LED_GREEN = 0b10
LED_BLUE  = 0b11

def set_led(ram, led_num, color):
    """Helper function to set a specific LED color"""
    current = ram.load_word(0x10020000)
    mask = ~(0b11 << (led_num * 2))
    new_value = (current & mask) | (color << (led_num * 2))
    ram.store_word(0x10020000, new_value)

def main():
    print("LED_GPIO Peripheral API Test")
    print("=" * 50)

    # Create status line
    status_line = TerminalStatusLine()

    # Set up emulator components
    ram = RAM_MMIO(1024 * 1024)
    cpu = CPU(ram)

    # Create and register LED GPIO peripheral
    led_gpio = LED_GPIO(status_line=status_line)
    ram.register_peripheral(led_gpio)

    print("\nTest 1: All LEDs OFF")
    ram.store_word(0x10020000, 0x0000)
    input("Press Enter to continue...")

    print("\nTest 2: All LEDs RED")
    ram.store_word(0x10020000, 0x5555)  # 01 01 01 01 01 01 01 01
    input("Press Enter to continue...")

    print("\nTest 3: All LEDs GREEN")
    ram.store_word(0x10020000, 0xAAAA)  # 10 10 10 10 10 10 10 10
    input("Press Enter to continue...")

    print("\nTest 4: All LEDs BLUE")
    ram.store_word(0x10020000, 0xFFFF)  # 11 11 11 11 11 11 11 11
    input("Press Enter to continue...")

    print("\nTest 5: Rainbow pattern")
    ram.store_word(0x10020000, 0xE4E4)  # Blue Green Red Off pattern
    input("Press Enter to continue...")

    print("\nTest 6: Walking RED LED")
    for i in range(8):
        ram.store_word(0x10020000, 0x0000)
        set_led(ram, i, LED_RED)
        import time
        time.sleep(0.2)

    print("\nTest 7: Individual LED control")
    print("Setting LEDs: 7=BLUE, 6=GREEN, 5=RED, 4=OFF, 3=BLUE, 2=GREEN, 1=RED, 0=OFF")
    ram.store_word(0x10020000, 0x0000)
    set_led(ram, 7, LED_BLUE)
    set_led(ram, 6, LED_GREEN)
    set_led(ram, 5, LED_RED)
    set_led(ram, 4, LED_OFF)
    set_led(ram, 3, LED_BLUE)
    set_led(ram, 2, LED_GREEN)
    set_led(ram, 1, LED_RED)
    set_led(ram, 0, LED_OFF)
    input("Press Enter to continue...")

    print("\nTest 8: Read-back test")
    test_value = 0xABCD
    ram.store_word(0x10020000, test_value)
    read_back = ram.load_word(0x10020000)
    print(f"Wrote: 0x{test_value:04X}, Read: 0x{read_back:04X}")
    assert read_back == test_value, "Read-back mismatch!"
    print("Read-back test PASSED")
    input("Press Enter to continue...")

    print("\nTest 9: Alternating pattern")
    import time
    for i in range(5):
        ram.store_word(0x10020000, 0x5555)  # All RED
        time.sleep(0.3)
        ram.store_word(0x10020000, 0xAAAA)  # All GREEN
        time.sleep(0.3)

    print("\nTest complete! Turning all LEDs OFF")
    ram.store_word(0x10020000, 0x0000)

    print("\nAll tests passed!")

if __name__ == "__main__":
    main()
