BITS 64

;---Initialized data----------------------------------------------------------------
VRAM dq 0xB8000

;---Constants-----------------------------------------------------------------------
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
    mov rdi, [abs VRAM]
    mov rcx, 500 ; 80*25 / 4 = 500 (we set 4 characters each time).
    rep stosq    ; Clear the entire screen.
    ret


Print:
;**********************************************************************************;
; Prints a string                                                                  ;
;----------------------------------------------------------------------------------;
; rsi: pointer to string (first 16 bits = the number of characters in the string.) ;
;  ah: Color attributes                                                            ;
;  r8: x                                                                           ;
;  r9: y                                                                           ;
;**********************************************************************************;
    push rax
    push rcx
    push rdx
    push rsi
    push rdi
    push r8
    push r9
    dec r8
    add r8, r8
    dec r9
    mov rdi, [abs VRAM]            

    push rax
    mov rax, VGA_WIDTH*2
    mul r9
    add r8, rax
    pop rax
    mov cx, word [rsi] ; first 16 bits = the number of characters in the string
    inc rsi

   .string_loop: ; print all the characters in the string
        lodsb
        mov al, byte [rsi]
        mov [rdi+r8], ax
        add rdi, 2    
    loop .string_loop
    pop r9
    pop r8
    pop rdi
    pop rsi
    pop rdx
    pop rcx
    pop rax
    ret


Print_hex:
;**********************************************************************************;
; Prints a 16-digit hexadecimal value                                              ;
;----------------------------------------------------------------------------------;
; r10: value to be printed                                                         ;
;  ah: Color attributes                                                            ;
;**********************************************************************************;
    push rcx
    push rsi
    push r10    
    sub rsp, 20         ; make space for the string length (2 bytes) and 18 characters
    mov rsi, rsp
    push rsi            ; store rsi (string address)
    mov [rsi], word 18  ; string length = 17
    mov [rsi+2], word "0x"  
    add rsi, 19         ; point rsi to the end of the string
    mov ecx, 16         ; loop 16 times (one for each digit)
   .digit:
        push r10             ; store rax
        and r10, 0Fh         ; isolate digit
        add r10b,'0'         ; convert to ascii
        cmp r10b,'9'         ; is hex?
        jbe .nohex          
        add r10b, 7          ; hex
       .nohex:
        mov [rsi], byte r10b ; store result
        dec rsi              ; next position
        pop r10              ; restore rax
        shr r10, 4           ; right shift by 4 
    loop .digit         
    pop rsi       ; restore rsi (string address)
    call Print
    add rsp, 20
    pop r10
    pop rsi
    pop rcx
    ret
