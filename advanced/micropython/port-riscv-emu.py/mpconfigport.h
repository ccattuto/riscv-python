#include <stdint.h>

// options to control how MicroPython is built

// Use the minimal starting configuration (disables all optional features).
#define MICROPY_CONFIG_ROM_LEVEL (MICROPY_CONFIG_ROM_LEVEL_MINIMUM)

// You can disable the built-in MicroPython compiler by setting the following
// config option to 0.  If you do this then you won't get a REPL prompt, but you
// will still be able to execute pre-compiled scripts, compiled with mpy-cross.
#define MICROPY_ENABLE_COMPILER     (1)
#define MICROPY_ENAVLE_REPL	        (1)
#define MICROPY_PY_BUILTINS_INPUT   (1)
#define MICROPY_PY_SYS_STDFILES     (1)

#define MICROPY_ENABLE_GC                 (1)
#define MICROPY_HELPER_REPL               (1)
#define MICROPY_ENABLE_REPL_HELPERS       (1)
#define MICROPY_MODULE_FROZEN_MPY         (0)
#define MICROPY_ENABLE_EXTERNAL_IMPORT    (0)
#define MICROPY_KBD_EXCEPTION             (1)

// Enable core modules
#define MICROPY_PY_MICROPYTHON            (1)
#define MICROPY_PY_BUILTINS_HELP          (1)
#define MICROPY_PY_BUILTINS_HELP_MODULES  (1)
#define MICROPY_PY_GC                     (1)
#define MICROPY_PY_BUILTINS_STR_UNICODE   (1)
#define MICROPY_PY_BUILTINS_FLOAT         (0)  // keep at 0 for RV32I without soft float
#define MICROPY_PY_BUILTINS_COMPLEX       (0)
#define MICROPY_PY_IO                     (0)  // no file system or streams in minimal yet
#define MICROPY_PY_ARRAY                  (0)
#define MICROPY_PY_COLLECTIONS            (0)
#define MICROPY_PY_MATH                   (0)
#define MICROPY_PY_URANDOM                (0)
#define MICROPY_PY_STRUCT                 (0)
#define MICROPY_PY_ERRNO                  (0)
#define MICROPY_PY_BINASCII               (0)
#define MICROPY_PY_RE                     (0)
#define MICROPY_PY_UCTYPES                (0)

#define MICROPY_PY_SYS                    (1)
#define MICROPY_PY_SYS_MODULES            (1)
#define MICROPY_PY_SYS_PLATFORM           "riscv-emu.py"
#define MICROPY_PY_SYS_STDIO              (1)
#define MICROPY_PY_SYS_EXC_INFO           (1)
#define MICROPY_PY_SYS_IMPL               (1)
#define MICROPY_PY_SYS_ARGV               (1)

#define MICROPY_PY_BUILTINS_SLICE         (0)
#define MICROPY_PY_ALL_FEATURES           (0)

#define MICROPY_ALLOC_PATH_MAX            (256)

// Use the minimum headroom in the chunk allocator for parse nodes.
#define MICROPY_ALLOC_PARSE_CHUNK_INIT    (16)

// type definitions for the specific machine

typedef intptr_t mp_int_t; // must be pointer size
typedef uintptr_t mp_uint_t; // must be pointer size
typedef long mp_off_t;

// We need to provide a declaration/definition of alloca()
#include <alloca.h>

#define MICROPY_HW_BOARD_NAME "minimal"
#define MICROPY_HW_MCU_NAME "risc-emu.py"

#define MP_STATE_PORT MP_STATE_VM
