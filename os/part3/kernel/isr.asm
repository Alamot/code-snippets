; INTERRUPT SERVICE ROUTINES

BITS 64 

;---Initialized data----------------------------------------------------------
systimer_ticks dq 0
keyboard_scancode dq 0
error_code_low dw 0
error_code_high dw 0

int_message dw 17
db 'Interrupt raised!'

division_by_zero_message dw 17
db 'Division by zero!'

gpf_message dw 25
db 'General Protection Fault!'

pf_message dw 11
db 'Page Fault!'


;---Code------------------------------------------------------------------------
ISR_dummy:
;***************************************************************************;
; Just a dummy generic handler. It prints the message "Interrupt raised!".  ;
;***************************************************************************;
    cli
    push rax
    push r8
    push r9
    push rsi
    mov ah, (VGA_COLOR_RED << 4) | VGA_COLOR_LIGHT_BROWN
    mov r8, 1
    mov r9, 1
    mov rsi, int_message
    Call Print
    pop rsi
    pop r9
    pop r8
    pop rax
    .halt: hlt
    jmp .halt ; Infinite loop
    iretq
    

ISR_Division_by_Zero:
;***************************************************************************;
; Divizion by zero handler                                                  ;
;***************************************************************************;
    cli
    push rax
    push r8
    push r9
    push rsi
    mov ah, (VGA_COLOR_RED << 4) | VGA_COLOR_LIGHT_BROWN
    mov r8, 1
    mov r9, 1
    mov rsi, division_by_zero_message
    Call Print
    pop rsi
    pop r9
    pop r8
    pop rax
    .halt: hlt
    jmp .halt ; Infinite loop
    iretq


ISR_GPF:
;***************************************************************************;
; General Protection Fault handler                                                  ;
;***************************************************************************;
    cli
    push rax
    push r8
    push r9
    push rsi
    mov ah, (VGA_COLOR_RED << 4) | VGA_COLOR_LIGHT_BROWN
    mov r8, 1
    mov r9, 1
    mov rsi, gpf_message
    Call Print
    pop rsi
    pop r9
    pop r8
    pop rax
    .halt: hlt
    jmp .halt ; Infinite loop
    iretq


ISR_Page_Fault:
;***************************************************************************;
; Page Fault handler                                                  ;
;***************************************************************************;
    cli
    pop word [error_code_high]
    pop word [error_code_low]
    push rax
    push r8
    push r9
    push rsi
    mov ah, (VGA_COLOR_RED << 4) | VGA_COLOR_LIGHT_BROWN
    mov r8, 1
    mov r9, 1
    mov rsi, pf_message
    call Print
    pop rsi
    pop r9
    pop r8
    pop rax
    .halt: hlt 
    jmp .halt ; Infinite loop
    iretq


ISR_systimer:
;*****************************************************************************;
; System Timer Interrupt Service Routine (IRQ0 mapped to INT 0x20)            ;
;*****************************************************************************;
    push rax
    inc qword [systimer_ticks]
    mov al, PIC_EOI      ; Send EOI (End of Interrupt) command
    out PIC1_COMMAND, al
    pop rax
    iretq


ISR_keyboard:
;*****************************************************************************;
; Keyboard Controller Interrupt Service Routine (IRQ1 mapped to INT 0x21)     ;
;*****************************************************************************;
    push rax
    xor rax, rax         
    in al, 0x60          ; MUST read byte from keyboard (else no more interrupts).
    mov [keyboard_scancode], al
    mov al, PIC_EOI      ; Send EOI (End of Interrupt) command
    out PIC1_COMMAND, al
    pop rax
    iretq
