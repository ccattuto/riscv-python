# ---------------------
# Configuration
# ---------------------
TARGET      := test
ARCH        := rv32i
ABI         := ilp32
CC          := riscv64-unknown-elf-gcc
CFLAGS      := -march=$(ARCH) -mabi=$(ABI) -O2
LDFLAGS     := -Ttext=0 -nostartfiles --specs=nano.specs --specs=nosys.specs -static # -Wl,-u,_printf_float
OBJDUMP     := riscv64-unknown-elf-objdump
OBJCOPY     := riscv64-unknown-elf-objcopy

# ---------------------
# Source files
# ---------------------
SRCS        := start.S syscalls.S $(TARGET).c
OBJS        := $(SRCS:.c=.o)
OBJS        := $(OBJS:.S=.o)

# ---------------------
# Build rules
# ---------------------
all: $(TARGET).elf

$(TARGET).elf: $(OBJS)
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $^

%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

%.o: %.S
	$(CC) $(CFLAGS) -c -o $@ $<

clean:
	rm -f *.o *.elf *.bin *.dump *.map

dump: $(TARGET).elf
	$(OBJDUMP) -D -Mintel -S $< > $(TARGET).dump

bin: $(TARGET).elf
	$(OBJCOPY) -O binary $< $(TARGET).bin

.PHONY: all clean dump bin
