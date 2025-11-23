#include "py/compile.h"
#include "py/runtime.h"
#include "py/stackctrl.h"
#include "py/gc.h"
#include "py/objlist.h"
#include "shared/runtime/pyexec.h"
#include "shared/runtime/gchelper.h"
#include "mpconfigport.h"

extern uint8_t _gc_heap_start, _gc_heap_end;

int main(int argc, char *argv[]) {
    mp_stack_ctrl_init();
    mp_stack_set_limit(4096);
    gc_init((void*) &_gc_heap_start, (void*) &_gc_heap_end);
    mp_init();

	mp_obj_list_init(MP_OBJ_TO_PTR(mp_sys_argv), 0);
    for (int i = 0; i < argc; i++) {
		mp_obj_list_append(mp_sys_argv, mp_obj_new_str(argv[i], strlen(argv[i])));
    }

#if (MICROPY_PORT_MODE == MODE_REPL_SYSCALL)
    // Welcome message for syscall REPL mode
    mp_printf(&mp_plat_print, "Welcome to MicroPython on RISC-V!\n");
#endif

#if (MICROPY_PORT_MODE == MODE_HEADLESS) || \
    (MICROPY_PORT_MODE == MODE_UART)
    // Execute frozen script (module name set by Makefile via -DFROZEN_MODULE_NAME)
    #ifndef FROZEN_MODULE_NAME
    #define FROZEN_MODULE_NAME "startup"  // default if not set
    #endif
    pyexec_frozen_module(FROZEN_MODULE_NAME, false);
#endif

#if (MICROPY_PORT_MODE == MODE_REPL_SYSCALL) || \
    (MICROPY_PORT_MODE == MODE_UART)
    // Start REPL
	pyexec_friendly_repl();
#endif

    gc_sweep_all();
    mp_deinit();
    return 0;
}
