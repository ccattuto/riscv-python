# Toolchain and tools
CC = riscv64-unknown-elf-gcc
OBJDUMP = riscv64-unknown-elf-objdump
OBJCOPY = riscv64-unknown-elf-objcopy

# Flags
CFLAGS_COMMON = -march=rv32i -mabi=ilp32 -O2
LDFLAGS_COMMON = -nostartfiles -static
LINKER_SCRIPT_NEWLIB = -Tlinker_newlib.ld
LINKER_SCRIPT_BARE = -Tlinker_bare.ld
NEWLIB_SPECS = --specs=nano.specs --specs=nosys.specs

# Source file groups
ASM_TARGETS = test_asm1
BARE_TARGETS = test_bare1
NEWLIB_TARGETS = test_newlib1

# Object file suffixes
STARTUP_NEWLIB = start_newlib.o
STARTUP_BARE = start_bare.o
SYSCALLS_NEWLIB = syscalls_newlib.o

# Default build
all: $(addsuffix .elf,$(ASM_TARGETS) $(BARE_TARGETS) $(NEWLIB_TARGETS)) \
     $(addsuffix .bin,$(ASM_TARGETS) $(BARE_TARGETS))

# --- ASM-only targets ---
$(ASM_TARGETS:%=%.elf): %.elf: %.o
	$(CC) $(CFLAGS_COMMON) $(LDFLAGS_COMMON) -Ttext=0 -nostdlib -o $@ $^

# --- Bare-metal C targets (no newlib) ---
$(BARE_TARGETS:%=%.elf): %.elf: $(STARTUP_BARE) %.o
	$(CC) $(CFLAGS_COMMON) $(LDFLAGS_COMMON) $(LINKER_SCRIPT_BARE) -nostdlib -o $@ $^

# --- Newlib targets (newlib support) ---
$(NEWLIB_TARGETS:%=%.elf): %.elf: $(STARTUP_NEWLIB) $(SYSCALLS_NEWLIB) %.o
	$(CC) $(CFLAGS_COMMON) $(LDFLAGS_COMMON) $(LINKER_SCRIPT_NEWLIB) $(NEWLIB_SPECS) -o $@ $^

# Generate .bin from .elf
$(BARE_TARGETS:%=%.bin): %.bin: %.elf
	$(OBJCOPY) -O binary $< $@

$(ASM_TARGETS:%=%.bin): %.bin: %.elf
	$(OBJCOPY) -O binary $< $@

# Compile rules
%.o: %.S
	$(CC) $(CFLAGS_COMMON) -c -o $@ $<

%.o: %.c
	$(CC) $(CFLAGS_COMMON) -c -o $@ $<

clean:
	rm -f *.o *.elf *.bin *.map *.dump

.PHONY: all clean run
