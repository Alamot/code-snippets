; Author: Alamot

BITS 64

;---Define----------------------------------------------------------------------
STRUC TS
  .status resw 1
  .rip resq 1
  .rax resq 1
  .rbx resq 1
  .rcx resq 1
  .rdx resq 1
  .rbp resq 1
  .rsi resq 1
  .rdi resq 1
  .rsp resq 1
  .r8  resq 1
  .r9  resq 1
  .r10 resq 1
  .r11 resq 1
  .r12 resq 1
  .r13 resq 1
  .r14 resq 1
  .r15 resq 1
  .cs resw 1
  .ds resw 1
  .es resw 1
  .fs resw 1
  .gs resw 1
  .ss resw 1
  .cr3 resq 1
  .rflags resq 1
ENDSTRUC

;---Initialized data----------------------------------------------------------
num_tasks dq 0
active_task_slot dq 0
stack_allocation dq 0
code_segment dq 0
return_address dq 0
stack_segment dq 0
stack_pointer dq 0
rflags dq 0

; Task Slot 0
TS0: ISTRUC TS 
  at TS.status, dw 0
  at TS.rip, dq 0
  at TS.rax, dq 0
  at TS.rbx, dq 0
  at TS.rcx, dq 0
  at TS.rdx, dq 0
  at TS.rbp, dq 0
  at TS.rsi, dq 0
  at TS.rdi, dq 0
  at TS.rsp, dq 0
  at TS.r8,  dq 0
  at TS.r9,  dq 0
  at TS.r10, dq 0
  at TS.r11, dq 0
  at TS.r12, dq 0
  at TS.r13, dq 0
  at TS.r14, dq 0
  at TS.r15, dq 0
  at TS.cs, dw 0
  at TS.ds, dw 0
  at TS.es, dw 0
  at TS.fs, dw 0
  at TS.gs, dw 0
  at TS.ss, dw 0
  at TS.cr3, dq 0
  at TS.rflags, dq 0
IEND

; Task Slot 1
TS1: ISTRUC TS 
  at TS.status, dw 0
  at TS.rip, dq 0
  at TS.rax, dq 0
  at TS.rbx, dq 0
  at TS.rcx, dq 0
  at TS.rdx, dq 0
  at TS.rbp, dq 0
  at TS.rsi, dq 0
  at TS.rdi, dq 0
  at TS.rsp, dq 0
  at TS.r8,  dq 0
  at TS.r9,  dq 0
  at TS.r10, dq 0
  at TS.r11, dq 0
  at TS.r12, dq 0
  at TS.r13, dq 0
  at TS.r14, dq 0
  at TS.r15, dq 0
  at TS.cs, dw 0
  at TS.ds, dw 0
  at TS.es, dw 0
  at TS.fs, dw 0
  at TS.gs, dw 0
  at TS.ss, dw 0
  at TS.cr3, dq 0
  at TS.rflags, dq 0
IEND

; Task Slot 2
TS2: ISTRUC TS 
  at TS.status, dw 0
  at TS.rip, dq 0
  at TS.rax, dq 0
  at TS.rbx, dq 0
  at TS.rcx, dq 0
  at TS.rdx, dq 0
  at TS.rbp, dq 0
  at TS.rsi, dq 0
  at TS.rdi, dq 0
  at TS.rsp, dq 0
  at TS.r8,  dq 0
  at TS.r9,  dq 0
  at TS.r10, dq 0
  at TS.r11, dq 0
  at TS.r12, dq 0
  at TS.r13, dq 0
  at TS.r14, dq 0
  at TS.r15, dq 0
  at TS.cs, dw 0
  at TS.ds, dw 0
  at TS.es, dw 0
  at TS.fs, dw 0
  at TS.gs, dw 0
  at TS.ss, dw 0
  at TS.cr3, dq 0
  at TS.rflags, dq 0
IEND

; Array of pointers to the task slots
TS_ARRAY dq TS0, TS1, TS2


