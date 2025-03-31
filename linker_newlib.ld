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
    *(.rodata*)
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

  .bss : ALIGN(4)
  {
    __bss_start = .;
    *(.bss*)
    *(COMMON)
    __bss_end = .;
  } > RAM

  /* Heap and Stack regions */
  . = ALIGN(4);
  end = .; /* <-- needed for _sbrk */
  __stack_top = ORIGIN(RAM) + LENGTH(RAM);

  PROVIDE(_end = end);
  PROVIDE(_stack_top = __stack_top);
}
