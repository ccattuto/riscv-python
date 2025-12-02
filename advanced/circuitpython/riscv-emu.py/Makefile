TOP = ../circuitpython

BOARD ?= riscv-emu.py
PORT_DIR := $(CURDIR)
BUILD ?= $(PORT_DIR)/build-$(BOARD)

include circuitpy_mkenv.mk

CROSS_COMPILE = /opt/riscv/bin/riscv32-unknown-elf-

INC += \
	-I. \
	-I../.. \
	-I../lib/mp-readline \
	-I../shared/runtime \
	-I$(TOP) \
	-Iboards/$(BOARD) \
	-Iboards/ \
	-I$(BUILD)

MARCH_BASE = rv32i
RVM ?= 1
MARCH_EXT = $(if $(filter 1,$(RVM)),m,)$(if $(filter 1,$(RVA)),a,)$(if $(filter 1,$(RVC)),c,)
MARCH = $(MARCH_BASE)$(MARCH_EXT)_zicsr

CFLAGS += -Os

DISABLE_WARNINGS = -Wno-cast-align
CFLAGS += $(INC) -Wall -Werror -std=gnu11 -fshort-enums $(BASE_CFLAGS) $(CFLAGS_MOD) $(COPT) $(DISABLE_WARNINGS) -Werror=missing-prototypes

CFLAGS += \
	-march=$(MARCH) \
	-mabi=ilp32 \
	-D_REENT_SMALL \
	-nostartfiles \
	-static \
	--specs=nano.specs

CFLAGS += -DCIRCUITPY_CONSOLE_UART_RX -DCIRCUITPY_CONSOLE_UART_TX
# Use toolchain libm if we're not using our own.
ifndef INTERNAL_LIBM
LIBS += -lm
endif

LIBS += -lc

SRC_C += \
	boards/$(BOARD)/board.c \
	boards/$(BOARD)/pins.c \
	background.c \
	mphalport.c \
	gccollect.c

SRC_ASM = start.S gchelper_rv32i.S trap_handler.S

SRC_COMMON_HAL_EXPANDED = $(addprefix shared-bindings/, $(SRC_COMMON_HAL)) \
                          $(addprefix shared-bindings/, $(SRC_BINDINGS_ENUMS)) \
                          $(addprefix common-hal/, $(SRC_COMMON_HAL))

SRC_SHARED_MODULE_EXPANDED = $(addprefix shared-bindings/, $(SRC_SHARED_MODULE)) \
                             $(addprefix shared-module/, $(SRC_SHARED_MODULE)) \
                             $(addprefix shared-module/, $(SRC_SHARED_MODULE_INTERNAL))

# There may be duplicates between SRC_COMMON_HAL_EXPANDED and SRC_SHARED_MODULE_EXPANDED,
# because a few modules have files both in common-hal/ and shared-module/.
# Doing a $(sort ...) removes duplicates as part of sorting.
SRC_COMMON_HAL_SHARED_MODULE_EXPANDED = $(sort $(SRC_COMMON_HAL_EXPANDED) $(SRC_SHARED_MODULE_EXPANDED))

SRC_S = # supervisor/riscvpy_cpu.s

OBJ = $(PY_O) $(SUPERVISOR_O) $(addprefix $(BUILD)/, $(SRC_C:.c=.o))
OBJ += $(addprefix $(BUILD)/, $(SRC_COMMON_HAL_SHARED_MODULE_EXPANDED:.c=.o))
ifeq ($(INTERNAL_LIBM),1)
OBJ += $(addprefix $(BUILD)/, $(SRC_LIBM:.c=.o))
endif
OBJ += $(addprefix $(BUILD)/, $(SRC_CIRCUITPY_COMMON:.c=.o))
OBJ += $(addprefix $(BUILD)/, $(SRC_S:.s=.o))
OBJ += $(addprefix $(BUILD)/, $(SRC_S_UPPER:.S=.o))
OBJ += $(addprefix $(BUILD)/, $(SRC_MOD:.c=.o))
OBJ += $(addprefix $(BUILD)/, $(SRC_ASM:.S=.o))

$(BUILD)/%.o: %.S
	$(STEPECHO) "AS $<"
	$(Q)$(CC) $(CFLAGS) -c -o $@ $<

SRC_QSTR += $(SRC_C) $(SRC_SUPERVISOR) $(SRC_COMMON_HAL_EXPANDED) $(SRC_SHARED_MODULE_EXPANDED) $(SRC_CIRCUITPY_COMMON)

all: $(BUILD)/firmware.elf $(BUILD)/firmware.bin $(BUILD)/circuitpy.img

BOARD_LD := $(wildcard boards/$(BOARD)/link.ld)

ifneq ($(BOARD_LD),)
	LINKER_SCRIPTS = -Wl,-T,$(BOARD_LD)
endif

LINKER_SCRIPTS += -Wl,-T,link.ld

$(BUILD)/circuitpy.img: circuitpy/code.py
	$(STEPECHO) "Create $@"
	$(Q)dd if=/dev/zero of=$(BUILD)/circuitpy.img bs=1 count=0 seek=512K
	/opt/homebrew/sbin/mkfs.fat -n CIRCUITPY --offset=0 $(BUILD)/circuitpy.img
	$(Q)mcopy -i $(BUILD)/circuitpy.img circuitpy/* ::

ifeq ($(VALID_BOARD),)
$(BUILD)/firmware.elf: invalid-board
else
$(BUILD)/firmware.elf: $(OBJ) $(BOARD_LD) link.ld
	$(STEPECHO) "LINK $@"
	$(Q)echo $(OBJ) > $(BUILD)/firmware.objs
	$(Q)echo $(PICO_LDFLAGS) > $(BUILD)/firmware.ldflags
	$(Q)$(CC) -o $@ $(CFLAGS) @$(BUILD)/firmware.ldflags $(LINKER_SCRIPTS) -Wl,--print-memory-usage -Wl,-Map=$@.map -Wl,-cref -Wl,--gc-sections @$(BUILD)/firmware.objs -Wl,-lc
endif

$(BUILD)/firmware.bin: $(BUILD)/firmware.elf
	$(STEPECHO) "Create $@"
	$(Q)$(OBJCOPY) -O binary -R .dtcm_bss $^ $@

include $(TOP)/py/mkrules.mk
