; Author: Alamot

BITS 16

;---Initialized data------------------------------------------------------------
e820_mmap_entries db 0
e820_mmap_buffer: times 128*20 db 0   ; Allocate space for 128 E820 map entries.

;---Code------------------------------------------------------------------------
Get_E820_map:
;******************************************************************************;
; Prepare paging                                                               ;
;------------------------------------------------------------------------------;
; Rerurns:                                                                     ;
;   bx = number of entries (Each entry is 20 bytes)                            ;
;   es:di = start of array (you decide where)                                  ;
;******************************************************************************;
    pusha                      ; Store registers
    push es
    xor ebx, ebx               ; ebx = 0 (continuation value / entry counter)
    mov di, e820_mmap_buffer   ; es:di = destination buffer
    xor ax, ax
    mov es, ax                 ; es = 0 (buffer below 1MB).
.next_entry:
    mov eax, 0xE820            ; eax = 0xE820
    mov edx, 0x534D4150        ; edx = 'SMAP'
    mov ecx, 20                ; ecx = size of buffer (at least 20)
    mov [abs e820_mmap_entries], ebx   ; Store number of entries
    int 0x15                   ; Call BIOS interrupt 15
    jc .done                   ; CF=1 => Unsupported function (or error or end)
    cmp eax, 0x534D4150        ; On success, eax must have been reset to "SMAP"
    jne .done             
    test ebx, ebx              ; ebx = 0 => List is only 1 entry (worthless)
    je .done         
    add di, 20                 ; Next buffer slot
    cmp ebx, 128               ; Limit to 128 entries
    jae .done              
    jmp .next_entry
.done:     
    pop es 
    popa                       ; Restore registers
    ret
