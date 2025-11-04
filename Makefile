# Toolchain and tools
CC = riscv64-linux-gnu-gcc
OBJCOPY = riscv64-linux-gnu-objcopy

# Flags - ENABLE RVC (Compressed Instructions)
CFLAGS_COMMON = -march=rv32ic_zicsr -mabi=ilp32 -O2 -D_REENT_SMALL -I .
LDFLAGS_COMMON = -nostartfiles -static
LINKER_SCRIPT_NEWLIB = -Tlinker_newlib.ld
LINKER_SCRIPT_BARE = -Tlinker_bare.ld
NEWLIB_SPECS = --specs=nosys.specs
NEWLIB_NANO_SPECS = --specs=nano.specs

# Source file groups
ASM_TARGETS = test_asm1
BARE_TARGETS = test_bare1
NEWLIB_NANO_TARGETS = test_newlib1 test_newlib2 test_newlib3 test_newlib4 test_newlib5 \
                 test_newlib6 test_newlib7 test_newlib8 test_newlib9 test_newlib10 test_newlib11 \
				 test_peripheral_uart test_peripheral_blkdev test_newlib13
NEWLIB_TARGETS = test_newlib12

ALL_ELF_TARGETS = $(addprefix build/,$(addsuffix .elf,$(ASM_TARGETS) $(BARE_TARGETS) $(NEWLIB_NANO_TARGETS) $(NEWLIB_TARGETS)))
ALL_BIN_TARGETS = $(addprefix build/,$(addsuffix .bin,$(ASM_TARGETS) $(BARE_TARGETS)))

# Object file suffixes (all compiled into build/)
STARTUP_NEWLIB = build/start_newlib.o
STARTUP_BARE = build/start_bare.o
SYSCALLS_NEWLIB = build/syscalls_newlib.o

# Default build
all: $(ALL_ELF_TARGETS) $(ALL_BIN_TARGETS)

# --- ASM-only targets ---
$(addprefix build/,$(ASM_TARGETS:%=%.elf)): build/%.elf: build/%.o
	$(CC) $(CFLAGS_COMMON) $(LDFLAGS_COMMON) -Ttext=0 -nostdlib -o $@ $^

# --- Bare-metal C targets (no newlib) ---
$(addprefix build/,$(BARE_TARGETS:%=%.elf)): build/%.elf: $(STARTUP_BARE) build/%.o
	$(CC) $(CFLAGS_COMMON) $(LDFLAGS_COMMON) $(LINKER_SCRIPT_BARE) -nostdlib -o $@ $^

# --- Newlib nano targets ---
$(addprefix build/,$(NEWLIB_NANO_TARGETS:%=%.elf)): build/%.elf: $(STARTUP_NEWLIB) $(SYSCALLS_NEWLIB) build/%.o
	$(CC) $(CFLAGS_COMMON) $(LDFLAGS_COMMON) $(LINKER_SCRIPT_NEWLIB) $(NEWLIB_NANO_SPECS) -o $@ $^

# --- Newlib (full) + libm targets ---
$(addprefix build/,$(NEWLIB_TARGETS:%=%.elf)): build/%.elf: $(STARTUP_NEWLIB) $(SYSCALLS_NEWLIB) build/%.o
	$(CC) $(CFLAGS_COMMON) $(LDFLAGS_COMMON) $(LINKER_SCRIPT_NEWLIB) $(NEWLIB_SPECS) -o $@ $^ -lm

# --- Generate .bin from .elf (only for asm and bare) ---
$(addprefix build/,$(ASM_TARGETS:%=%.bin)): build/%.bin: build/%.elf
	$(OBJCOPY) -O binary $< $@

$(addprefix build/,$(BARE_TARGETS:%=%.bin)): build/%.bin: build/%.elf
	$(OBJCOPY) -O binary $< $@

# --- Compile rules ---
# From tests/
build/%.o: tests/%.S | build
	$(CC) $(CFLAGS_COMMON) -c -o $@ $<

build/%.o: tests/%.c | build
	$(CC) $(CFLAGS_COMMON) -c -o $@ $<

# From root (startup/syscalls)
build/%.o: %.S | build
	$(CC) $(CFLAGS_COMMON) -c -o $@ $<

build/%.o: %.c | build
	$(CC) $(CFLAGS_COMMON) -c -o $@ $<

# Ensure build dir exists
build:
	mkdir -p $@

# Clean
clean:
	rm -rf build

.PHONY: all clean
