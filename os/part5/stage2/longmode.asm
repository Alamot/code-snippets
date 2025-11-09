; Author: Alamot

BITS 16

;---Code------------------------------------------------------------------------
Is_longmode_supported:
;********************************************************************;
; Check if Long mode is supported                                    ;
;--------------------------------------------------------------------;
; Returns: eax = 0 if Long mode is NOT supported, else non-zero.     ;
;********************************************************************;
    mov eax, 0x80000000 ; Test if extended processor info in available.  
    cpuid                
    cmp eax, 0x80000001 
    jb .not_supported     

    mov eax, 0x80000001 ; After calling CPUID with EAX = 0x80000001, 
    cpuid               ; all AMD64 compliant processors have the longmode-capable-bit
    test edx, (1 << 29) ; (bit 29) turned on in the EDX (extended feature flags).

    jz .not_supported   ; If it's not set, there is no long mode.
    ret

   .not_supported:
      xor eax, eax
      ret


Enter_long_mode:
;********************************************************************;
; Enter long mode                                                    ;
;********************************************************************;
    mov edi, PAGING_DATA ; Point edi at the PAGING_DATA.
    mov eax, 10100000b  ; Set the PAE and PGE bit.
    mov cr4, eax
    mov edx, edi        ; Point CR3 at the PML4.
    mov cr3, edx
    mov ecx, 0xC0000080 ; Read from the EFER MSR. 
    rdmsr    
    or eax, 0x00000100  ; Set the LME bit.
    wrmsr
    mov ebx, cr0        ; Activate long mode
    or ebx,0x80000001   ; by enabling paging and protection simultaneously.
    mov cr0, ebx                    
    lgdt [GDT.Pointer]  ; Load GDT.Pointer.
    jmp CODE_SEG:Kernel ; Load CS with 64 bit segment and flush the instruction cache.
