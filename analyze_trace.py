#!/usr/bin/env python3
"""
Analyze emulator trace output for test_newlib11.c BSS initialization loop.

Usage: python3 analyze_trace.py < trace_output.txt
"""

import sys
import re

def analyze_bss_loop(trace_lines):
    """Analyze the BSS initialization loop (PC 0x98-0x9E)."""

    loop_iterations = []
    prev_a0 = None
    in_loop = False
    exited_loop = False
    next_pc = None

    for line in trace_lines:
        # Parse: pc=0x00000098, gp=0x00001A48, sp=0x00100000, ra=0x00000000, a0=0x00001250, a1=0x00001710
        match = re.search(r'pc=0x([0-9A-Fa-f]+).*?a0=0x([0-9A-Fa-f]+).*?a1=0x([0-9A-Fa-f]+)', line)
        if not match:
            continue

        pc = int(match.group(1), 16)
        a0 = int(match.group(2), 16)
        a1 = int(match.group(3), 16)

        # Track when we enter the loop
        if pc == 0x98:
            if not in_loop:
                in_loop = True
                print(f"Entered BSS loop at PC=0x98")
                print(f"  Start: a0=0x{a0:08X}, a1=0x{a1:08X}")
                print(f"  Range: {a1-a0} bytes, {(a1-a0)//4} iterations expected\n")

            # Record this iteration
            loop_iterations.append(a0)

            if prev_a0 is not None:
                increment = a0 - prev_a0
                if increment != 4:
                    print(f"WARNING: a0 increment is {increment}, expected 4 at iteration {len(loop_iterations)}")

            prev_a0 = a0

        # Check if we exit the loop
        elif in_loop and pc not in [0x98, 0x9C, 0x9E]:
            exited_loop = True
            next_pc = pc
            break

    # Report results
    print("=" * 70)
    print("RESULTS:")
    print("=" * 70)

    if not loop_iterations:
        print("ERROR: Loop never started (PC never reached 0x98)")
        return False

    print(f"Total iterations observed: {len(loop_iterations)}")
    print(f"First a0 value: 0x{loop_iterations[0]:08X}")
    print(f"Last a0 value:  0x{loop_iterations[-1]:08X}")

    expected_final = 0x1710
    expected_iterations = (expected_final - loop_iterations[0]) // 4

    print(f"\nExpected final a0: 0x{expected_final:08X}")
    print(f"Expected iterations: {expected_iterations}")

    if exited_loop:
        print(f"\n✓ Loop exited correctly to PC=0x{next_pc:08X}")
        if loop_iterations[-1] >= expected_final:
            print("✓ Final a0 value is >= target (loop condition false)")
            return True
        else:
            print(f"✗ WARNING: Loop exited early! Last a0=0x{loop_iterations[-1]:08X} < 0x{expected_final:08X}")
            return False
    else:
        print(f"\n✗ Loop did NOT exit (still looping or trace ended)")
        print(f"   Last a0=0x{loop_iterations[-1]:08X}, target=0x{expected_final:08X}")
        print(f"   Progress: {len(loop_iterations)}/{expected_iterations} iterations ({100*len(loop_iterations)/expected_iterations:.1f}%)")
        return False

def main():
    print("Reading trace from stdin...")
    lines = sys.stdin.readlines()
    print(f"Read {len(lines)} lines\n")

    success = analyze_bss_loop(lines)

    print("\n" + "=" * 70)
    if success:
        print("VERDICT: BSS loop completed successfully ✓")
    else:
        print("VERDICT: BSS loop has issues ✗")
    print("=" * 70)

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
