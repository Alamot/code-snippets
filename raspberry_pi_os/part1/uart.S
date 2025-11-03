/*---Constants----------------------------------------------------------------*/

// Raspberry Pi 3B+
.equ PERIPH_BASE, 0x3F000000      /*  <--- Uncomment this for Pi 3  */

// Raspberry Pi 4B
//.equ PERIPH_BASE, 0xFE000000    /*  <--- Uncomment this for Pi 4  */

.equ UART0_BASE, (PERIPH_BASE + 0x201000)
.equ UART0_DR, (UART0_BASE + 0x00)
.equ UART0_FR, (UART0_BASE + 0x18)
.equ TXFF_BIT, (1 << 5)


/*---Code---------------------------------------------------------------------*/
.section ".text"
.global uart_puts
uart_puts:
/******************************************************************************/
/* Sends a string to UART (PL011).                                            */
/******************************************************************************/
/* x20: The address of the string                                             */
/******************************************************************************/
    stp lr, xzr, [sp, #-16]!   // Store Link Register (has the return address)
    stp x21, x22, [sp, #-16]!  // Store registers that will be used
    ldrh w21, [x20], #2        // Load length into w21 (needs 2-byte alignment!)    
 1: ldrb w22, [x20], #1        // Load a byte into w22 (then increase x20 by 1)
    bl uart_putc               // Call uart_putc (Link Register will be written)
    subs w21, w21, #1          // Decrease string length counter
    bne 1b                     // Loop until string length counter = 0
    ldp x21, x22, [sp], #16    // Restore used registers
    ldp lr, xzr, [sp], #16     // Restore Link Register (has the return address)
    ret


.global uart_putc
uart_putc:
/******************************************************************************/
/* Waits for UART (PL011) to be ready, then writes one character.             */
/******************************************************************************/
/* w22: The character (byte) to print.                                        */
/******************************************************************************/
    stp x23, x24, [sp, #-16]!   // Store registers that will be used
    ldr x23, =UART0_FR    // Load UART Flag Register address into register x23. 
 1: ldr w24, [x23]        // Read Flag Register value into register w24.
    tst w24, #TXFF_BIT    // Test if "Transmit FIFO Full" bit is set.
    bne 1b                // If bit is set (UART is not ready), loop.
    ldr x23, =UART0_DR    // Load UART Data Register address into register x23.
    strb w22, [x23]       // Send our character byte to the Data Register
    ldp x23, x24, [sp], #16     // Restore used registers
    ret
