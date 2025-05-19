#include "shared-bindings/board/__init__.h"
    
static const mp_rom_map_elem_t board_module_globals_table[] = {
    CIRCUITPYTHON_BOARD_DICT_STANDARD_ITEMS
};

MP_DEFINE_CONST_DICT(board_module_globals, board_module_globals_table);

const mp_obj_dict_t mcu_pin_globals = {
    // Pin definitions (must exist)
};

