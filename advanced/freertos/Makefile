# toolchain
CC = riscv64-unknown-elf-gcc
LD = riscv64-unknown-elf-ld

# directories
KERNEL = ./FreeRTOS-Kernel
PORT = ./port

# whether machine timer registers are memory-mapped or CSR-based
MTIMER_MMIO = 0

# common source files: start files + emulator headers + FreeRTOS kernel components
COMMON_SRCS = \
    $(KERNEL)/tasks.c \
    $(KERNEL)/list.c \
    $(KERNEL)/queue.c \
    $(KERNEL)/timers.c \
    $(KERNEL)/event_groups.c \
    $(KERNEL)/portable/MemMang/heap_4.c \
    $(KERNEL)/portable/GCC/RISC-V/port.c \
    $(KERNEL)/portable/GCC/RISC-V/portASM.S \
    $(PORT)/start.S \
    $(PORT)/port_riscvpy.c \
    $(PORT)/syscalls_newlib.S

# modified trap handler for CSR-based machine timer
ifeq ($(MTIMER_MMIO), 0)
COMMON_SRCS += $(PORT)/trap_handler.S
endif

APPS = freertos_app1.c freertos_app2.c freertos_app3.c

CFLAGS = -Wall -Wextra -O2 -march=rv32i_zicsr -mabi=ilp32 -D_REENT_SMALL \
         -I. -I$(PORT) -I$(KERNEL)/include -I$(KERNEL)/portable/GCC/RISC-V \
         -DMTIMER_MMIO=${MTIMER_MMIO}

LDFLAGS = -T$(PORT)/linker_riscvpy.ld -nostartfiles -static --specs=nano.specs

TARGETS = $(APPS:.c=.elf)

all: $(TARGETS)

%.elf: %.c $(COMMON_SRCS)
	$(CC) $(CFLAGS) $(COMMON_SRCS) $< $(LDFLAGS) -o $@

clean:
	rm -f $(TARGETS) *.o
