#include <stdio.h>
#include "py/obj.h"
#include "py/lexer.h"
#include "py/stream.h"
#include "py/runtime.h"
#include "py/builtin.h"
#include "py/mpprint.h"

// Stub: If nlr fails, just halt.
void nlr_jump_fail(void *val) {
    printf("FATAL: nlr_jump_fail\n");
    while (1);
}

// Stub: We have no filesystem
mp_import_stat_t mp_import_stat(const char *path) {
    return MP_IMPORT_STAT_NO_EXIST;
}

// Stub: no file-based imports
mp_lexer_t *mp_lexer_new_from_file(qstr filename) {
    printf("FATAL: mp_lexer_new_from_file() not supported\n");
    return NULL;
}

static mp_uint_t mp_dummy_stream_read(mp_obj_t self, void *buf, mp_uint_t size, int *errcode) {
    *errcode = MP_EIO;
    return MP_STREAM_ERROR;
}

static mp_uint_t mp_dummy_stream_write(mp_obj_t self, const void *buf, mp_uint_t size, int *errcode) {
    *errcode = MP_EIO;
    return MP_STREAM_ERROR;
}

static void mp_dummy_stream_print(const mp_print_t *print, mp_obj_t self, mp_print_kind_t kind) {
    mp_print_str(print, "<dummy_stream>");
}

// Stream protocol table
static const mp_stream_p_t dummy_stream_p = {
    .read = mp_dummy_stream_read,
    .write = mp_dummy_stream_write,
    .is_text = false,
};

// Object type using new macro
MP_DEFINE_CONST_OBJ_TYPE(
    mp_dummy_stream_type,
    MP_QSTR_dummy_stream,
    MP_TYPE_FLAG_NONE,
    print, mp_dummy_stream_print,
    protocol, &dummy_stream_p
);

const mp_obj_base_t mp_sys_stdin_obj  = { &mp_dummy_stream_type };
const mp_obj_base_t mp_sys_stdout_obj = { &mp_dummy_stream_type };
const mp_obj_base_t mp_sys_stderr_obj = { &mp_dummy_stream_type };
