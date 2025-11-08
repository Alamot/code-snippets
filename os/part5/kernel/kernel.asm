; Author: Alamot

BITS 64   ; We have entered the long mode! :)

;---Constants-------------------------------------------------------------------
DATA_SEG equ 0x0010

;---Initialized data------------------------------------------------------------
hello_world_message dw 12
db 'Hello World!'
ticks_message dw 14
db 'Timer ticks:  '
keycode_message dw 14
db 'Keyboard key: '
task1_header dw 6
db "Task 1"
task2_header dw 6
db "Task 2"
task3_header dw 6
db "Task 3"

;---Include---------------------------------------------------------------------
%include "kernel/video.asm"
%include "kernel/idt.asm"
%include "kernel/isr.asm"
%include "kernel/pma.asm"
%include "kernel/tasking.asm"
%include "kernel/debug.asm"

;---Code------------------------------------------------------------------------
Kernel:
    lidt [abs IDTR] ; Load our IDTR

    mov al, 0x80       ; OCW1: Unmask all interrupts at master PIC.
    out PIC1_DATA, al
    mov al, 0x80       ; OCW1: Unmask all interrupts at master PIC.
    out PIC2_DATA, al

    ; Set all segments registers to DATA_SEG.
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
    
    ; Print "Hello World!" at the upper right corner.
    mov ah, (VGA_COLOR_BLACK << 4) | VGA_COLOR_LIGHT_GREEN
    mov r8, 69    ; x = 69
    mov r9, 1     ; y = 1
    mov rsi, hello_world_message
    call Print

    ; Print the E280 memory mapping entries.
    mov ah, (VGA_COLOR_BLUE << 4) | VGA_COLOR_WHITE 
    mov r8, 1     ; x = 1
    mov r9, 1     ; y = 1
    call Print_E280_memory_map

    ; Initialize the Physical Memory Allocator (PMA).
    call PMA_init
    ; Print PMA info
    mov ah, (VGA_COLOR_BLACK << 4) | VGA_COLOR_WHITE
    mov r8, 1     ; x = 1
    mov r9, 11    ; y = 11
    call Print_PMA_info

    ; Initialize general stack allocation to the current rsp value.
    mov [abs stack_allocation], rsp
    
    ; Create three tasks.
    mov rsi, Task1
    call Create_task
    mov rsi, Task2
    call Create_task
    mov rsi, Task3
    call Create_task
 
    ; Set active the first task slot
    mov qword [abs active_task_slot], 0

    ; Task 1: We print system timer ticks, keyboard scan code and frame bitmap.
    Task1:
        ; Print task message
        mov ah, (VGA_COLOR_DARK_GREY << 4) | VGA_COLOR_WHITE
        mov r8, 49    ; x = 49
        mov r9, 2     ; y = 2
        mov rsi, task1_header
        Call Print        
        ; Print timer ticks message.
        inc r9
        mov rsi, ticks_message
        Call Print    
        ; Print keyboard key message.
        inc r9
        mov rsi, keycode_message
        Call Print                      
    .loop:       
        mov ah, (VGA_COLOR_DARK_GREY << 4) | VGA_COLOR_WHITE     
        mov r8, 63    ; x = 63
        mov r9, 3     ; y = 3
        ; Print system timer ticks.
        mov r10, [abs systimer_ticks]
        call Print_hex          
        inc r9
        ; Print keyboard scan code.        
        mov r10, [abs keyboard_scancode]
        call Print_hex
        ; Print the frame bitamp of Physical Memory Allocator (PMA).
        mov ah, (VGA_COLOR_BLACK << 4) | VGA_COLOR_WHITE
        mov r8, 4     ; x = 4
        mov r9, 15    ; y = 15
        mov rsi, BITMAP_ADDR
        call Print_PMA_frame_bitmap    
    jmp Task1.loop
    
    ; Task 2: We set r10 to 0 and we increase it by one in a loop.
    Task2:
        ; Print Task 2 header
        mov ah, (VGA_COLOR_BROWN << 4) | VGA_COLOR_WHITE 
        mov r8, 49    ; x = 40
        mov r9, 6     ; y = 6
        mov rsi, task2_header
        Call Print
        mov r8, 49    ; x = 49
        mov r9, 7     ; y = 7
        mov r10, 0
       .loop:
            ; Allocate a PMA frame
            push rax
            Call PMA_alloc_frame
            mov rdi, rax ; rdi = rax = address of allocated frame
            pop rax
            ; Increase and print number of ticks
            inc r10            
            Call Print_hex
            ; Release the PMA frame
            call PMA_free_frame
        jmp Task2.loop

    ; Task 3: We set r10 to 0xFFFFFFFFFFFFFFFF and we decrease it by one in a loop.
    Task3: 
        ; Print Task 3 header
        mov ah, (VGA_COLOR_MAGENTA << 4) | VGA_COLOR_WHITE 
        mov r8, 49    ; x = 49
        mov r9, 9     ; y = 9
        mov rsi, task3_header
        Call Print    
        mov r8, 49    ; x = 40
        mov r9, 10    ; y = 10
        mov r10, 0xFFFFFFFFFFFFFFFF
       .loop:
            ; Allocate a PMA frame
            push rax
            Call PMA_alloc_frame
            mov rdi, rax ; rdi = rax = address of allocated frame
            pop rax
            ; Decrease and print number of ticks
            dec r10
            Call Print_hex            
            ; Release the PMA frame
            call PMA_free_frame
        jmp Task3.loop
