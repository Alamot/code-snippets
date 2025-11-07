// A 64-bit (AArch64) kernel for the Raspberry Pi. 
// Author: Alamot 

/******************************************************************************/
/* A note of caution                                                          */ 
/******************************************************************************/
/* When programming in ARM AArch64 assembly, it is important to exercise      */
/* caution regarding both control flow and data alignment.                    */ 
/*                                                                            */
/* Unlike x86, where the return address is automatically pushed onto the      */ 
/* stack by the CALL instruction, ARM uses the link register (x30 aka lr)     */
/* to store the return address. This means that each BL (Branch with Link)    */ 
/* overwrites the previous value of x30. If a function makes another BL call  */
/* without first saving the content of the link register (for example,        */
/* by pushing it onto the stack), the original return address will be lost    */
/* forever, causing return to a wrong place.                                  */ 
/*                                                                            */
/* Be also mindful of data alignment requirements when accessing memory.      */  
/* Many load and store instructions require the addresses to be aligned to    */
/* specific boundaries (e.g. LDHR (Load halfword) needs a 2-byte alignment).  */ 
/* Misaligned accesses can cause alignment faults or degrade performance.     */
/* Ensuring proper alignment of data structures and using alignment           */
/* directives (.aling) where necessary helps maintain both correctness and    */
/* efficiency.                                                                */
/******************************************************************************/


/*---Initialized-data---------------------------------------------------------*/
.section ".rodata"                    // Read only data section
.align 2   // ARM instructions needs proper data alignment otherwise they fault.
hello_msg: .short 14                  // The length of the string (16 bits). 
           .ascii "Hello, world!\n"   // We don't use null-terminated strings.
                           
/*---Code---------------------------------------------------------------------*/
.section ".text"
.global _start
_start:
                     /* Read this CPU core's ID */
mrs x1, MPIDR_EL1    // Read Multiprocessor Affinity Register.
and x1, x1, #3       // Mask to get just the CPU ore ID (0-3). 
cbz x1, core0        // If ID is 0, branch to core0.
b halt               // If not Core 0, put it to sleep.

core0: 
    ldr x1, =__stack_top   
    mov sp, x1             // We set our stack pointer to __stack_top address 
    mov x2, 5              // Counter = 5 (i.e. send the message five times)
main:
    ldr x20, =hello_msg    // Load the address of the message into x20
    bl uart_puts           // Send the message to UART 
    subs x2, x2, #1        // Decrease counter
    bne main               // Loop until length counter = 0
halt:        /* Infinite loop. */
    wfe      // Wait For Event: This is a low-power sleep/halt instruction.
    b halt   // It prevents us from going off in memory and executing junk.


/*---Uninitialized-data-------------------------------------------------------*/
.section ".bss"  // Allocate uninitialized space (in linker.ld) for the stack.  

