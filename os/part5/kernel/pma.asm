; Author: Alamot

BITS 64

;---Constants-------------------------------------------------------------------
BITMAP_ADDR  equ 0x14000     ; Physical address for the bitmap storage.
FRAME_FACTOR equ 12          ; Used in fast shift operations (instead of divs).
FRAME_SIZE   equ (1 << FRAME_FACTOR)   ; Frame size = 4096

;---Initialized data------------------------------------------------------------
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
    shr rax, FRAME_FACTOR              ; Max frame index = address / FRAME_SIZE
    inc rax                            ; rax = Total number of frames
    mov [abs PMA_max_frames], rax      ; Store total number of frames
    ; Calculate bitmap size in bytes: rax = (Max Frames + 7) / 8
    add rax, 7
    shr rax, 3
    mov [abs PMA_bitmap_size_bytes], rax ; Store bitmap size

    ; --- PHASE 2: Initialize bitmap and mark everything as USED (1) ---
    mov rdi, BITMAP_ADDR                 ; Destination address (Bitmap start)
    mov rcx, [abs PMA_bitmap_size_bytes] ; Byte count
    mov al, 0xFF                         ; Value to fill (all 1s = USED)
    rep stosb                            ; Fill bitmap with 0xFF

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
    ; 3. Mark Bitmap Storage as USED
    mov rdi, BITMAP_ADDR
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
    push rcx
    push rsi
    test rdx, rdx             ; Check if length is zero
    jz .done
    ; Calculate start frame index (address / FRAME_SIZE)
    mov rsi, rdi              ; rsi = start address
    shr rsi, FRAME_FACTOR     ; rsi = start frame index
    ; Calculate end address and end frame index
    lea rax, [rdi + rdx - 1]  ; rax = end address (last byte of range)
    shr rax, FRAME_FACTOR     ; rax = end frame index
    ; Calculate number of frames to mark
    mov rcx, rax              ; rcx = end frame index
    sub rcx, rsi              ; rcx = end - start frame index
    inc rcx                   ; rcx = number of frames (inclusive)
    ; Start marking from the beginning
    mov rax, rsi              ; rax = current frame index (start frame index)
.mark_loop:
    call PMA_mark_frame       ; Mark current frame (rax=frame index, r10=0/1)
    inc rax                   ; Next frame index
    loop .mark_loop
.done:
    pop rsi
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
    mov rcx, rax          ; rcx = rax = frame index
    shr rax, 3            ; Byte offset = frame_index / 8
    and cl, 7             ; Bit position = frame_index % 8
    mov dl, 1
    shl dl, cl            ; dl = 1 << bit_position
    test r10, r10         ; Check r10: 0 -> Mark FREE, 1 -> Mark USED
    jz .unset
    or byte [BITMAP_ADDR + rax], dl    ; Set bit (Mark USED)
    jmp .done
.unset:
    not dl                             ; dl = ~(1 << bit_position)
    and byte [BITMAP_ADDR + rax], dl   ; Clear bit (Mark Free)
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
    mov rsi, BITMAP_ADDR                   ; rsx = bitmap base address
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
    push r10
    mov r10, 0            ; r10 = 0 (set frame as FREE)
    mov rdx, FRAME_SIZE
    call PMA_mark_range
    pop r10
    ret
