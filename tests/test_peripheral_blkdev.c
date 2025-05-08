#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#define MMIO_CMD     (*(volatile uint32_t *) 0x10010000)
#define MMIO_BLK     (*(volatile uint32_t *) 0x10010004)
#define MMIO_PTR     (*(volatile uint32_t *) 0x10010008)
#define MMIO_CTRL    (*(volatile uint32_t *) 0x1001000C)
#define MMIO_STATUS  (*(volatile uint32_t *) 0x10010010)

#define BLOCK_SIZE 512
#define MAX_BLOCKS 64

void write_block(uint32_t block, uint8_t *data) {
    MMIO_BLK = block;
    MMIO_PTR = (uintptr_t) data;
    MMIO_CMD = 1;  // WRITE
    MMIO_CTRL = 1;
    while (MMIO_STATUS == 0);
}

void read_block(uint32_t block, uint8_t *data) {
    MMIO_BLK = block;
    MMIO_PTR = (uintptr_t) data;
    MMIO_CMD = 0;  // READ
    MMIO_CTRL = 1;
    while (MMIO_STATUS == 0);
}

int main(void) {
    srand(42);  // Fixed seed for repeatability
    printf("Two-phase block device integrity test...\n");

    uint8_t *wr_buf = malloc(MAX_BLOCKS * BLOCK_SIZE);
    uint8_t *rd_buf = malloc(BLOCK_SIZE);

    if (!wr_buf || !rd_buf) {
        fprintf(stderr, "Memory allocation failed\n");
        return 1;
    }

    // --- Phase 1: Write all blocks ---
    for (uint32_t blk = 0; blk < MAX_BLOCKS; blk++) {
        uint8_t *block = wr_buf + blk * BLOCK_SIZE;
        for (int i = 0; i < BLOCK_SIZE; i++) {
            block[i] = rand() & 0xFF;
        }
        write_block(blk, block);
        printf("Written block %u\n", blk);
    }

    // --- Optional: clear RAM buffer to simulate real separation ---
    memset(rd_buf, 0, BLOCK_SIZE);

    // --- Phase 2: Read and verify all blocks ---
    srand(42);  // Reset PRNG to match original data
    for (uint32_t blk = 0; blk < MAX_BLOCKS; blk++) {
        uint8_t *expected = wr_buf + blk * BLOCK_SIZE;

        // Rebuild expected data
        for (int i = 0; i < BLOCK_SIZE; i++) {
            expected[i] = rand() & 0xFF;
        }

        read_block(blk, rd_buf);

        if (memcmp(rd_buf, expected, BLOCK_SIZE) != 0) {
            printf("X Block %u mismatch\n", blk);
            free(wr_buf);
            free(rd_buf);
            return 1;
        } else {
            printf("* Block %u verified\n", blk);
        }
    }

    printf("All %u blocks passed\n", MAX_BLOCKS);
    free(wr_buf);
    free(rd_buf);
    return 0;
}
