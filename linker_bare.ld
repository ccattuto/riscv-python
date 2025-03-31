ENTRY(_start)

MEMORY
{
  RAM (rwx) : ORIGIN = 0x00000000, LENGTH = 1M
}

SECTIONS
{
  . = 0x00000000;

  .text : {
    *(.text._start)
    *(.text*)
  }

  .rodata : {
    *(.rodata*)
  }

  .data : {
    *(.data*)
  }

  .bss : {
    *(.bss*)
    *(COMMON)
  }

  . = ALIGN(4);
  end = .;
  __stack_top = ORIGIN(RAM) + LENGTH(RAM);

  PROVIDE(_end = end);
  PROVIDE(_stack_top = __stack_top);
}
