; INTERRUPT SERVICE ROUTINES

BITS 64 

;---Initialized data----------------------------------------------------------
systimer_ticks dq 0
tasktimer_ticks dq 0
keyboard_scancode dq 0
error_code_low dw 0
error_code_high dw 0

int_message dw 17
db 'Interrupt raised!'

division_by_zero_message dw 17
db 'Division by zero!'

invalid_opcode_message dw 15
db 'Invalid Opcode!'

gpf_message dw 25
db 'General Protection Fault!'

pf_message dw 11
db 'Page Fault!'

alignment_check_message dw 26
db 'Alignment Check Exception!'

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


ISR_Invalid_Opcode:
;***************************************************************************;
; Invalid Opcode handler                                                  ;
;***************************************************************************;
    cli
    push rax
    push r8
    push r9
    push rsi
    mov ah, (VGA_COLOR_RED << 4) | VGA_COLOR_LIGHT_BROWN
    mov r8, 1
    mov r9, 1
    mov rsi, invalid_opcode_message
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


ISR_Alignment_Check:
;***************************************************************************;
; Alignment Check Exception handler                                                  ;
;***************************************************************************;
    cli
    push rax
    push r8
    push r9
    push rsi
    mov ah, (VGA_COLOR_RED << 4) | VGA_COLOR_LIGHT_BROWN
    mov r8, 1
    mov r9, 1
    mov rsi, alignment_check_message
    Call Print
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
    mov al, PIC_EOI       ; Send EOI (End of Interrupt) command
    out PIC1_COMMAND, al  
    pop rax
    inc qword [systimer_ticks]
    inc qword [tasktimer_ticks]
    cmp qword [tasktimer_ticks], 1 ; Every how many ticks we want to switch tasks.
    jg .switch_task
    iretq

   .switch_task:
        ; set tasktimer_ticks to 0
        mov qword [tasktimer_ticks], 0
        ; In long mode, when an interrupt occurs, the processor pushes in the stack
        ; the interrupted program's stack pointer (SS:RSP), the RFLAGS, and the
        ; return pointer (CS:RIP). In order to switch task, we have to replace them.
        ; Therefore, we remove (pop) them from the stack.
        pop qword [return_address] ; RIP
        pop qword [code_segment]   ; CS
        pop qword [rflags]         ; RFLAGS
        pop qword [stack_pointer]  ; RSP
        pop qword [stack_segment]  ; SS
        ; We save the current task state in the active task slot.
        call Save_task_state
        ; We activate the next task slot
        inc qword [active_task_slot]
        ; We check if the current task was the last task.
        push rax
        mov rax, [num_tasks]
        cmp [active_task_slot], rax
        pop rax
        jnz .load
        ; If we reach the last task, switch to the first task
        mov qword [active_task_slot], 0
       .load:
        ; Load the next task state from the active task slot.
        call Load_task_state
        ; We now push back to the stack the values we have loaded for the next task.
        push qword [stack_segment]
        push qword [stack_pointer]
        push qword [rflags]
        push qword [code_segment]
        push qword [return_address] 
        ; The instruction IRETQ will load these values to the proper registers
        ; and we will switch to the next task.
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
