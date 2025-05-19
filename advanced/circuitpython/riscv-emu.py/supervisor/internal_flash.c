// This file is part of the CircuitPython project: https://circuitpython.org
//
// SPDX-FileCopyrightText: Copyright (c) 2021 Scott Shawcroft for Adafruit Industries
//
// SPDX-License-Identifier: MIT

#include "supervisor/internal_flash.h"

#include <stdint.h>
#include <stdbool.h>
#include <string.h>

#include "py/mpconfig.h"
#include "py/runtime.h"
#include "py/mperrno.h"

#include "supervisor/internal_flash.h"

#define MMIO_CMD     (*(volatile uint32_t *) 0x10010000)
#define MMIO_BLK     (*(volatile uint32_t *) 0x10010004)
#define MMIO_PTR     (*(volatile uint32_t *) 0x10010008)
#define MMIO_CTRL    (*(volatile uint32_t *) 0x1001000C)
#define MMIO_STATUS  (*(volatile uint32_t *) 0x10010010)

#define FS_BLOCK_SIZE 512
#define FS_SIZE (CIRCUITPY_INTERNAL_FLASH_FILESYSTEM_SIZE)

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

void supervisor_flash_init(void) {
}

uint32_t supervisor_flash_get_block_size(void) {
    return FS_BLOCK_SIZE;
}

uint32_t supervisor_flash_get_block_count(void) {
    return FS_SIZE / FS_BLOCK_SIZE;
}

void port_internal_flash_flush(void) {
}

mp_uint_t supervisor_flash_read_blocks(uint8_t *dest, uint32_t block, uint32_t num_blocks) {
    for (uint32_t i = 0; i < num_blocks; i++) {
        read_block(block + i, dest + i * FS_BLOCK_SIZE);
    }
    return 0;
}

mp_uint_t supervisor_flash_write_blocks(const uint8_t *src, uint32_t block, uint32_t num_blocks) {
    for (uint32_t i = 0; i < num_blocks; i++) {
        write_block(block + i, (uint8_t *)(src + i * FS_BLOCK_SIZE));
    }
    return 0;  // Success
}

void supervisor_flash_release_cache(void) {
}

