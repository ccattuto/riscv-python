.section .text
.globl trap_handler_riscvpy

trap_handler_riscvpy:
    addi    sp, sp, -64

    # Save RA and temporaries (t0–t6)
    sw      ra,  0(sp)
    sw      t0,  4(sp)
    sw      t1,  8(sp)
    sw      t2, 12(sp)
    sw      t3, 16(sp)
    sw      t4, 20(sp)
    sw      t5, 24(sp)
    sw      t6, 28(sp)
    # Save a0–a7 (arguments)
    sw      a0, 32(sp)
    sw      a1, 36(sp)
    sw      a2, 40(sp)
    sw      a3, 44(sp)
    sw      a4, 48(sp)
    sw      a5, 52(sp)
    sw      a6, 56(sp)
    sw      a7, 60(sp)

    # Check for timer interrupt
    csrr    t0, mcause
    li      t1, 0x80000007
    bne     t0, t1, 1f 

    # Call supervisor_tick()
    call    port_tick

	# Update mtimecmp
	call	rearm_timer

1:
    # Restore a0–a7
    lw      a0, 32(sp)
    lw      a1, 36(sp)
    lw      a2, 40(sp)
    lw      a3, 44(sp)
    lw      a4, 48(sp)
    lw      a5, 52(sp)
    lw      a6, 56(sp)
    lw      a7, 60(sp)
    # Restore RA and temporaries
    lw      ra,  0(sp)
    lw      t0,  4(sp)
    lw      t1,  8(sp)
    lw      t2, 12(sp)
    lw      t3, 16(sp)
    lw      t4, 20(sp)
    lw      t5, 24(sp)
    lw      t6, 28(sp)

    addi    sp, sp, 64

    # Return from trap
    mret

