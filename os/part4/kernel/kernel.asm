BITS 64  ; We have entered the long mode! :)

;---Define----------------------------------------------------------------------
%define DATA_SEG   0x0010

;---Initialized data------------------------------------------------------------
hello_world_message dw 12
db 'Hello World!'

ticks_message dw 20
db 'System timer ticks: '

scancode_message dw 20
db 'Keyboard scan code: '

task1_message dw 6
db "Task 1"

task2_message dw 6
db "Task 2"

task3_message dw 6
db "Task 3"

;---Include---------------------------------------------------------------------
%include "kernel/video.asm"
%include "kernel/idt.asm"
%include "kernel/isr.asm"
%include "kernel/tasking.asm"

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

    ; Initialize general stack allocation to the current rsp value
    mov [stack_allocation], rsp

    ; Create three tasks
    mov rsi, Task1
    call Create_task
    mov rsi, Task2
    call Create_task
    mov rsi, Task3
    call Create_task
 
    ; Set active the first task slot
    mov qword [active_task_slot], 0

    ; Task 1: We print system timer ticks and keyboard scan code
    Task1:
        mov ah, (VGA_COLOR_DARK_GREY << 4) | VGA_COLOR_WHITE
        mov r8, 1
        mov r9, 2
        mov rsi, task1_message
        Call Print
        mov r8, 1
        mov r9, 3
        mov rsi, ticks_message
        Call Print   
        mov r8, 1
        mov r9, 4
        mov rsi, scancode_message
        Call Print  
       .loop:
        ; Print system timer ticks.
        mov r8, 21
        mov r9, 3
        mov r10, [systimer_ticks]
        call Print_hex
        ; Print keyboard scan code.
        mov r8, 21
        mov r9, 4
        mov r10, [keyboard_scancode]
        call Print_hex
    jmp Task1.loop
    
    ; Task 2: We set r10 to 0x0 and we increase it by one in a loop
    Task2:
        mov ah, (VGA_COLOR_GREEN << 4) | VGA_COLOR_WHITE 
        mov r8, 1
        mov r9, 6
        mov rsi, task2_message
        Call Print
        mov r8, 1
        mov r9, 7
        mov r10, 0
       .loop:
            inc r10
            ; Print number of ticks
            Call Print_hex
        jmp Task2.loop

    ; Task 3: We set r10 to  0xFFFFFFFFFFFFFFFF and we decrease it by one in a loop
    Task3: 
        mov ah, (VGA_COLOR_MAGENTA << 4) | VGA_COLOR_WHITE 
        mov r8, 1
        mov r9, 9
        mov rsi, task3_message
        Call Print
        mov r8, 1
        mov r9, 10
        mov r10, 0xFFFFFFFFFFFFFFFF
       .loop:   
            dec r10
            ; Print number of ticks
            Call Print_hex
        jmp Task3.loop
