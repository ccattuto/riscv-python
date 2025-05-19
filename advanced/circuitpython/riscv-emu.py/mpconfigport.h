// This file is part of the CircuitPython project: https://circuitpython.org
//
// SPDX-FileCopyrightText: Copyright (c) 2021 Scott Shawcroft for Adafruit Industries
//
// SPDX-License-Identifier: MIT

#pragma once

#define MICROPY_PY_SYS_PLATFORM             	"riscv-emu.py"

#define CIRCUITPY_REPL_SERIAL 					(1)
#define CIRCUITPY_REPL_USB    					(0)

#define MICROPY_KBD_EXCEPTION					(1)

#define CIRCUITPY_USE_MTIME_TICKS 				(0)
#define CIRCUITPY_USE_MTIME_MMIO				(1)

#define CIRCUITPY_DEFAULT_STACK_SIZE 			(2048)

#define CIRCUITPY_INTERNAL_FLASH_FILESYSTEM 	(1)
#define CIRCUITPY_INTERNAL_FLASH_FILESYSTEM_SIZE (1024 * 512)
#define CIRCUITPY_INTERNAL_FLASH_FS_LITTLEFS	(0)
#define CIRCUITPY_FSUSERMOUNT 0

#define MICROPY_PY_FUNCTION_ATTRS           	(1)
#define MICROPY_PY_REVERSE_SPECIAL_METHODS  	(1)
#define MICROPY_USE_INTERNAL_PRINTF         	(1)

// This also includes mpconfigboard.h.
#include "py/circuitpy_mpconfig.h"

