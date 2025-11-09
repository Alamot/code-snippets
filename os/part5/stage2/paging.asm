; Author: Alamot

BITS 16

;---Constants-------------------------------------------------------------------
PAGE_PRESENT equ (1 << 0)   ; Bit 0 => Page present
PAGE_WRITE   equ (1 << 1)   ; Bit 1 => Page writable
PAGE_PS      equ (1 << 7)   ; Bit 7 => 2MB page size, ignore PT
PAGING_DATA  equ 0xF000     ; Address to store the paging tables
; RPL (Requestor Privilege Level - Bits 1-0): 0 is highest, 3 is lowest 
; TI (Table Indicator - Bit 2): 0 => GDT, 1 => LDT
; Index (Bits 15-3): The index of the segment descriptor within the GDT.                   
; Segment Selector = (Index * 8) + (TI * 4) + RPL = (1 * 8) + (0 * 4) + 0 = 8                  
CODE_SEG equ 8

;---Initialized data------------------------------------------------------------

;****************************************************************************************;
; Global Descriptor Table (GDT)                                                          ;
;****************************************************************************************;
; The Global Descriptor Table (GDT) is a data structure used by x86-family processors    ;
; (starting with the 80286) in order to define the characteristics of the various memory ;
; areas (segments) used during program execution, including the base address, the size,  ;
; and access privileges like executability and writability.                              ;
;****************************************************************************************;
GDT:
  .Null:
    dq 0x0000000000000000  ; Null Descriptor (should be present).
  .Code:
    dq 0x00209A0000000000  ; 64-bit code descriptor (exec/read).
    dq 0x0000920000000000  ; 64-bit data descriptor (read/write).
  ALIGN 4
    dw 0                   ; Padding (to make the "address of the GDT" field aligned on a 4-byte boundary).
  .Pointer:
    dw $ - GDT - 1         ; 16-bit Size (Limit) of GDT.
    dd GDT                 ; 32-bit Base Address of GDT. (CPU will zero extend to 64-bit)


;---Code------------------------------------------------------------------------
Prepare_paging:
;******************************************************************************;
; Prepare paging                                                               ;
;------------------------------------------------------------------------------;
; ES:EDI Should point to a valid 4096-aligned 16KiB buffer.                    ;
; SS:ESP Should point to memory that can be used as a small stack.             ;
;******************************************************************************;
    mov edi, PAGING_DATA     ; Point to 16KiB buffer for the paging structures.
    ; Zero out the entire 16KiB buffer (PML4, PDPT, PD, unused PT)
    push di                  ; Store di (rep stosd alters di).
    mov ecx, 0x1000          ; Count should be 16384 / 4 = 4096 dwords
    xor eax, eax
    cld
    rep stosd
    pop di                   ; Restore di
    ; Build the PML4 (Page Map Level 4): PML4[0] -> PDPT
    lea eax, [es:di + 0x1000]            ; eax = address of the PDPT
    or eax, PAGE_PRESENT | PAGE_WRITE    ; Set the flags (present and writable)
    mov [es:di], eax                     ; PML4E[0] = eax
    ; Build the PDPT (Page Directory Pointer Table): PDPT[0] -> PD
    lea eax, [es:di + 0x2000]           ; eax = address of the PD
    or  eax, PAGE_PRESENT | PAGE_WRITE  ; Set the flags (present and writable)
    mov [es:di + 0x1000], eax           ; PDPT[0] = eax  
    ; Fill the PD (Page Directory) with 512 entries (each maps a 2 MiB page)
    lea di, [di + 0x2000]       ; DI now points to start of Page Directory
    xor ebx, ebx                ; EBX = page index (0 to 511)
    mov ecx, 512                ; Number of 2 MiB pages to map
.MapLoop:
    mov eax, ebx                ; Compute physical address: ebx * 0x200000          
    shl eax, 21                 ; 2^21 = 0x200000 = 2 MiB    
    ; Set flags: Present, Writable, PS=1 (2 MiB page)
    or eax, PAGE_PRESENT | PAGE_WRITE | PAGE_PS 
    mov [es:di], eax            ; Store low 32 bits (each entry is 8 bytes)
    mov [es:di + 4], dword 0    ; Store high 32 bits (0 => identity mapping)
    add di, 8                   ; Advance to next entry 
    inc ebx                     ; Increment index
    loop .MapLoop
    ret
