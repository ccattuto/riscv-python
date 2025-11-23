include ../micropython//py/mkenv.mk

CROSS = 1

# qstr definitions (must come before including py.mk)
QSTR_DEFS = qstrdefsport.h

# MicroPython feature configurations
MICROPY_ROM_TEXT_COMPRESSION ?= 1

# Mode selection (default to REPL_SYSCALL for backwards compatibility)
# Valid values: REPL_SYSCALL, HEADLESS, UART
MODE ?= REPL_SYSCALL

# Script to embed (for HEADLESS and UART modes)
FROZEN_SCRIPT ?= startup.py

# include py core make definitions
include $(TOP)/py/py.mk

ifeq ($(CROSS), 1)
CROSS_COMPILE ?= riscv64-unknown-elf-
endif

# Mode-specific configuration
ifeq ($(MODE),REPL_SYSCALL)
    MODE_FLAG = MODE_REPL_SYSCALL
else ifeq ($(MODE),HEADLESS)
    MODE_FLAG = MODE_HEADLESS
else ifeq ($(MODE),UART)
    MODE_FLAG = MODE_UART
else
    $(error Invalid MODE=$(MODE). Valid values: REPL_SYSCALL, HEADLESS, UART)
endif

# MicroPython build tools
MPY_CROSS ?= $(TOP)/mpy-cross/build/mpy-cross
MPY_TOOL ?= $(PYTHON) $(TOP)/tools/mpy-tool.py


# Extension options - set to 1 to enable, 0 to disable
# Note: the toolchain might not support all combinations
RVM ?= 1  # Multiply/Divide (M extension)
RVA ?= 0  # Compressed Instructions (C extension)
RVC ?= 0  # Atomic Instructions (A extension)

# Build march string based on extensions enabled (canonical order: I, M, A, F, D, C)
MARCH_BASE = rv32i
MARCH_EXT = $(if $(filter 1,$(RVM)),m,)$(if $(filter 1,$(RVA)),a,)$(if $(filter 1,$(RVC)),c,)
MARCH = $(MARCH_BASE)$(MARCH_EXT)_zicsr

INC += -I.
INC += -I$(TOP)
INC += -I$(BUILD)

ifeq ($(CROSS), 1)
DFU = $(TOP)/tools/dfu.py
PYDFU = $(TOP)/tools/pydfu.py
CFLAGS_RISCV  = -march=$(MARCH) -mabi=ilp32 -D_REENT_SMALL
CFLAGS += $(INC) -Wall -Werror -std=c99 $(CFLAGS_RISCV) $(COPT) -DMICROPY_PORT_MODE=$(MODE_FLAG)
# All modes use Newlib linker script and specs
LDFLAGS += -nostartfiles -static -Tlinker_newlib.ld --specs=nosys.specs
else
UNAME_S := $(shell uname -s)
LD = $(CC)
CFLAGS += $(INC) -Wall -Werror -Wdouble-promotion -Wfloat-conversion -std=c99 $(COPT) -DMICROPY_PORT_MODE=$(MODE_FLAG)
# All modes use Newlib
ifeq ($(UNAME_S),Linux)
LDFLAGS += -nostartfiles -Wl,--gc-sections -static -Tlinker_newlib.ld --specs=nano.specs -Wl,-map,$@.map -Wl,-dead_strip
else ifeq ($(UNAME_S),Darwin)
LDFLAGS += -nostartfiles -Wl,--gc-sections -static -Tlinker_newlib.ld --specs=nano.specs -Wl,-map,$@.map -Wl,-dead_strip
endif
endif

CSUPEROPT = -Os # save some code space

# Tune for Debugging or Optimization
#CFLAGS += -g
ifeq ($(DEBUG), 1)
CFLAGS += -O0
else
CFLAGS += -O2 -DNDEBUG
CFLAGS += -fdata-sections -ffunction-sections
endif

# Flags for optional C++ source code
CXXFLAGS += $(filter-out -std=c99,$(CFLAGS))

# Libraries (all modes use Newlib)
# Need libgcc for 64-bit integer ops, libc for standard functions, libm for math
LIBS = -lc -lm -lgcc

# Common source files for all modes
SRC_C = \
	main.c \
	gccollect.c \
	shared/readline/readline.c \
	shared/runtime/pyexec.c \
	shared/runtime/gchelper_native.c \
	shared/runtime/stdout_helpers.c \
	extmod/modmachine.c \
	extmod/machine_mem.c \
	extmod/moductypes.c