;---Code------------------------------------------------------------------------
Save_task_state:   
;**********************************************************************************;
; Save task state to the active task slot                                          ;
;**********************************************************************************;
    push r15
    push r15
    push rax
    mov rax, [abs active_task_slot]
    mov r15, [TS_ARRAY+rax*8]
    mov rax, [abs code_segment]
    mov [r15+TS.cs], rax
    mov rax, [abs return_address]
    mov [r15+TS.rip], rax
    mov rax, [abs stack_segment]
    mov [r15+TS.ss], rax
    mov rax, [abs stack_pointer]
    mov [r15+TS.rsp], rax
    mov rax, [abs rflags]
    mov [r15+TS.rflags], rax
    pop rax
    mov [r15+TS.rax], rax
    mov [r15+TS.rbx], rbx
    mov [r15+TS.rcx], rcx
    mov [r15+TS.rdx], rdx
    mov [r15+TS.rbp], rbp
    mov [r15+TS.rsi], rsi
    mov [r15+TS.rdi], rdi
    mov [r15+TS.r8], r8
    mov [r15+TS.r9], r9
    mov [r15+TS.r10], r10
    mov [r15+TS.r11], r11
    mov [r15+TS.r12], r12
    mov [r15+TS.r13], r13
    mov [r15+TS.r14], r14
    pop qword [r15+TS.r15]
    pop r15
    ret


Load_task_state:    
;**********************************************************************************;
; Load task state from the active task slot                                        ;
;**********************************************************************************;
    mov rax, [abs active_task_slot]
    mov r15, [TS_ARRAY+rax*8]
    mov rax, [r15+TS.rip]
    mov [abs return_address], rax
    mov rax, [r15+TS.cs]
    mov [abs code_segment], rax
    mov rax, [r15+TS.ss]
    mov [abs stack_segment], rax
    mov rax, [r15+TS.rsp]
    mov [abs stack_pointer], rax
    mov rax, [r15+TS.rflags]
    mov [abs rflags], rax
    mov rax, [r15+TS.rax]
    mov rbx, [r15+TS.rbx]
    mov rcx, [r15+TS.rcx]
    mov rdx, [r15+TS.rdx]
    mov rbp, [r15+TS.rbp]
    mov rsi, [r15+TS.rsi]
    mov rdi, [r15+TS.rdi]
    mov r8,  [r15+TS.r8]
    mov r9,  [r15+TS.r9]
    mov r10, [r15+TS.r10]
    mov r11, [r15+TS.r11]
    mov r12, [r15+TS.r12]
    mov r13, [r15+TS.r13]
    mov r14, [r15+TS.r14]
    push qword [r15+TS.r15]
    pop r15
    ret


Create_task:
;**********************************************************************************;
; Crate a new task                                                                 ;
;----------------------------------------------------------------------------------;
; rsi: pointer to the address of the first instruction of the task                 ;
;**********************************************************************************;
    push rax
    push r15
    ; Trick to save RFLAGS to [rflags]
    pushfq
    mov rax, [rsp]
    mov [abs rflags], rax
    add rsp, 8 ; Instead of popfq
    ; Save code and stack selectors
    mov [abs code_segment], cs
    mov [abs stack_segment], ss
    ;Set active task slot equal to the number of tasks.
    ;This means we make active an emply slot (as we count task slots from 0).
    mov rax, [abs num_tasks]
    mov qword [abs active_task_slot], rax
    ; Init task state.
    call Save_task_state
    ; Set rip (in the state of task) equal to rsi (i.e. the task address).
    mov r15, [TS_ARRAY+rax*8]
    mov qword [r15+TS.rip], rsi 
    ; Allocate a new stack of 1000 bytes for the task.
    sub qword [abs stack_allocation], 1000  
    mov rax, [abs stack_allocation]
    ; Set rsp (in the state of task) to point to the new stack for the task.
    mov qword [r15+TS.rsp], rax
    ; Increase number of tasks by one.
    inc qword [abs num_tasks]
    pop r15
    pop rax
    ret
