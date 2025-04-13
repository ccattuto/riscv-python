#!/bin/bash

TEST_DIR="./riscv-samples/unit-tests/rv32ui"
EMU="./riscv-emu.py"
PASS=0
FAIL=0

for BIN in "$TEST_DIR"/*.bin; do
    A0_DEC=$( "$EMU" "$BIN" 2>/dev/null | grep '(x10)' | awk -F'[()]' '{ print $4 }' )

    if [[ "$A0_DEC" == "257" ]]; then
        echo "[PASS] $(basename "$BIN")"
        ((PASS++))
    else
        echo "[FAIL] $(basename "$BIN") (a0=$A0_DEC)"
        ((FAIL++))
    fi
done

echo
echo "Summary: $PASS passed, $FAIL failed"
