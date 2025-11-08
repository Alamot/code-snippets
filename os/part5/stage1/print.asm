; Author: Alamot

BITS 16

;---Initialized data------------------------------------------------------------

newline dw 2
db 13,10 ; \r\n

stage1_message dw 17
db 'Stage 1 finished.'

;---Code------------------------------------------------------------------------

Real_mode_print:
;*********************************************************************************;
; Prints a string (in real mode)                                                  ;
;---------------------------------------------------------------------------------;
; si: pointer to string (first 16 bits = the number of characters in the string.) ;  
;*********************************************************************************;
    push ax
    push cx
    push si
    mov cx, word [si] ; first 16 bits = the number of characters in the string
    add si, 2
    .string_loop:     ; print all the characters in the string
        lodsb
        mov ah, 0eh
        int 10h
    loop .string_loop, cx
    pop si
    pop cx
    pop ax
    ret


Real_mode_println:
;***********************************************************;
; Prints a string (in real mode) and a newline (\r\n)       ;
;-----------------------------------------------------------;
; si: pointer to string                                     ;
; (first 16 bits = the number of characters in the string.) ;  
;***********************************************************;
    push si
    call Real_mode_print
    mov si, newline
    call Real_mode_print
    pop si
    ret
