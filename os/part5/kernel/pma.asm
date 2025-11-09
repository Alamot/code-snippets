; Author: Alamot

BITS 64

;---Constants-------------------------------------------------------------------
FRAME_FACTOR equ 12                    ; Used in fast shift operations
FRAME_SIZE   equ (1 << FRAME_FACTOR)   ; Frame size = 4096

;---Initialized data------------------------------------------------------------
PMA_bitmap_address dq 0x100000 ; Physical address of the bitmap (default at 1MB)
PMA_max_frames dq 0
PMA_bitmap_size_bytes dq 0
PMA_highest_address dq 0

;---Code------------------------------------------------------------------------
PMA_init:
;******************************************************************************;
; Initializes the bitmap-based Physical Memory Allocator (PMA).                ;
;******************************************************************************;
    push rax
    push rbx
    push rcx
    push rsi
    push rdi
    push r14

    ; --- PHASE 1: Determine highest address and bitmap size ---
    xor r14, r14                       ; r14 = 0 (will save the highest address)
    mov rcx, [abs e820_mmap_entries]   ; rcx = number of entries (loop counter)
    mov rsi, e820_mmap_buffer          ; rsi = E820 map address
   .find_max_loop:
        mov rax, [rsi]                 ; Read current E820 entry base address
        mov rbx, [rsi + 8]             ; Read current E820 entry length
        cmp dword [rsi + 16], 1        ; Check if this is usable RAM (Type 1)
        jne .next_entry                ; If not, move to next entry
        add rax, rbx                   ; rax = end address (base + length)
        cmp rax, r14                   ; Is current end address (rax) higher?
        jle .next_entry                ; If not, move to next entry
        mov r14, rax                   ; if yes, update highest address (r14)
        .next_entry:
        add rsi, 20                    ; Move to next E820 entry (20 bytes)
        loop .find_max_loop
    mov rax, r14                       ; r14 = highest physical address + 1
    sub rax, 1                         ; rax = highest physical address
    mov [abs PMA_highest_address], rax ; Store highest physical address    
    cmp rax, 0x100000                  ; Check if we have more than 1MB memory
    jg .RAM_is_greater_than_1MB        ; If not...
    mov qword [abs PMA_bitmap_address], 0x20000 ; Move PMA_bitmap_address lower
.RAM_is_greater_than_1MB:
    shr rax, FRAME_FACTOR              ; Max frame index = address / FRAME_SIZE
    inc rax                            ; rax = Total number of frames
    mov [abs PMA_max_frames], rax      ; Store total number of frames
    ; Calculate bitmap size in bytes: rax = (Max Frames + 7) / 8
    add rax, 7
    shr rax, 3
    mov [abs PMA_bitmap_size_bytes], rax ; Store bitmap size

    ; --- PHASE 2: Initialize bitmap and mark everything as USED (1) ---
    mov rdi, [abs PMA_bitmap_address]    ; Destination address (Bitmap start)
    mov rcx, [abs PMA_bitmap_size_bytes] ; Byte count
    shr rcx, 3
    mov rax, 0xFFFFFFFFFFFFFFFF          ; Value to fill (all 1s = USED)
    rep stosq                            ; Fill bitmap with 1

    ; --- PHASE 3: Mark USABLE regions as FREE (0) ---
    mov rcx, [abs e820_mmap_entries]     ; rcx = entry count (loop counter)
    mov rsi, e820_mmap_buffer            ; rsi = E820 map address
    mov r10, 0                           ; r10 = 0 (set frame as free)
   .mark_free_loop:
        cmp dword [rsi + 16], 1          ; Check if entry is USABLE RAM (Type 1)
        jne .next_entry_mark             ; If not, move to next entry
        mov rdi, [rsi]                   ; rdi = E820 entry base address
        mov rdx, [rsi + 8]               ; rdx = E820 entry length
        call PMA_mark_range              ; Call to mark this range as FREE
       .next_entry_mark:
        add rsi, 20                      ; Move to next E820 entry (20 bytes)
        loop .mark_free_loop

    ; --- PHASE 4: Mark RESERVED regions (Kernel, Bitmap, I/O) as USED (1) ---
    mov r10, 1      ; r10 = 1 (set frames as USED)
    ; 1. Mark the STACK as USED (Start=0x0, Length=0x7c00)
    mov rdi, 0x0
    mov rdx, Stage1_entrypoint    ; rdx = stack base
    call PMA_mark_range
    ; 2. Mark KERNEL code/data as USED
    mov rdi, kernel_start
    mov rdx, kernel_end
    sub rdx, rdi                  ; rdx = kernel size
    call PMA_mark_range    
    ; 3. Mark PAGING TABLES as USED
    mov rdi, PAGING_DATA
    mov rdx, 4 * 4096
    call PMA_mark_range    
    ; 4. Mark BITMAP Storage as USED
    mov rdi, [abs PMA_bitmap_address]
    mov rdx, [abs PMA_bitmap_size_bytes]
    call PMA_mark_range

    pop r14
    pop rdi
    pop rsi
    pop rcx
    pop rbx
    pop rax
    ret


