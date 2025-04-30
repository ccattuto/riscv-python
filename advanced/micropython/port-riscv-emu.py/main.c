#include "py/compile.h"
#include "py/runtime.h"
#include "py/stackctrl.h"
#include "py/gc.h"
#include "py/objlist.h"
#include "shared/runtime/pyexec.h"
#include "shared/runtime/gchelper.h"

extern uint8_t _gc_heap_start, _gc_heap_end;

#if MICROPY_ENABLE_GC
void gc_collect(void) {
    gc_collect_start();
    gc_helper_collect_regs_and_stack();
    gc_collect_end();
}
#endif /* MICROPY_ENABLE_GC */

int main(int argc, char *argv[]) {
    mp_stack_ctrl_init();
    mp_stack_set_limit(4096);
    gc_init((void*) &_gc_heap_start, (void*) &_gc_heap_end);
    mp_init();

	mp_obj_list_init(MP_OBJ_TO_PTR(mp_sys_argv), 0);
    for (int i = 0; i < argc; i++) {
		mp_obj_list_append(mp_sys_argv, mp_obj_new_str(argv[i], strlen(argv[i])));
    }

    mp_printf(&mp_plat_print, "Welcome to MicroPython on RISC-V!\n");

	pyexec_friendly_repl();

    gc_sweep_all();
    mp_deinit();
    return 0;
}
