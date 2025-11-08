; Author: Alamot

BITS 64

;---Initialized data----------------------------------------------------------------
KB_unit dw 2
db 'KB'

;---Constants-----------------------------------------------------------------------
VRAM equ 0xB8000
VGA_WIDTH equ 80
VGA_HEIGHT equ 25
; Colors
VGA_COLOR_BLACK equ 0
VGA_COLOR_BLUE equ 1
VGA_COLOR_GREEN equ 2
VGA_COLOR_CYAN equ 3
VGA_COLOR_RED equ 4
VGA_COLOR_MAGENTA equ 5
VGA_COLOR_BROWN equ 6
VGA_COLOR_LIGHT_GREY equ 7
VGA_COLOR_DARK_GREY equ 8
VGA_COLOR_LIGHT_BLUE equ 9
VGA_COLOR_LIGHT_GREEN equ 10
VGA_COLOR_LIGHT_CYAN equ 11
VGA_COLOR_LIGHT_RED equ 12
VGA_COLOR_LIGHT_MAGENTA equ 13
VGA_COLOR_LIGHT_BROWN equ 14
VGA_COLOR_WHITE equ 15

;---Code---------------------------------------------------------------------------
Fill_screen:
;*********************************************************************************;
; Fill screen                                                                     ;
;---------------------------------------------------------------------------------;
; rax (XY__XY__XY__XY__): X -> Background color, Y -> Character color             ;
; rax (__ZZ__ZZ__ZZ__ZZ): ASCII code(s) of character(s) to use to fill the screen ;
;*********************************************************************************;
    push rax
    push rcx
    push rdi
    mov rdi, VRAM
    mov rcx, 500 ; 80*25 / 4 = 500 (we set 4 characters each time).
    rep stosq    ; Clear the entire screen.
    pop rdi
    pop rcx
    pop rax
    ret


Print:
;**********************************************************************************;
; Prints a string                                                                  ;
;----------------------------------------------------------------------------------;
;  ah: Color attributes                                                            ;
;  r8: x                                                                           ;
;  r9: y                                                                           ;
; rsi: pointer to string (first 16 bits = the number of characters in the string.) ;
;**********************************************************************************;
    push rax
    push rcx
    push rdx
    push rsi
    push rdi
    push r8
    push r9
    ; Map x, y coordinates to VRAM
    dec r8
    add r8, r8
    dec r9
    mov rdi, VRAM
    push rax
    mov rax, VGA_WIDTH*2
    mul r9
    add r8, rax
    pop rax
    movzx rcx, word [rsi]    ; rcx = string length (zero-extend first 16 bits) 
    add rsi, 2
   .string_loop:             ; Print all the characters in the string.
        lodsb                ; al = [rsi], rsi++
        mov [rdi+r8], ax     ; Write attributes (ah) + character (al) to VRAM.
        add rdi, 2           ; Move to next word in VRAM
    loop .string_loop        ; rcx--, jnz
    pop r9
    pop r8
    pop rdi
    pop rsi
    pop rdx
    pop rcx
    pop rax
    ret


Print_hex:
;******************************************************************************;
; Prints a 16-digit hexadecimal value                                          ;
;------------------------------------------------------------------------------;
;  ah: Color attributes                                                        ;
;  r8: x                                                                       ;
;  r9: y                                                                       ;
; r10: value to be printed                                                     ;
;******************************************************************************;
    push rcx
    push rsi
    push r10
    sub rsp, 24              ; Make space for the string + alignment
    mov rsi, rsp
    push rsi                 ; Store rsi (string address)
    mov [rsi], word 18       ; String length = 18
    mov [rsi+2], word "0x"   ; Add hex prefix "0x"
    add rsi, 19              ; Point rsi to the end of the string
    mov ecx, 16              ; Loop 16 times (one for each digit)
   .digit:
        push r10             ; Store r10
        and r10, 0Fh         ; Isolate digit
        add r10b,'0'         ; We add '0' to convert a numerical digit to ASCII
        cmp r10b,'9'         ; Is hex digit ("ABCDEF") ?
        jbe .nohex
        add r10b, 7          ; We add 7 more to convert a hex digit to ASCII
       .nohex:
        mov [rsi], byte r10b ; Store result
        dec rsi              ; Next position
        pop r10              ; Restore r10
        shr r10, 4           ; Right shift by 4
    loop .digit
    pop rsi                  ; Restore rsi (string address)
    call Print               ; Print string
    add rsp, 24              ; Release local space
    pop r10
    pop rsi
    pop rcx
    ret


Print_int:
;******************************************************************************;
; Prints an integer value                                                      ;
;------------------------------------------------------------------------------;
;  ah: Color attributes                                                        ;
;  r8: x                                                                       ;
;  r9: y                                                                       ;
; r10: value to be printed                                                     ;
;******************************************************************************;
    push rax
    push rbx
    push rcx
    push rdx
    push rsi
    push r10
    push r11
    sub rsp, 24         ; Make space for the string length + alignment
    mov rsi, rsp
    add rsi, 20         ; Point rsi to the end of the string
    xor rcx, rcx        ; rcx = 0
    push rax            ; Store color attributes
.digit_loop:
    ; Fast divmod by 10 using multiplication
    mov rax, r10
    mov r11, 0x199999999999999A   ; 2^64 / 10 (rounded up)
    mul r11                       ; Result in rdx
    mov rbx, rdx                  ; Quotient
    ; Calculate remainder (= r10 - quotient * 10)
    lea rdx, [rbx + rbx * 4]      
    shl rdx, 1                    
    sub r10, rdx                  
    add r10, '0'                  ; We add '0' to convert a digit to ASCII
    mov [rsi], byte r10b          ; Write character to string
    dec rsi                       
    inc rcx
    mov r10, rbx                  ; Next quotient
    test rbx, rbx                 ; If not zero, loop
    jnz .digit_loop
    dec rsi 
    mov [rsi], word cx            ; Write string length
    pop rax                       ; Restore color attributes
    call Print                    ; Print it
    add rsp, 24
    pop r11
    pop r10
    pop rsi
    pop rdx
    pop rcx
    pop rbx
    pop rax
    ret
