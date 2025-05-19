// This file is part of the CircuitPython project: https://circuitpython.org
//
// SPDX-FileCopyrightText: Copyright (c) 2021 Scott Shawcroft for Adafruit Industries
//
// SPDX-License-Identifier: MIT
#pragma once

#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include "supervisor/flash.h"

void write_block(uint32_t block, uint8_t *data);
void read_block(uint32_t block, uint8_t *data);

void supervisor_flash_init(void);
uint32_t supervisor_flash_get_block_size(void);
uint32_t supervisor_flash_get_block_count(void);
void port_internal_flash_flush(void);
mp_uint_t supervisor_flash_read_blocks(uint8_t *dest, uint32_t block, uint32_t num_blocks);
mp_uint_t supervisor_flash_write_blocks(const uint8_t *src, uint32_t block, uint32_t num_blocks);
void supervisor_flash_release_cache(void);

