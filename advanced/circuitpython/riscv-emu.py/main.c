#include "py/runtime.h"
#include "py/compile.h"
#include "py/repl.h"
#include "py/gc.h"
#include "shared-bindings/board/__init__.h"
#include "supervisor/internal_flash.h"
#include "supervisor/shared/safe_mode.h"
#include "supervisor/shared/stack.h"
#include "supervisor/filesystem.h"
#include "shared/runtime/pyexec.h"
#include "mpconfigport.h"

#include "riscv-py.h"

typedef enum {
    SUPERVISOR_RUNNING,
    SUPERVISOR_SAFE_MODE,
    SUPERVISOR_REPL,
    SUPERVISOR_VM,
} supervisor_execution_status_t;

extern uint32_t _gc_heap_start, _gc_heap_end;
extern uint32_t _pystack_start, _pystack_end;
extern uint32_t _stack_top;

vstr_t *boot_output = NULL;

extern void board_init(void);
extern void reset_board(void);
supervisor_execution_status_t supervisor_execution_status(void);

int main(void) {
    pyexec_result_t result;

	stack_init();
    mp_stack_ctrl_init();
	mp_stack_set_top((void*) &_stack_top);
    mp_stack_set_limit(64 * 1024);
    gc_init((void*) &_gc_heap_start, (void*) &_gc_heap_end);
	mp_pystack_init((void*) &_pystack_start, (void*) &_pystack_end);
    mp_init();

    // Set up board peripherals and mount filesystem
    board_init();
	filesystem_init(true, false);

    pyexec_file_if_exists("code.py", &result);

    pyexec_friendly_repl();

    // Clean shutdown
    mp_deinit();
    reset_board();
    return 0;
}

NORETURN void nlr_jump_fail(void *) {
    for (;;) {}  // or reboot / safe mode
}

supervisor_execution_status_t supervisor_execution_status(void) {
    return SUPERVISOR_RUNNING;
}