PMA_mark_range:
;******************************************************************************;
; Marks a contiguous physical memory range as USED (set bits to 1).            ;
;******************************************************************************;
; rdi: Start Address                                                           ;
; rdx: Length (in bytes)                                                       ;
; r10: 0 (FREE) or 1 (USED)                                                    ;
;******************************************************************************;
    push rax
    push rbx
    push rcx
    push rdx
    push rsi
    push rdi
    test rdx, rdx             ; Check if length is zero
    jz .done
    ; Calculate start frame index (address / FRAME_SIZE)
    mov rsi, rdi              ; rsi = start address
    shr rsi, FRAME_FACTOR     ; rsi = start frame index
    ; Calculate end address and end frame index
    lea rbx, [rdi + rdx - 1]  ; rbx = end address (last byte of range)
    shr rbx, FRAME_FACTOR     ; rbx = end frame index
    mov rax, rsi              ; rax = start frame index
   .slow_mark_bits:
        call PMA_mark_frame   ; Mark current frame (rax=frame index, r10=0/1)
        inc rax               ; Next frame index
        cmp rax, rbx          ; Did we reach the end?
        ja .done             
        test rax, 7           ; Is frame index divisible by 8?
        jz .fast_mark_bytes   ; If yes, start of a byte reached, go for speed
        jmp .slow_mark_bits        
   .fast_mark_bytes:        
    mov rcx, rbx              
    sub rcx, rax               
    inc rcx              ; rcx = rbx - rax + 1 = number of remaining frames
    shr rcx, 3           ; rcx = rcx / 8 = number of bytes to fill
    test rcx, rcx        ; If rcx is 0, no whole bytes remain, go to trail bits
    jz .trail_bits                 
    call PMA_fast_mark_using_bytes
    shl rcx, 3
    add rax, rcx         ; rax = rax + rcx * 8 = next frame index to process
   .trail_bits:
    jmp .slow_mark_bits  ; Jump to mark loop        
   .done:
    pop rdi
    pop rsi
    pop rdx
    pop rcx
    pop rbx
    pop rax
    ret
    
    
PMA_fast_mark_using_bytes:
;******************************************************************************;
; Marks very fast a series of frames (it should be byte-aligned)               ;
;******************************************************************************;
; rax: Start frame index                                                       ;
; rcx: Number of rames
; r10: 0 (FREE) or 1 (USED)                                                    ;
;******************************************************************************;
    push rax
    push rcx
    push rdi
    mov rdi, [abs PMA_bitmap_address] 
    shr rax, 3                      
    add rdi, rax    ; rdi = bitmap base + (frame index / 8)
    xor rax, rax    ; rax = 0
    test r10, r10   ; Check r10 to decide the AL fill value 
    jz .set_free
    mov al, 0xFF    ; Value to fill (all 1s = USED)
   .set_free: 
    rep stosb       ; Fill bitmap with al value (0xFF for USED, 0x00 for FREE)
    pop rdi
    pop rcx
    pop rax    
    ret


