ENTRY(_start)

MEMORY
{
  RAM (rwx) : ORIGIN = 0x00000000, LENGTH = 1M
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

  /* Heap and Stack regions */
  . = ALIGN(8);
  end = .;
  __heap_start = .;

  __stack_top = ORIGIN(RAM) + LENGTH(RAM);
  __freertos_irq_stack_top = __stack_top;
  __stack_bottom = __stack_top - 128K;
  __heap_end = __stack_bottom;

  PROVIDE(_end = end);
  PROVIDE(_heap_start = __heap_start);
  PROVIDE(_heap_end = __heap_end);
  PROVIDE(_stack_top = __stack_top);
  PROVIDE(_stack_bottom = __stack_bottom);
  PROVIDE(_global_pointer$ = __global_pointer$);
}
