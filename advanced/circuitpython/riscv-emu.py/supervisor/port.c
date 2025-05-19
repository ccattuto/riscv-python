// This file is part of the CircuitPython project: https://circuitpython.org
//
// SPDX-FileCopyrightText: Copyright (c) 2021 Scott Shawcroft for Adafruit Industries
//
// SPDX-License-Identifier: MIT

#include <stdint.h>
#include <string.h>
#include <stdlib.h>
#include "supervisor/background_callback.h"
#include "supervisor/port.h"
#include "genhdr/mpversion.h"
#include "shared-bindings/microcontroller/__init__.h"
#include "supervisor/shared/safe_mode.h"
#include "supervisor/shared/tick.h"
#include "riscv-py.h"


extern int main(void);
extern void _start(void) __attribute__((noreturn));;
extern void trap_handler_riscvpy(void);

void reset_board(void);
void rearm_timer(void);
void port_tick(void);

__attribute__((weak)) void setup_timer_interrupt(void);
__attribute__((weak)) void disable_timer_interrupt(void);

#if CIRCUITPY_USE_MTIME_MMIO
#define MTIME_ADDR 			0x0200BFF8
#define MTIMECMP_ADDR 		0x02004000
#define MTIME_ADDR_LO		(*(volatile uint32_t *)(MTIME_ADDR + 0))
#define MTIME_ADDR_HI		(*(volatile uint32_t *)(MTIME_ADDR + 4))
#define MTIMECMP_ADDR_LO	(*(volatile uint32_t *)(MTIMECMP_ADDR + 0))
#define MTIMECMP_ADDR_HI	(*(volatile uint32_t *)(MTIMECMP_ADDR + 4))

static inline void write_mtime(uint64_t value) {
	MTIME_ADDR_LO = value & 0xFFFFFFFF;
	MTIME_ADDR_HI = value >> 32;
}

static inline void write_mtimecmp(uint64_t value) {
	MTIMECMP_ADDR_LO = value & 0xFFFFFFFF;
	MTIMECMP_ADDR_HI = value >> 32;
}

static inline uint64_t read_mtime(void) {
    uint32_t hi1, lo, hi2;
	do {
		hi1 = MTIME_ADDR_HI;
		lo = MTIME_ADDR_LO;
		hi2 = MTIME_ADDR_HI;
    } while (hi1 != hi2);

    return ((uint64_t) hi2 << 32) | lo;
}

static inline uint64_t read_mtimecmp(void) {
    return ((uint64_t) MTIMECMP_ADDR_HI << 32) | MTIMECMP_ADDR_LO;
}

static inline uint32_t read_mtime_lo(void) {
    return MTIME_ADDR_LO;
}

#else
static inline void write_mtime(uint64_t value) {
    uint32_t hi = value >> 32;
    uint32_t lo = value & 0xFFFFFFFF;

    __asm__ volatile ("csrw 0x7C0, %0" :: "r"(lo));
    __asm__ volatile ("csrw 0x7C1, %0" :: "r"(hi));
}

static inline void write_mtimecmp(uint64_t value) {
    uint32_t hi = value >> 32;
    uint32_t lo = value & 0xFFFFFFFF;

    __asm__ volatile ("csrw 0x7C2, %0" :: "r"(lo));
    __asm__ volatile ("csrw 0x7C3, %0" :: "r"(hi));
}

static inline uint64_t read_mtime(void) {
    uint32_t hi1, lo, hi2;
    do {
        __asm__ volatile ("csrr %0, 0x7C1" : "=r"(hi1));
        __asm__ volatile ("csrr %0, 0x7C0" : "=r"(lo));
        __asm__ volatile ("csrr %0, 0x7C1" : "=r"(hi2));
    } while (hi1 != hi2);

    return ((uint64_t) hi2 << 32) | lo;
}

static inline uint64_t read_mtimecmp(void) {
    uint32_t hi, lo;
    __asm__ volatile ("csrr %0, 0x7C3" : "=r"(hi));
    __asm__ volatile ("csrr %0, 0x7C2" : "=r"(lo));
    return ((uint64_t) hi << 32) | lo;
}

