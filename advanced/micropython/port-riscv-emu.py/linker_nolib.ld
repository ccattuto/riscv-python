ENTRY(_start)

MEMORY
{
  RAM (rwx) : ORIGIN = 0x00000000, LENGTH = 4M
}

SECTIONS
{
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

  .gc_heap (NOLOAD) : ALIGN(4) {
    __gc_heap_start = .;
    . = . + 0x200000;  /* 2 MB for MicroPython GC */
     __gc_heap_end = .;
  } > RAM

  /* Stack region - no Newlib heap needed */
  . = ALIGN(8);
  end = .;

  __stack_top = ORIGIN(RAM) + LENGTH(RAM);
  __stack_bottom = __stack_top - 512K;

  PROVIDE(_end = end);
  PROVIDE(_gc_heap_start = __gc_heap_start);
  PROVIDE(_gc_heap_end = __gc_heap_end);
  PROVIDE(_stack_top = __stack_top);
  PROVIDE(_stack_bottom = __stack_bottom);
  PROVIDE(_global_pointer$ = __global_pointer$);
}
