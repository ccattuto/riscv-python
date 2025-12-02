ENTRY(_start)

MEMORY
{
  RAM (rwx) : ORIGIN = 0x00000000, LENGTH = 4M
}

SECTIONS
{
  . = 0x00000000;

  .text : ALIGN(4)
  {
    KEEP(*(.init))
    KEEP(*(.text.startup))
    *(.text*)
  } > RAM

  .rodata : ALIGN(4)
  {
    KEEP(*(.rodata*))
    KEEP(*(.srodata*))
  } > RAM

  .data : ALIGN(4)
  {
    *(.data*)
  } > RAM

  .sdata : ALIGN(4)
  {
    __global_pointer$ = . + 0x800;  /* required for gp-relative addressing */
    *(.sdata*)
  } > RAM

  .bss : ALIGN(8)
  {
    __bss_start = .;
    *(.bss*)
    *(COMMON)
    __bss_end = .;
  } > RAM

  .sbss : ALIGN(4)
  {
    __sbss_start = .;
    *(.sbss*)
    __sbss_end = .;
  } > RAM

  .pystack (NOLOAD):
  {
    . = ALIGN(8);
    __pystack_start = .;
    . = . + 64K;
    __pystack_end = .;
  } >RAM

  .gc_heap (NOLOAD) : ALIGN(8) {
    __gc_heap_start = .;
    . = . + 0x200000;  /* 2 Mb for MicroPython GC */
    __gc_heap_end = .;
  } > RAM

  /* Heap and Stack regions */
  . = ALIGN(8);
  end = .;
  __heap_start = .;

  __stack_top = ORIGIN(RAM) + LENGTH(RAM);
  __stack_bottom = __stack_top - 512K;
  __heap_end = __stack_bottom;

  PROVIDE(_estack = __stack_top);
  PROVIDE(_ebss = __bss_end);
  PROVIDE(_end = end);
  PROVIDE(_heap_start = __heap_start);
  PROVIDE(_heap_end = __heap_end);
  PROVIDE(_gc_heap_start = __gc_heap_start);
  PROVIDE(_gc_heap_end = __gc_heap_end);
  PROVIDE(_pystack_start = __pystack_start);
  PROVIDE(_pystack_end = __pystack_end);
  PROVIDE(_stack_top = __stack_top);
  PROVIDE(_stack_bottom = __stack_bottom);
  PROVIDE(_global_pointer$ = __global_pointer$);
}