PMA_mark_frame:
;******************************************************************************;
; Marks a frame as FREE (0) or USED (1).                                       ;
;******************************************************************************;
; rax: Frame index                                                             ;
; r10: 0 (FREE) or 1 (USED)                                                    ;
;******************************************************************************;
    push rax
    push rcx
    push rdx
    mov rcx, rax               ; rcx = rax = frame index
    shr rax, 3                 ; Byte offset = frame_index / 8
    and cl, 7                  ; Bit position = frame_index % 8
    mov dl, 1
    shl dl, cl                 ; dl = 1 << bit_position
    mov rcx, [abs PMA_bitmap_address]
    test r10, r10              ; Check r10: 0 -> Mark FREE, 1 -> Mark USED
    jz .unset
    or byte [rcx + rax], dl    ; Set bit (Mark USED)
    jmp .done
.unset:
    not dl                             ; dl = ~(1 << bit_position)
    and byte [rcx + rax], dl   ; Clear bit (Mark Free)
.done:
    pop rdx
    pop rcx
    pop rax
    ret


PMA_alloc_frame:
;******************************************************************************;
; Allocates a single physical memory frame.                                    ;
;------------------------------------------------------------------------------;
; Returns: rax = Physical Address of the free frame, or 0 if failure.          ;
;******************************************************************************;
    push rbx
    push rcx
    push rdx
    push rsi
    push rdi
    push r10
    mov rcx, [abs PMA_bitmap_size_bytes]   ; rcx = total bytes in bitmap
    mov rsi, [abs PMA_bitmap_address]      ; rsx = bitmap base address
    xor rbx, rbx                           ; rbx = 0 (Current byte offset)
.search_byte_loop:
    cmp rbx, rcx                           ; Did we reach the end?
    jae .fail_alloc                        ; If yes, we failed to alloc a frame
    mov al, [rsi + rbx]                    ; Load a byte from bitmap
    cmp al, 0xFF                           ; Are all bits 1 (frames USED)?
    je .next_byte                          ; If yes, move to next byte
    ; Found byte with free bits
    movzx rax, al                          ; Zero-extend byte to qword
    not rax                                ; Invert: free bits become 1
    bsf rax, rax                           ; Find first free bit position (0-7)
    ; Calculate frame index: rdi = (byte_offset * 8) + bit_position
    mov rdi, rbx
    shl rdi, 3                             ; byte_offset * 8
    add rdi, rax                           ; + bit_position = frame index
    ; Mark frame as used
    mov rax, rdi                           ; rdi = Frame index
    mov r10, 1                             ; r10 = 1 (mark frame as USED)
    call PMA_mark_frame
    ; Calculate physical address: rax = frame index * FRAME_SIZE
    mov rax, rdi
    shl rax, FRAME_FACTOR                  ; rax = physical address
    jmp .done_alloc
.next_byte:
    inc rbx
    jmp .search_byte_loop
.fail_alloc:
    xor rax, rax     ; rax = 0 (we failed to allocate a frame).
.done_alloc:
    pop r10
    pop rdi
    pop rsi
    pop rdx
    pop rcx
    pop rbx
    ret


PMA_free_frame:
;******************************************************************************;
; Allocates a single physical memory frame.                                    ;
;------------------------------------------------------------------------------;
; rdi = Physical Address of the frame to free                                  ;
;******************************************************************************;
    test rdi, rdi
    jz .done
    push rax
    push r10
    mov r10, 0               ; r10 = 0 (set frame as FREE)
    mov rax, rdi
    shr rax, FRAME_FACTOR      
    call PMA_mark_frame   
    pop r10
    pop rax
   .done:    
    ret
