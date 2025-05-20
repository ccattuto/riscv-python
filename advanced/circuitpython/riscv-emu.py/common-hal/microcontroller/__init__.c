// This file is part of the CircuitPython project: https://circuitpython.org
//
// SPDX-FileCopyrightText: Copyright (c) 2021 Scott Shawcroft for Adafruit Industries
//
// SPDX-License-Identifier: MIT

#include "py/mphal.h"
#include "py/obj.h"

#include "common-hal/microcontroller/__init__.h"
#include "shared-bindings/microcontroller/__init__.h"
#include "shared-bindings/microcontroller/Pin.h"
#include "shared-bindings/microcontroller/Processor.h"
#include "supervisor/filesystem.h"
#include "supervisor/port.h"
#include "supervisor/shared/safe_mode.h"

// CSR helpers

#define READ_CSR(reg) ({ unsigned int __tmp; \
    asm volatile ("csrr %0, " #reg : "=r"(__tmp)); \
    __tmp; })

#define WRITE_CSR(reg, val) ({ \
    asm volatile ("csrw " #reg ", %0" :: "rK"(val)); })

#define SET_CSR(reg, bitmask) ({ unsigned int __tmp; \
    asm volatile ("csrrs %0, " #reg ", %1" : "=r"(__tmp) : "rK"(bitmask)); \
    __tmp; })

#define CLEAR_CSR(reg, bitmask) ({ unsigned int __tmp; \
    asm volatile ("csrrc %0, " #reg ", %1" : "=r"(__tmp) : "rK"(bitmask)); \
    __tmp; })


void common_hal_mcu_delay_us(uint32_t delay) {
    mp_hal_delay_us(delay);
}

volatile uint32_t nesting_count = 0;
void common_hal_mcu_disable_interrupts(void) {
    CLEAR_CSR(mie, 1 << 7);
    nesting_count++;
}

void common_hal_mcu_enable_interrupts(void) {
    if (nesting_count == 0) {
        // reset_into_safe_mode(SAFE_MODE_INTERRUPT_ERROR);
    }
    nesting_count--;
    if (nesting_count > 0) {
        return;
    }
    SET_CSR(mie, 1 << 7);
}

static bool next_reset_to_bootloader = false;

void common_hal_mcu_on_next_reset(mcu_runmode_t runmode) {
    switch (runmode) {
        case RUNMODE_UF2:
        case RUNMODE_BOOTLOADER:
            next_reset_to_bootloader = true;
            break;
        case RUNMODE_SAFE_MODE:
            safe_mode_on_next_reset(SAFE_MODE_PROGRAMMATIC);
            break;
        default:
            break;
    }
}

void common_hal_mcu_reset(void) {
    filesystem_flush();
    if (next_reset_to_bootloader) {
        reset_to_bootloader();
    } else {
        reset_cpu();
    }
}

const mcu_processor_obj_t common_hal_mcu_processor_obj = {
    .base = {
        .type = &mcu_processor_type,
    },
};

