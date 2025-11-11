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
    mov edi, PML4         ; Point edi at the PML4 
    mov eax, 10100000b    ; Set the PAE and PGE bit.
    mov cr4, eax
    mov edx, edi          ; Point CR3 at the PML4.
    mov cr3, edx
    mov ecx, 0xC0000080   ; Read from the EFER MSR. 
    rdmsr    
    or eax, 0x00000100    ; Set the LME bit.
    wrmsr
    mov ebx, cr0          ; Activate long mode
    or ebx,0x80000001     ; by enabling paging and protection simultaneously.
    mov cr0, ebx                    
    lgdt [rel GDTR]       ; Load GDT.Pointer
    jmp CODE_SEL:LONGMODE ; Mode-Switch Jump (Load CS & flush instruction cache) 
LONGMODE: 
    BITS 64               ; We have entered the long mode! :)          
    mov ax, DATA_SEL      ; Set all segments registers to DATA_SEL.
    mov ds, ax
    mov es, ax
    mov fs, ax
    mov gs, ax
    mov ss, ax
    mov rax, KERNEL_VIRT_BASE + HIGH_KERNEL      
    jmp rax               ; Jump to high-address mapped kernel 
HIGH_KERNEL:
    lea rax, [rel GDT]          ; Load our high-address GDT
    mov [rel GDTR.Base], rax
    lgdt [rel GDTR]          
    add rsp, KERNEL_VIRT_BASE   ; Point rsp (stack) to its high address
    mov qword [abs KERNEL_VIRT_BASE + PML4], 0 ; Clear PML4[0] (identity entry)
    mov rax, cr3                ; Flush the TLB (Translation Lookaside Buffer)
    mov cr3, rax                ; Reload CR3 to flush TLB
    jmp Kernel_entrypoint       ; Jump to Kernel entrypoint
