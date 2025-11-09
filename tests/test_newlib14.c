// Test program for M Extension (Multiply/Divide) instructions
// Needs to be compiled with RVM=1

#include <stdio.h>
#include <stdint.h>

// Test helper
void test_mul(int32_t a, int32_t b) {
    int32_t result = a * b;
    printf("MUL: %d * %d = %d\n", a, b, result);
}

void test_mulh(int32_t a, int32_t b) {
    int64_t product = (int64_t)a * (int64_t)b;
    int32_t result = (int32_t)(product >> 32);
    printf("MULH: %d * %d = %d (high)\n", a, b, result);
}

void test_mulhu(uint32_t a, uint32_t b) {
    uint64_t product = (uint64_t)a * (uint64_t)b;
    uint32_t result = (uint32_t)(product >> 32);
    printf("MULHU: %u * %u = %u (high)\n", a, b, result);
}

void test_mulhsu(int32_t a, uint32_t b) {
    int64_t product = (int64_t)a * (uint64_t)b;
    int32_t result = (int32_t)(product >> 32);
    printf("MULHSU: %d * %u = %d (high)\n", a, b, result);
}

void test_div(int32_t a, int32_t b) {
    int32_t result = (b == 0) ? -1 :
                     (a == INT32_MIN && b == -1) ? INT32_MIN :
                     a / b;
    printf("DIV: %d / %d = %d\n", a, b, result);
}

void test_divu(uint32_t a, uint32_t b) {
    uint32_t result = (b == 0) ? 0xFFFFFFFF : a / b;
    printf("DIVU: %u / %u = %u\n", a, b, result);
}

void test_rem(int32_t a, int32_t b) {
    int32_t result = (b == 0) ? a :
                     (a == INT32_MIN && b == -1) ? 0 :
                     a % b;
    printf("REM: %d %% %d = %d\n", a, b, result);
}

void test_remu(uint32_t a, uint32_t b) {
    uint32_t result = (b == 0) ? a : a % b;
    printf("REMU: %u %% %u = %u\n", a, b, result);
}

int main(void) {
    printf("=== M Extension Test ===\n");

    // Test MUL - basic multiplication
    printf("--- MUL Tests ---\n");
    test_mul(7, 13);            // 91
    test_mul(-7, 13);           // -91
    test_mul(-7, -13);          // 91
    test_mul(0x1000, 0x1000);   // 0x1000000

    // Test MULH - signed x signed, high bits
    printf("--- MULH Tests ---\n");
    test_mulh(0x7FFFFFFF, 2);   // MAX_INT * 2
    test_mulh(-1, -1);          // (-1) * (-1) = 1, high = 0
    test_mulh(0x80000000, 2);   // MIN_INT * 2

    // Test MULHU - unsigned x unsigned, high bits
    printf("--- MULHU Tests ---\n");
    test_mulhu(0xFFFFFFFF, 0xFFFFFFFF);     // max * max
    test_mulhu(0x80000000, 2);              // 2^31 * 2

    // Test MULHSU - signed x unsigned, high bits
    printf("--- MULHSU Tests ---\n");
    test_mulhsu(-1, 0xFFFFFFFF);    // -1 * max_uint
    test_mulhsu(2, 0x80000000);     // 2 * 2^31

    // Test DIV - signed division
    printf("--- DIV Tests ---\n");
    test_div(20, 6);            // 3
    test_div(-20, 6);           // -3
    test_div(20, -6);           // -3
    test_div(-20, -6);          // 3
    test_div(100, 0);           // div by zero → -1
    test_div(0x80000000, -1);   // overflow → MIN_INT

    // Test DIVU - unsigned division
    printf("--- DIVU Tests ---\n");
    test_divu(20, 6);           // 3
    test_divu(0xFFFFFFFF, 2);   // max / 2
    test_divu(100, 0);          // div by zero → 0xFFFFFFFF

    // Test REM - signed remainder
    printf("--- REM Tests ---\n");
    test_rem(20, 6);            // 2
    test_rem(-20, 6);           // -2
    test_rem(20, -6);           // 2
    test_rem(-20, -6);          // -2
    test_rem(100, 0);           // div by zero → 100
    test_rem(0x80000000, -1);   // overflow → 0

    // Test REMU - unsigned remainder
    printf("--- REMU Tests ---\n");
    test_remu(20, 6);           // 2
    test_remu(0xFFFFFFFF, 10);  // 5
    test_remu(100, 0);          // div by zero → 100

    printf("=== All M Extension Tests Complete ===\n");

    return 0;
}
