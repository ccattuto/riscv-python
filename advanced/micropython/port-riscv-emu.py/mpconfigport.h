#include <stdint.h>

// options to control how MicroPython is built

// Mode definitions (set via Makefile)
#define MODE_REPL_SYSCALL    1  // REPL with syscalls
#define MODE_EMBEDDED_SILENT 2  // Frozen script, no I/O
#define MODE_REPL_UART       3  // REPL over UART MMIO
#define MODE_EMBEDDED_UART   4  // Frozen script + UART REPL

#ifndef MICROPY_PORT_MODE
#define MICROPY_PORT_MODE MODE_REPL_SYSCALL
#endif

// Use CORE_FEATURES ROM level as base, then explicitly enable what we need
#define MICROPY_CONFIG_ROM_LEVEL (MICROPY_CONFIG_ROM_LEVEL_CORE_FEATURES)

// Float support: only for REPL_SYSCALL mode
#if (MICROPY_PORT_MODE == MODE_REPL_SYSCALL)
    #define MICROPY_PY_BUILTINS_FLOAT         (1)
    #define MICROPY_FLOAT_IMPL                (MICROPY_FLOAT_IMPL_FLOAT)
    #define MICROPY_PY_MATH                   (1)
    #define MICROPY_PY_CMATH                  (0)
#else
    #define MICROPY_PY_BUILTINS_FLOAT         (0)
    #define MICROPY_FLOAT_IMPL                (MICROPY_FLOAT_IMPL_NONE)
    #define MICROPY_PY_MATH                   (0)
    #define MICROPY_PY_CMATH                  (0)
#endif

#define MICROPY_ENABLE_COMPILER     (1)
#define MICROPY_ENAVLE_REPL	        (1)
#define MICROPY_PY_BUILTINS_INPUT   (1)
#define MICROPY_PY_SYS_STDFILES     (1)

#define MICROPY_ENABLE_GC                 (1)
#define MICROPY_HELPER_REPL               (1)
#define MICROPY_ENABLE_REPL_HELPERS       (1)

// Enable frozen modules for embedded modes
#if (MICROPY_PORT_MODE == MODE_EMBEDDED_SILENT) || \
    (MICROPY_PORT_MODE == MODE_EMBEDDED_UART)
    #define MICROPY_MODULE_FROZEN_MPY         (1)
#else
    #define MICROPY_MODULE_FROZEN_MPY         (0)
#endif

#define MICROPY_ENABLE_EXTERNAL_IMPORT    (0)
#define MICROPY_KBD_EXCEPTION             (1)

// Enable core modules
#define MICROPY_PY_MICROPYTHON            (1)
#define MICROPY_PY_BUILTINS_HELP          (1)
#define MICROPY_PY_BUILTINS_HELP_MODULES  (1)
#define MICROPY_PY_GC                     (1)
#define MICROPY_PY_BUILTINS_STR_UNICODE   (1)

#define MICROPY_LONGINT_IMPL              (MICROPY_LONGINT_IMPL_LONGLONG)
#define MICROPY_PY_BUILTINS_COMPLEX       (0)
#define MICROPY_PY_IO                     (0)  // no file system or streams

// Explicitly enable modules we need (some may not be in CORE_FEATURES)
#define MICROPY_PY_ARRAY                  (1)
#define MICROPY_PY_COLLECTIONS            (1)
#define MICROPY_PY_COLLECTIONS_DEQUE      (1)
#define MICROPY_PY_COLLECTIONS_ORDEREDDICT (1)
#define MICROPY_PY_URANDOM                (1)
#define MICROPY_PY_URANDOM_SEED_INIT_FUNC (0)
#define MICROPY_PY_STRUCT                 (1)
#define MICROPY_PY_ERRNO                  (1)
#define MICROPY_PY_BINASCII               (1)
#define MICROPY_PY_RE                     (1)
#define MICROPY_PY_HEAPQ                  (1)
#define MICROPY_PY_HASHLIB                (0)
#define MICROPY_PY_JSON                   (1)
#define MICROPY_PY_UCTYPES                (1)

#define MICROPY_PY_SYS                    (1)
#define MICROPY_PY_SYS_MODULES            (1)
#define MICROPY_PY_SYS_PLATFORM           "riscv-emu.py"
#define MICROPY_PY_SYS_STDIO              (1)
#define MICROPY_PY_SYS_EXC_INFO           (1)
#define MICROPY_PY_SYS_IMPL               (1)
#define MICROPY_PY_SYS_ARGV               (1)

#define MICROPY_PY_BUILTINS_SLICE         (1)

#define MICROPY_ALLOC_PATH_MAX            (256)

// Use the minimum headroom in the chunk allocator for parse nodes.
#define MICROPY_ALLOC_PARSE_CHUNK_INIT    (16)

// type definitions for the specific machine

typedef intptr_t mp_int_t; // must be pointer size
typedef uintptr_t mp_uint_t; // must be pointer size
typedef long mp_off_t;

// Define SSIZE_MAX for bare-metal environment (32-bit system)
#define SSIZE_MAX INT32_MAX

// We need to provide a declaration/definition of alloca()
#include <alloca.h>

#define MICROPY_HW_BOARD_NAME "emulated"
#define MICROPY_HW_MCU_NAME "riscv-emu.py"

#define MP_STATE_PORT MP_STATE_VM
