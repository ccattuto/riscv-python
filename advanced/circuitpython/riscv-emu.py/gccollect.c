#include "py/gc.h"

extern uint32_t _stack_top;

void *gc_helper_get_regs_and_sp(void *);

size_t gc_get_max_new_split(void) {
    return 0;  // disable split
}

void gc_collect(void) {
	uint32_t regs[12];
	void *sp;

    gc_collect_start();

    sp = gc_helper_get_regs_and_sp(regs);
	
	// Scan the saved registers
	gc_collect_root((void **)regs, sizeof(regs) / sizeof(uint32_t));

	// Scan the current stack
	gc_collect_root(sp, ((uintptr_t)&_stack_top - (uintptr_t)sp) / sizeof(uintptr_t));

    gc_collect_end();
}

