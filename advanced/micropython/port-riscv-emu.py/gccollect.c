#include "py/gc.h"

#ifdef MICROPY_ENABLE_GC
extern uint32_t _stack_top;
extern void *gc_helper_get_regs_and_sp(void *);

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
#endif /* MICROPY_ENABLE_GC */

