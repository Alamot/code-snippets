BITS 64  ; We have entered the long mode! :)

;---Define----------------------------------------------------------------------
%define DATA_SEG   0x0010

;---Initialized data------------------------------------------------------------
hello_world_message dw 12
db 'Hello World!'

ticks_message dw 19
db 'System timer ticks:'

scancode_message dw 19
db 'Keyboard scan code:'

;---Include---------------------------------------------------------------------
%include "kernel/idt.asm"
%include "kernel/isr.asm"
%include "kernel/video.asm"

;---Code------------------------------------------------------------------------
Kernel:
    lidt [IDTR] ; Load our IDTR

    mov al, 0x80       ; OCW1: Unmask all interrupts at master PIC
    out PIC1_DATA, al
    mov al, 0x80       ; OCW1: Unmask all interrupts at master PIC
    out PIC2_DATA, al

    ; Set all segments registers to DATA_SEG
    mov ax, DATA_SEG
    mov ds, ax
    mov es, ax
    mov fs, ax
    mov gs, ax
    mov ss, ax
    
    ; Clear the screen.
    mov rax, 0x0020002000200020 ; Set background color to black (0) and
                                ; character to blank space (20).
    call Fill_screen            

    ; Print "Hello World!" at the upper right corner
    mov ah, 0x1E
    mov r8, 69
    mov r9, 1
    mov rsi, hello_world_message
    call Print

    ; Uncomment the following lines if you want to test the "Division by zero" exception.
    ; mov eax, 1
    ; mov ecx, 0
    ; div ecx   
    
   .loop:
        ; Print system timer ticks.
        mov ah, VGA_COLOR_LIGHT_GREEN     
        mov r8, 1
        mov r9, 2
        mov rsi, ticks_message
        Call Print       
        mov r8, 21
        mov r9, 2
        mov r10, [systimer_ticks]
        call Print_hex
        ; Print keyboard scan code.
        mov ah, VGA_COLOR_LIGHT_CYAN    
        mov r8, 1
        mov r9, 4
        mov rsi, scancode_message
        Call Print  
        mov r8, 21
        mov r9, 4
        mov r10, [keyboard_scancode]
        call Print_hex
        jmp .loop ; Infinite loop.
