#include "py/compile.h"
#include "py/runtime.h"
#include "py/stackctrl.h"
#include "py/gc.h"
#include "py/objlist.h"
#include "shared/runtime/pyexec.h"
#include <reent.h>

extern struct _reent *_impure_ptr;
extern uint8_t _gc_heap_start, _gc_heap_end;

int main(int argc, char *argv[]) {
	__sinit(_impure_ptr);

    mp_stack_ctrl_init();
    mp_stack_set_limit(4096);
    gc_init((void*) &_gc_heap_start, (void*) &_gc_heap_end);
    mp_init();

	mp_obj_list_init(MP_OBJ_TO_PTR(mp_sys_argv), 0);
    for (int i = 0; i < argc; ++i) {
		mp_obj_list_append(mp_sys_argv, mp_obj_new_str(argv[i], strlen(argv[i])));
    }

    mp_printf(&mp_plat_print, "Welcome to MicroPython on RISC-V!\n");

	pyexec_friendly_repl();

    mp_deinit();
    return 0;
}

