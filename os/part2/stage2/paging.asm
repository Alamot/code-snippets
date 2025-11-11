; Author: Alamot

BITS 16

;---Constants-------------------------------------------------------------------
; Paging flag bits
PAGE_PRESENT equ (1 << 0)               ; Bit 0 => Page present
PAGE_WRITE   equ (1 << 1)               ; Bit 1 => Page writable
PAGE_HUGE_PS equ (1 << 7)               ; Bit 7 => 2MB page size, ignore PT

; Addresses to store the paging structures
PML4         equ 0xB000
PDPT_LOW     equ (PML4 + 0x1000)
PD_LOW       equ (PML4 + 0x2000)
PDPT_HIGH    equ (PML4 + 0x3000)
PD_HIGH      equ (PML4 + 0x4000)

; Kernel virtual address
KERNEL_VIRT_BASE equ 0xFFFFFFFF80000000 ; High-half base (48-bit address)

; Extract indices from KERNEL_VIRT_BASE for page table structure
PML4_INDEX   equ ((KERNEL_VIRT_BASE >> 39) & 0x1FF)  ; Bits 47-39
PDPT_INDEX   equ ((KERNEL_VIRT_BASE >> 30) & 0x1FF)  ; Bits 38-30
PD_INDEX     equ ((KERNEL_VIRT_BASE >> 21) & 0x1FF)  ; Bits 29-21
PT_INDEX     equ ((KERNEL_VIRT_BASE >> 12) & 0x1FF)  ; Bits 20-12

; Segment Selector = (Index * 8) + (TI * 4) + RPL = (1 * 8) + (0 * 4) + 0 = 8   
; RPL (Requestor Privilege Level - Bits 1-0): 0 is highest, 3 is lowest 
; TI (Table Indicator - Bit 2): 0 => GDT, 1 => LDT
; Index (Bits 15-3): The index of the segment descriptor within the GDT.                   
CODE_SEL equ 8
DATA_SEL equ 16


;---Initialized data------------------------------------------------------------

;******************************************************************************;
; Global Descriptor Table (GDT)                                                ;
;******************************************************************************;
; The Global Descriptor Table (GDT) is a data structure used by x86-family     ;
; processors (starting with the 80286) in order to define the characteristics  ;
; of the various memory areas (segments) used during program execution,        ;
; including the base address, the size, and access privileges like             ;
; executability and writability.                                               ;
;******************************************************************************;
GDT:
  .Null:
    dq 0x0000000000000000  ; Null Descriptor (should be present).
  .Code:
    dq 0x00209A0000000000  ; 64-bit code descriptor (exec/read).
    dq 0x0000920000000000  ; 64-bit data descriptor (read/write).
  ALIGN 4                  ; Align the pointer field on a 4-byte boundary.
    dw 0                   ; Padding.
  GDTR:
  .Length dw $ - GDT - 1   ; 16-bit Size (Limit) of GDT.
  .Base   dd GDT           ; 32-bit Base Address of GDT 
                           ; (CPU will zero extend to 64-bit)

;---Code------------------------------------------------------------------------
Prepare_paging:
;******************************************************************************;
; Prepare paging                                                               ;
;------------------------------------------------------------------------------;
; ES:EDI Should point to a valid 4096-aligned 16KiB buffer.                    ;
; SS:ESP Should point to memory that can be used as a small stack.             ;
;******************************************************************************;
  
    ; Zero out the entire 20KiB buffer (PML4, PDPT, PD, unused PT)
    mov edi, PML4            ; Point to 16KiB buffer for the paging structures.
    push di                  ; Store di (rep stosd alters di).
    mov ecx, 5*0x1000/4      ; Count should be 5*4096/4 = 5120 dwords
    xor eax, eax             ; eax = 0
    cld                      ; Set forward direction
    rep stosd                ; Fill with 0s  
    pop di                   ; Restore di
    
    ;************************* Low (identity) mapping **************************
    ; Build the PML4 (Page Map Level 4): PML4[0] -> PDPT_LOW
    lea eax, [PDPT_LOW]                  ; eax = address of the PDPT_LOW
    or eax, PAGE_PRESENT | PAGE_WRITE    ; Set the flags (present and writable)
    mov [PML4], eax                      ; PML4E[0] = eax
    ; Build the PDPT_LOW (Page Directory Pointer Table): PDPT_LOW[0] -> PD_LOW
    lea eax, [PD_LOW]                    ; eax = address of the PD_LOW
    or  eax, PAGE_PRESENT | PAGE_WRITE   ; Set the flags (present and writable)
    mov [PDPT_LOW], eax                  ; PDPT_LOW[0] = eax  
    ; Fill the PD_LOW (Page Directory) with entries (each maps a 2 MiB page)
    mov eax, 0                                       ; eax = 0 (0-2MiB identity)
    or eax, PAGE_PRESENT | PAGE_WRITE | PAGE_HUGE_PS ; Set flags (2MiB page)
    mov [PD_LOW], eax                                ; PD_LOW[0] = eax 
    ; ...
    
    ; ************************ High-half kernel mapping ************************
    ; PML4[PML4_INDEX] -> PDPT_HIGH
    lea eax, [PDPT_HIGH]                ; eax = PDPT_HIGH
    or eax, PAGE_PRESENT | PAGE_WRITE   ; Set the flags (present and writable)
    mov [PML4+PML4_INDEX*8], eax        ; PML4[PML4_INDEX] = eax
    ; PDPT_HIGH[PDPT_INDEX] -> PD_HIGH
    lea eax, [PD_HIGH]                  ; eax = PD_HIGH
    or eax, PAGE_PRESENT | PAGE_WRITE   ; Set the flags (present and writable)
    mov [PDPT_HIGH+PDPT_INDEX*8], eax   ; PDPT_HIGH[PDPT_INDEX] = eax
    ; Fill the PD_HIGH (Page Directory) with entries (each maps a 2 MiB page)
    mov di, PD_HIGH
    xor eax, eax                        ; eax = 0
    mov ecx, 512                        ; Fill 512 entries (i.e. map 1 GiB)
   .MapLoop:        
        ; Set flags: Present, Writable, 2 MiB page
        or eax, PAGE_PRESENT | PAGE_WRITE | PAGE_HUGE_PS
        mov [di], eax                   ; Store low 32 bits (entry is 8 bytes) 
        mov [di + 4], dword 0           ; Store high 32 bits 
        add di, 8                       ; Advance to next PD_HIGH entry 
        add eax, 0x200000               ; Increment address by 2MiB
        loop .MapLoop
    ret
