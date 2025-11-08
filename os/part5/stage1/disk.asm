; Author: Alamot

BITS 16

;---Initialized data------------------------------------------------------------

disk db 0x80

disk_error_message dw 11
db 'Disk error!'


DAP:
;*******************************************************************************;
; Disk Address Packet                                                           ;
;-------------------------------------------------------------------------------;
; Offset  Size   Description                                                    ;
;   0       1    size of packet (16 bytes)                                      ;
;   1       1    always 0                                                       ;
;   2       2    number of sectors to load (max = 127 on some BIOS)             ;
;   4       2    16-bit offset of target buffer                                 ;
;   4       2    16-bit segment of target buffer                                ;
;   8       4    lower 32 bits of 48-bit starting LBA                           ;
;  12       4    upper 32 bits of 48-bit starting LBA                           ;
;*******************************************************************************;
              db 0x10 ; size of packet = 16 bytes
              db 0    ; always 0
.num_sectors: dw 127  ; number of sectors to load (max = 127 on some BIOS)
.buf_offset:  dw 0x0  ; 16-bit offset of target buffer
.buf_segment: dw 0x0  ; 16-bit segment of target buffer
.LBA_lower:   dd 0x0  ; lower 32 bits of 48-bit starting LBA
.LBA_upper:   dd 0x0  ; upper 32 bits of 48-bit starting LBA



;---Code------------------------------------------------------------------------

Real_mode_read_disk:
;**********************************************************;
; Load disk sectors to memory (int 13h, function code 42h) ;
;----------------------------------------------------------;
; ax: start sector                                         ;
; cx: number of sectors (512 bytes) to read                ;
; bx: offset of buffer                                     ;
; dx: segment of buffer                                    ;
;**********************************************************;
    .start:
        cmp cx, 127 ; (max sectors to read in one call = 127)
        jbe .good_size
         pusha
        mov cx, 127
        call Real_mode_read_disk
        popa
        add eax, 127
        add dx, 127 * 512 / 16
        sub cx, 127
        jmp .start

    .good_size:
        mov [DAP.LBA_lower], ax
        mov [DAP.num_sectors], cx
        mov [DAP.buf_segment], dx
        mov [DAP.buf_offset], bx
        mov dl, [disk]
        mov si, DAP
        mov ah, 0x42
        int 0x13
        jc .print_error
        ret
    .print_error:
        mov si, disk_error_message
        call Real_mode_println
    .halt: hlt
     jmp .halt; Infinite loop. We cannot recover from disk error.
