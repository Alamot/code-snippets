; Author: Alamot

BITS 64   ; We have entered the long mode! :)

;---Constants-------------------------------------------------------------------
VRAM equ KERNEL_VIRT_BASE + 0xB8000  

;---Code------------------------------------------------------------------------
Kernel_entrypoint:
;********************************************************************;
; Just some dummy code for now                                       ;
;********************************************************************;
    ; Set RDI to point to Video RAM (KERNEL_VIRT_BASE + 0xB8000)
    mov rdi, VRAM
 
    ; Print "Hello World!"
    mov rax, 0x1F6C1F6C1F651F48    
    mov [rdi], rax
    mov rax, 0x1F6F1F571F201F6F
    mov [rdi + 8], rax
    mov rax, 0x1F211F641F6C1F72
    mov [rdi + 16], rax
 
   .halt: hlt 
    jmp .halt ; Infinite loop.

