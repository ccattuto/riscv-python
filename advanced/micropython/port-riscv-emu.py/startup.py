# Example startup script for embedded MicroPython modes
# This script demonstrates various MicroPython capabilities

print("MicroPython embedded startup script")
print("=====================================")

# Basic computation
result = sum([i**2 for i in range(10)])
print(f"Sum of squares 0-9: {result}")

# Use built-in modules
import math
print(f"Pi: {math.pi:.6f}")
print(f"Sqrt(2): {math.sqrt(2):.6f}")

# Array operations
import array
arr = array.array('i', [1, 2, 3, 4, 5])
print(f"Array: {list(arr)}")

# Struct packing/unpacking
import struct
packed = struct.pack('HHL', 1, 2, 3)
unpacked = struct.unpack('HHL', packed)
print(f"Struct pack/unpack: {unpacked}")

# Regular expressions
import re
match = re.match(r'(\w+):(\d+)', 'hello:42')
if match:
    print(f"Regex match: {match.groups()}")

print("\nStartup script completed successfully!")
