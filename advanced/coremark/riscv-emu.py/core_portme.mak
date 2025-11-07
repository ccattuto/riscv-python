# Copyright 2018 Embedded Microprocessor Benchmark Consortium (EEMBC)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# 
# Original Author: Shay Gal-on

#File : core_portme.mak

# Flag : OUTFLAG
#	Use this flag to define how to to get an executable (e.g -o)
OUTFLAG= -o
# Flag : CC
#	Use this flag to define compiler to use
CC 		= riscv64-unknown-elf-gcc
# Flag : LD
#	Use this flag to define compiler to use
LD		= $(CC)
# Flag : AS
#	Use this flag to define compiler to use
AS		= $(CC)

# Extension options - set to 1 to enable, 0 to disable
# Pass these on command line: make PORT_DIR=../riscv-emu.py RVC=1 MUL=1
export RVC ?= 0  # Compressed Instructions (C extension)
export MUL ?= 0  # Multiply/Divide (M extension)
export RVA ?= 0  # Atomic Instructions (A extension)

# Build march string based on extensions enabled (canonical order: I, M, A, F, D, C)
MARCH_BASE = rv32i
MARCH_EXT = $(if $(filter 1,$(MUL)),m,)$(if $(filter 1,$(RVA)),a,)$(if $(filter 1,$(RVC)),c,)
MARCH = $(MARCH_BASE)$(MARCH_EXT)_zicsr

# Flag : CFLAGS
#	Use this flag to define compiler options. Note, you can add compiler options from the command line using XCFLAGS="other flags"
PORT_CFLAGS = -march=$(MARCH) -mabi=ilp32 -O2 -D_REENT_SMALL
FLAGS_STR = "$(PORT_CFLAGS) $(XCFLAGS) $(XLFLAGS) $(LFLAGS_END)"
CFLAGS = $(PORT_CFLAGS) -I$(PORT_DIR) -I. -DFLAGS_STR=\"$(FLAGS_STR)\"
#Flag : LFLAGS_END
#	Define any libraries needed for linking or other flags that should come at the end of the link line (e.g. linker scripts).
#	Note : On certain platforms, the default clock_gettime implementation is supported but requires linking of librt.
SEPARATE_COMPILE=1
# Flag : SEPARATE_COMPILE
# You must also define below how to create an object file, and how to link.
OBJOUT 	= -o
LFLAGS 	= -march=$(MARCH) -mabi=ilp32 -nostartfiles -static -T$(PORT_DIR)/linker_newlib.ld --specs=nano.specs
ASFLAGS = $(CFLAGS)
OFLAG 	= -o
COUT 	= -c

LFLAGS_END = 
# Flag : PORT_SRCS
# 	Port specific source files can be added here
#	You may also need cvt.c if the fcvt functions are not provided as intrinsics by your compiler!
PORT_SRCS = $(PORT_DIR)/start_newlib.S $(PORT_DIR)/syscalls_newlib.S $(PORT_DIR)/core_portme.c
PORT_OBJS = $(PORT_DIR)/start_newlib.o $(PORT_DIR)/syscalls_newlib.o $(PORT_DIR)/core_portme.o
vpath %.c $(PORT_DIR)
vpath %.S $(PORT_DIR)

# Flag : LOAD
#	For a simple port, we assume self hosted compile and run, no load needed.

# Flag : RUN
#	For a simple port, we assume self hosted compile and run, simple invocation of the executable

LOAD = echo
RUN = $(PORT_DIR)/risc-emu-wrapper

OEXT = .o
EXE = .elf

$(OPATH)$(PORT_DIR)/%$(OEXT) : %.c
	$(CC) $(CFLAGS) $(XCFLAGS) $(COUT) $< $(OBJOUT) $@

$(OPATH)%$(OEXT) : %.c
	$(CC) $(CFLAGS) $(XCFLAGS) $(COUT) $< $(OBJOUT) $@

$(OPATH)$(PORT_DIR)/%$(OEXT) : %.S
	$(AS) $(ASFLAGS) $(COUT) $< $(OBJOUT) $@

# Target : port_pre% and port_post%
# For the purpose of this simple port, no pre or post steps needed.

.PHONY : port_prebuild port_postbuild port_prerun port_postrun port_preload port_postload
port_pre% port_post% : 

# FLAG : OPATH
# Path to the output folder. Default - current folder.
OPATH = ./
MKDIR = mkdir -p

