; Author: Alamot

BITS 16

;---Initialized data------------------------------------------------------------
stage2_message dw 19
db 'Entering Stage 2...'
longmode_supported_message dw 23
db 'Long mode is supported.'
longmode_not_supported_message dw 27
db 'Long mode is not supported.'

;---Code------------------------------------------------------------------------
Stage2_entrypoint:
      ; Print 'Entering Stage 2...' message
      mov si, stage2_message
      call Real_mode_println
       
      ; Get memory map
      call Get_E820_map
       
      ; Check if long mode is supported
      call Is_longmode_supported
      test eax, eax
      jz .long_mode_not_supported
      mov si, longmode_supported_message
      call Real_mode_println

      ; Enable Gate A20
      call Enable_A20
      ; Prepare paging  
      call Prepare_paging
      ; Remap PIC
      call Remap_PIC
      ; Enter long mode
      call Enter_long_mode

     .long_mode_not_supported:
        mov si, longmode_not_supported_message
        call Real_mode_println
       .halt: hlt ; Infinite loop. 
        jmp .halt ; (It prevents us from going off in memory and executing junk).


; Include
%include "stage2/e280_mapping.asm"
%include "stage2/a20.asm"
%include "stage2/paging.asm"
%include "stage2/pic.asm"
%include "stage2/longmode.asm"

