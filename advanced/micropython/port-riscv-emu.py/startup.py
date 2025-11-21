# Example startup script for embedded MicroPython modes
# Note: Float support disabled in non-Newlib modes

print("MicroPython embedded startup script")
print("=====================================")

# Basic computation (integer only)
result = sum([i**2 for i in range(10)])
print("Sum of squares 0-9:", result)

# Array operations
import array
arr = array.array('i', [1, 2, 3, 4, 5])
print("Array:", list(arr))

# Struct packing/unpacking
import struct
packed = struct.pack('HHL', 1, 2, 3)
unpacked = struct.unpack('HHL', packed)
print("Struct pack/unpack:", unpacked)

# Regular expressions
import re
match = re.match(r'(\w+):(\d+)', 'hello:42')
if match:
    print("Regex match:", match.groups())

# String operations
text = "Hello from RISC-V!"
print("Upper:", text.upper())
print("Reversed:", text[::-1])

# List comprehensions
squares = [x*x for x in range(10)]
print("Squares:", squares)

print("\nStartup script completed successfully!")
