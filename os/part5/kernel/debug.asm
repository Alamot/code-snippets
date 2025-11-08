; Author: Alamot

BITS 64

;---Initialized data----------------------------------------------------------------
e820_header dw 35
db 'Number of E820 memory map entries: '
e820_mmap_headers dw 39
db 'Base address       Length             T'
highest_usable_address_header dw 24
db 'Highest usable address: '
frame_bitmap_size_header dw 27
db 'Frame bitmap size (bytes): '
number_of_frames_header dw 18
db 'Number of frames: '


Print_E280_memory_map:
;******************************************************************************;
; Print the E280 memory mapping entries                                        ;
;******************************************************************************;
;  ah: Color attributes                                                        ;
;  r8: x                                                                       ;
;  r9: y                                                                       ;
;******************************************************************************;
    push rsi
    push r8
    push r9
    push r10
    push r11    
    mov r11, r8        ; Store original x value       
    ; Print number of E820 entries
    mov rsi, e820_header
    call Print
    add r8w, [abs e820_header]
    mov r10, [abs e820_mmap_entries]
    call Print_int
    ; Print headers of E820 entries
    mov r8, r11        ; Restore original x value   
    add r9, 2
    mov rsi, e820_mmap_headers
    call Print
    ; Print E820 entries
    inc r9
    mov rcx, [abs e820_mmap_entries]        
    mov rsi, e820_mmap_buffer
    mmap_loop:
        ; Print E280 entry base address
        mov r8, r11    ; Restore original x value   
        mov r10, [rsi]
        call Print_hex    
        ; Print E280 entry length
        add r8, 19    
        mov r10, [rsi + 8]
        call Print_hex
        ; Print E280 entry type
        add r8, 19
        mov r10d, dword [rsi + 16]
        call Print_int
        inc r9   
        add rsi, 20
        loop mmap_loop
    pop r11        
    pop r10
    pop r9
    pop r8
    pop rsi
    ret
    
    
Print_PMA_info:    
;******************************************************************************;
; Print info about the Physical Memory Allocator                               ;
;------------------------------------------------------------------------------;
;  ah: Color attributes                                                        ;
;  r8: x                                                                       ;
;  r9: y                                                                       ;
;  rsi: bitmap address                                                         ;
;******************************************************************************;
    push rsi
    push r8
    push r9
    push r11    
    mov r11, r8    ; Store original x value    
    ; Print number of frames
    mov rsi, number_of_frames_header
    call Print
    add r8w, [abs number_of_frames_header]
    mov r10, [abs PMA_max_frames]
    call Print_int 
    ; Print frame bitmap size (in bytes)
    mov r8, r11    ; Restore original x value 
    inc r9         ; y += 1
    mov rsi, frame_bitmap_size_header
    call Print
    add r8w, [abs frame_bitmap_size_header]
    mov r10, [abs PMA_bitmap_size_bytes]
    call Print_int 
    ; Print highest usable address
    mov r8, r11    ; Restore original x value 
    inc r9         ; y += 1   
    mov rsi, highest_usable_address_header
    call Print
    mov r10, [abs PMA_highest_address]
    add r8w, [abs highest_usable_address_header]
    call Print_hex     
    pop r11
    pop r9
    pop r8
    pop rsi
    ret

    
Print_PMA_frame_bitmap:
;******************************************************************************;
; Print the frame bitmap of Physical Memory Allocator                          ;
;------------------------------------------------------------------------------;
;  ah: Color attributes                                                        ;
;  r8: x                                                                       ;
;  r9: y                                                                       ;
;  rsi: bitmap address                                                         ;
;******************************************************************************;
    push rax
    push rbx
    push rcx
    push rdx
    push rsi
    push r8
    push r9
    push r10
    push r11
    push r12
    push r13
    sub rsp, 16                          ; Allocate space for string buffer
    mov r11, rax                         ; Store color attributes
    mov r13, r8                          ; Store original x value
    mov rbx, rsi                         ; rbx = bitmap address
    mov r12, [abs PMA_bitmap_size_bytes] ; r12 = bitmap size in bytes (counter)
    mov rsi, rsp                         ; rsi = buffer start
    xor r10, r10                         ; r10 = 0 (KB per line indicator)    
.print_byte_loop:
    test r12, r12                        ; Did we reach the end of bitmap?
    jz .exit
    movzx rax, byte [rbx]                ; Current byte (rbx is incremented)
    inc rbx                              
    dec r12                              ; Decrease byte counter  
    push rsi                             ; Store rsi
    mov [rsi], word 8                    ; String length = 8
    add rsi, 9                           ; Point rsi to the end of the string
    mov rcx, 8                           ; Loop 8 bits
.store_bits:
    rol al, 1                            ; Rotate left (bit 7 goes to carry etc)
    mov byte [rsi], '_'                  ; Draw as FREE 
    jc .set_used                         ; Check if bit is set
    jmp .bit_done
.set_used:                               ; If yes, draw as USED
    mov byte [rsi], '#'                  ; Draw as USED
.bit_done:
    dec rsi                              ; Decrease string buffer index
    loop .store_bits
    pop rsi                              ; Restore rsi (string buffer address)
    mov rax, r11                         ; Restore color attributes
    call Print                           ; Print 8-char string
    ; Handle line wrap    
    add r8, 8                            ; x += 8
    cmp r8, 64                           ; Draw 64 frames per line
    jl .no_newline            
    ; Print KB indicator
    inc r8                               ; x += 1
    add r10, (64 * FRAME_SIZE / 1024)    ; r10 += 256 (KB per line indicator)
    Call Print_int
    add r8, 5                            ; x += 5
    ; Print "KB" unit
    push rsi                             
    mov rsi, KB_unit                     
    Call Print                           
    pop rsi       
    ; Set x, y coordinates for the next line
    mov r8, r13                          ; Restore original x value
    inc r9                               ; y += 1
    cmp r9, 25                           ; Don't past the 25 lines
    jg .exit
.no_newline:
    jmp .print_byte_loop
.exit:
    add rsp, 16                          ; Release space
    pop r13
    pop r12
    pop r11
    pop r10
    pop r9
    pop r8
    pop rsi
    pop rdx
    pop rcx
    pop rbx
    pop rax
    ret
