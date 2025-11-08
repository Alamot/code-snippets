; Author: Alamot

BITS 16    ; On the x86, the BIOS (and consequently the bootloader) runs in 16-bit Real Mode.
ORG 0x7C00 ; We are loaded/booted by BIOS into this memory address.

Stage1_entrypoint:             ; Main entry point where BIOS leaves us. Some BIOS may load us at 0x0000:0x7C00 while others at 0x07C0:0x0000.
    jmp 0x0000:.setup_segments ; We do a far jump to accommodate for this issue (CS is reloaded to 0x0000).
    .setup_segments:           ; Next, we set all segment registers to zero.
        xor ax, ax
        mov ss, ax
        mov ds, ax
        mov es, ax
        mov fs, ax
        mov gs, ax
        mov sp, Stage1_entrypoint    ; We set up a temporary stack so that it starts growing below Stage1_entrypoint (i.e. the stack base will be located at 0:0x7c00).
        cld    ; Clear the direction flag (i.e. go forward in memory when using instructions like lodsb).

    ; Loading stage 2 from disk into RAM
    mov [disk], dl ; Storing disk number. BIOS loads into dl the "drive number" of the booted device.
    mov ax, (stage2_start-stage1_start)/512 ; ax: start sector
    mov cx, (kernel_end-stage2_start)/512   ; cx: number of sectors (512 bytes) to read
    mov bx, stage2_start                    ; bx: offset of buffer
    xor dx, dx                              ; dx: segment of buffer
    call Real_mode_read_disk

    ; Print "Stage 1 finished." message.
    mov si, stage1_message
    call Real_mode_println

    ; Jump to the entry point of stage 2 (commented out for now)
    jmp Stage2_entrypoint

    .halt: hlt
    jmp .halt     ; Infinite loop (it prevents us from going off and executing other junk in memory).


; Include
%include "stage1/disk.asm"
%include "stage1/print.asm"


times 510-($-$$) db 0 ; Padding
dw 0xAA55 ; The last two bytes of the boot sector should have the 0xAA55 signature.
; Otherwise, we'll get an error message from BIOS that it didn't find a bootable disk.
; This signature is represented in binary as 1010101001010101. The alternating bit
; pattern was thought to be a protection against certain (drive or controller) failures.
