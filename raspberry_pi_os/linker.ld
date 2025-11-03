/* Linker Script: Defines the memory layout */
 
ENTRY(_start)

SECTIONS {
  . = 0x80000; /* The kernel code must start at the address 0x80000 for Raspberry Pi. */
  .text : { *(.text) } :read_execute  /* Code goes here. */
  
  .rodata : { *(.rodata) } :read_only /* Initialized read-only data go here. */
  
  .data : { *(.data) } :read_write /* Initialized data go here. */
    
  /* BSS Section: Uninitialized data (like the stack) go here. */
  /* This section is ONLY reserved in memory; nothing is written to the output file. */
  .bss : {
     . = ALIGN(16);
     . = . + 0x10000;  /* Reserve 64KB for the stack */
     __stack_top = .;  /* Set the label __stack_top to the end of the reserved space */
   } :read_write
    
  /* /DISCARD/ section: Get rid of any unused/unwanted sections */
  /DISCARD/ : { 
    *(.note.gnu.build-id)
    *(.ARM.exidx)
  }
}

/* Define the loadable segments and set their permissions */
PHDRS { 
  read_execute PT_LOAD FLAGS(5); /* R + X */
  read_only    PT_LOAD FLAGS(4); /* R */
  read_write   PT_LOAD FLAGS(6); /* R + W */   
}