# Mode-specific source files
# All modes use Newlib startup and syscalls (since we link Newlib libraries)
SRC_C += minimal_stubs.c shared/libc/printf.c
SRC_S = start_newlib.S syscalls_newlib.S gchelper_rv32i.S

# Select HAL based on mode
ifeq ($(MODE),REPL_SYSCALL)
    # Mode 1: syscall-based I/O
    SRC_C += mphalport.c
else ifeq ($(MODE),HEADLESS)
    # Mode 2: silent (no I/O)
    SRC_C += mphalport_silent.c
else ifeq ($(MODE),UART)
    # Mode 3: UART MMIO I/O
    SRC_C += mphalport_uart.c
endif

ifeq ($(CROSS), 1)
SRC_C += shared/libc/string0.c
endif

SRC_QSTR += shared/readline/readline.c shared/runtime/pyexec.c extmod/modmachine.c extmod/machine_mem.c extmod/moductypes.c

SRC_S = \
	start_newlib.S \
    syscalls_newlib.S \
	gchelper_rv32i.S

OBJ += $(PY_CORE_O)
OBJ += $(addprefix $(BUILD)/, $(SRC_C:.c=.o))
OBJ += $(addprefix $(BUILD)/, $(SRC_S:.S=.o))
OBJ += $(addprefix $(BUILD)/, $(SRC_CXX:.cpp=.o))

ifeq ($(CROSS), 1)
all: $(BUILD)/firmware.dfu
else
all: $(BUILD)/firmware.elf
endif

# Print build configuration
$(info Building MicroPython port in MODE=$(MODE))


$(BUILD)/firmware.elf: $(OBJ)
	$(ECHO) "LINK $@"
	$(Q)$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $^ $(LIBS)
	$(Q)$(SIZE) $@

$(BUILD)/firmware.bin: $(BUILD)/firmware.elf
	$(Q)$(OBJCOPY) -O binary -j .isr_vector -j .text -j .data $^ $(BUILD)/firmware.bin

$(BUILD)/firmware.dfu: $(BUILD)/firmware.bin
	$(ECHO) "Create $@"
	$(Q)$(PYTHON) $(DFU) -b 0x08000000:$(BUILD)/firmware.bin $@

deploy: $(BUILD)/firmware.dfu
	$(ECHO) "Writing $< to the board"
	$(Q)$(PYTHON) $(PYDFU) -u $<

# Run emulation build on a POSIX system with suitable terminal settings
run:
	@saved_=`stty -g`; \
	  stty raw opost -echo; \
	  $(BUILD)/firmware.elf; \
	  echo "Exit status: $$?"; \
	  stty $$saved_

test: $(BUILD)/firmware.elf
	$(Q)/usr/bin/printf "print('hello world!', list(x+1 for x in range(10)), end='eol\\\\n')\\r\\n\\004" | $(BUILD)/firmware.elf | tail -n2 | grep "^hello world! \\[1, 2, 3, 4, 5, 6, 7, 8, 9, 10\\]eol"

include $(TOP)/py/mkrules.mk

# Frozen module support for headless and UART modes
ifeq ($(MODE),HEADLESS)
    FROZEN_ENABLED = 1
else ifeq ($(MODE),UART)
    FROZEN_ENABLED = 1
else
    FROZEN_ENABLED = 0
endif

ifeq ($(FROZEN_ENABLED),1)
    # Extract module name from script filename (remove .py extension)
    FROZEN_MODULE_NAME = $(basename $(FROZEN_SCRIPT))

    # Add define to CFLAGS so main.c knows which module to load
    CFLAGS += -DFROZEN_MODULE_NAME=\"$(FROZEN_MODULE_NAME)\"

    # Compile Python script to .mpy bytecode
    $(BUILD)/$(FROZEN_SCRIPT:.py=.mpy): $(FROZEN_SCRIPT)
	$(ECHO) "MPY $(FROZEN_SCRIPT)"
	$(Q)$(MPY_CROSS) -o $@ -s $(FROZEN_MODULE_NAME) $<

    # Generate C code from .mpy bytecode
    $(BUILD)/_frozen_mpy.c: $(BUILD)/$(FROZEN_SCRIPT:.py=.mpy) $(BUILD)/genhdr/qstrdefs.generated.h
	$(ECHO) "MISC freezing bytecode"
	$(Q)$(MPY_TOOL) -f -q $(BUILD)/genhdr/qstrdefs.preprocessed.h -mlongint-impl=longlong $< > $@

    # Add frozen module C file to sources
    SRC_C += $(BUILD)/_frozen_mpy.c

    # Make firmware depend on frozen module
    $(BUILD)/firmware.elf: $(BUILD)/_frozen_mpy.c
endif