static inline uint32_t read_mtime_lo(void) {
    uint32_t lo;
    __asm__ volatile ("csrr %0, 0x7C0" : "=r"(lo));

    return lo;
}
#endif

#if CIRCUITPY_USE_MTIME_TICKS
// assumes the emulator runs at ~2 MIPS (i.e., mtime runs at 2 MHz)
uint64_t port_get_raw_ticks(uint8_t *subticks) {
	if (subticks) {
    	*subticks = 0;
	}
	return read_mtime() / 2000;
}

#else /* CIRCUITPY_USE_MTIME_TICKS */
volatile uint64_t ticks_ms = 0;

void port_tick(void) {
	ticks_ms++;
	supervisor_tick();
}

uint64_t port_get_raw_ticks(uint8_t *subticks) {
	if (subticks) {
    	*subticks = 0;
	}
	return ticks_ms;
}

void setup_timer_interrupt(void) {
	// Install trap handler and enable timer interrupt
    WRITE_CSR(mtvec, (uint32_t) trap_handler_riscvpy);
    SET_CSR(mie, 1 << 7);
    SET_CSR(mstatus, 1 << 3);
	write_mtime(0);
	write_mtimecmp(20000);  // assuming mtime runs at ~2 MHz, fire interrutp 10 ms in the future
}

void disable_timer_interrupt(void) {
	// Install trap handler and enable timer interrupt
    CLEAR_CSR(mstatus, 1 << 3);
    CLEAR_CSR(mie, 1 << 7);
    WRITE_CSR(mtvec, 0);
}

inline void rearm_timer(void) {
	uint64_t mtimecmp;
	mtimecmp = read_mtimecmp();
	write_mtimecmp(mtimecmp + 2000);  // assuming mtime runs at ~2 MHz, fire interrutp 1 ms in the future
}

#endif /* CIRCUITPY_USE_MTIME_TICKS */


safe_mode_t __attribute__((used)) port_init(void) {
    // Reset everything into a known state before board_init.
    reset_port();

    return SAFE_MODE_NONE;
}

void reset_port(void) {
    // Older ports will do blanket resets here. Instead, move to a model that
    // uses the deinit() functions to reset internal state.
}

void reset_board(void) {
	reset_cpu();
}

void reset_to_bootloader(void) {
	reset_cpu();
}

void reset_cpu(void) {
#if !CIRCUITPY_USE_MTIME_TICKS
	disable_timer_interrupt();
#endif
	_start();
}

extern uint32_t _stack_top,_stack_bottom;
extern uint32_t _gc_heap_start, _gc_heap_end;

uint32_t *port_stack_get_top(void) {
    return &_stack_top;
}

uint32_t *port_stack_get_limit(void) {
    return &_stack_bottom;
}

uint32_t *port_heap_get_bottom(void) {
    return &_gc_heap_start;
}

uint32_t *port_heap_get_top(void) {
    return &_gc_heap_end;
}

uint32_t saved_word;
void port_set_saved_word(uint32_t value) {
    // Store in RAM because the watchdog scratch registers don't survive
    // resetting by pulling the RUN pin low.
    saved_word = value;
}

uint32_t port_get_saved_word(void) {
    return saved_word;
}

static volatile bool ticks_enabled;
static volatile bool _woken_up;

void port_enable_tick(void) {
    ticks_enabled = true;
}

void port_disable_tick(void) {
    ticks_enabled = false;
}

void port_interrupt_after_ticks(uint32_t ticks) {
    _woken_up = false;
}

void port_idle_until_interrupt(void) {
    common_hal_mcu_disable_interrupts();
    if (!background_callback_pending() && !_woken_up) {
        // __WFI();
    }
    common_hal_mcu_enable_interrupts();
}

void port_yield() {
}

void port_boot_info(void) {
}

/*
void port_background_task(void) {
    // Existing background logic
    background_callback_run_all();

    // Poll UART to catch CTRL+C during tight loops
    if (common_hal_busio_uart_rx_characters_available()) {
        int c = mp_hal_stdin_rx_chr();
        if (c == mp_interrupt_char) {
            mp_sched_keyboard_interrupt();
        }
    }

    mp_handle_pending(true);
}
*/

