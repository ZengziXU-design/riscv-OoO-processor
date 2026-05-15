#=========================================================================
# inst_OoO.py
#=========================================================================
# Assembly tests targeting specific micro-architectural behaviors of the
# out-of-order processor.
#
# Unlike the per-instruction tests (inst_addi.py, inst_sw.py, ...), the
# tests in this file are NOT focused on the functional correctness of any
# single instruction. They verify that, when multiple instructions interact
# inside the OoO pipeline in particular ways, the hardware mechanisms
# (rename, IQ wake-up, ROB, freelist, mem-pipe, ...) still produce results
# matching the architectural specification.
#
# Each test pins down ONE property; redundant or strictly-subset tests
# have been removed so every entry covers a distinct mechanism.
#
# Tests are organized into the following sections:
#
#   Section 1: Out-of-order dispatch behavior
#       Independent ops issue ahead of a stalled producer.
#
#   Section 2: Hazard handling via register renaming
#       WAW, WAR, and dense WAW+WAR mixes.
#
#   Section 3: Resource exhaustion stalls
#       ROB full, IQ full, freelist wrap-around.
#
#   Section 4: Writeback path
#       Triple-port writeback (ALU+MUL+LW), back-to-back IQ wake-up.
#
#   Section 5: Boundary cases
#       x0 penetration through the scoreboard.
#
#   Section 6: Memory pipeline (Stage 1: in-order lw/sw)
#       mem-arith parallelism (both directions), mem ordering, lw wake-up
#       (consumer side AND producer side), in-flight=1 backpressure.
#
# Mem-section tests (Section 6) are particularly useful to also run with
# delays=True; the dmem stall path stresses mem-pipe backpressure that the
# default 0-delay run cannot reach.

import random

# Fix the random seed so results are reproducible
random.seed(0xdeadbeef)

from pymtl3 import *
from proj3.test.inst_utils import *

#=========================================================================
# Section 1: Out-of-order dispatch behavior
#=========================================================================

#-------------------------------------------------------------------------
# gen_ooo_overtake_test
#-------------------------------------------------------------------------
# A short ALU instruction overtakes a long-latency MUL stalled by RAW.
# This is the canonical OoO behavior: an independent younger op finishes
# execute before an older dependent op can even issue.

def gen_ooo_overtake_test():
  return """
    csrr x2, mngr2proc   < 2
    csrr x3, mngr2proc   < 3
    csrr x5, mngr2proc   < 4
    csrr x7, mngr2proc   < 10
    csrr x8, mngr2proc   < 20

    mul x1, x2, x3       # x1 = 6 (takes 4 cycles)
    add x4, x1, x5       # x4 = 10 (RAW on x1, trapped in IQ)
    add x6, x7, x8       # x6 = 30 (independent, overtakes)
    sub x9, x8, x7       # x9 = 10 (independent, overtakes)

    csrw proc2mngr, x1   > 6
    csrw proc2mngr, x4   > 10
    csrw proc2mngr, x6   > 30
    csrw proc2mngr, x9   > 10
  """

#=========================================================================
# Section 2: Hazard handling via register renaming
#=========================================================================

#-------------------------------------------------------------------------
# gen_ooo_waw_test
#-------------------------------------------------------------------------
# WAW: a later fast instruction overwrites the destination of an earlier
# slow MUL. Renaming maps each write to a different physical register so
# the architectural state always reflects the youngest writer.

def gen_ooo_waw_test():
  return """
    csrr x2, mngr2proc   < 2
    csrr x3, mngr2proc   < 3
    nop
    nop

    mul x1, x2, x3       # x1 = 6 (takes 4 cycles)
    add x1, x2, x2       # x1 = 4 (WAW; renames to a new physical x1)

    nop
    nop
    csrw proc2mngr, x1   > 4
  """

#-------------------------------------------------------------------------
# gen_ooo_war_test
#-------------------------------------------------------------------------
# WAR: a later writer to x1 must not corrupt an older reader of x1
# trapped in the IQ.

def gen_ooo_war_test():
  return """
    csrr x1, mngr2proc   < 10
    csrr x2, mngr2proc   < 2
    csrr x3, mngr2proc   < 3
    nop
    nop

    mul x4, x2, x3       # x4 = 6
    add x5, x1, x4       # x5 = 16 (trapped in IQ waiting for x4)
    add x1, x2, x2       # x1 = 4  (WAR; writes to a new physical x1)

    nop
    nop
    csrw proc2mngr, x1   > 4
    csrw proc2mngr, x5   > 16
  """

#-------------------------------------------------------------------------
# gen_ooo_waw_war_complex_test
#-------------------------------------------------------------------------
# A dense sequence stressing register renaming with interleaved WAW and
# WAR hazards on the same architectural registers (x3, x4).

def gen_ooo_waw_war_complex_test():
  return """
    csrr x1,  mngr2proc < 2
    csrr x2,  mngr2proc < 3
    csrr x4,  mngr2proc < 10
    csrr x5,  mngr2proc < 20
    csrr x9,  mngr2proc < 7
    csrr x10, mngr2proc < 8

    mul  x3,  x1, x2      # older slow write, old x3 = 6
    add  x7,  x4, x5      # independent fast op, x7 = 30

    add  x3,  x4, x1      # WAW on x3: younger fast write, new x3 = 12
    add  x8,  x3, x9      # should read NEW x3 (=12), x8 = 19

    add  x11, x4, x1      # reads OLD x4 (=10), x11 = 12
    add  x4,  x9, x10     # WAR on x4: younger overwrite, new x4 = 15
    add  x13, x4, x1      # should read NEW x4 (=15), x13 = 17

    mul  x6,  x3, x2      # should use NEW x3 (=12), x6 = 36
    add  x14, x9, x10     # independent fast op, x14 = 15

    csrw proc2mngr, x7  > 30
    csrw proc2mngr, x3  > 12
    csrw proc2mngr, x8  > 19
    csrw proc2mngr, x11 > 12
    csrw proc2mngr, x4  > 15
    csrw proc2mngr, x13 > 17
    csrw proc2mngr, x6  > 36
    csrw proc2mngr, x14 > 15
  """

#=========================================================================
# Section 3: Resource exhaustion stalls
#=========================================================================

#-------------------------------------------------------------------------
# gen_ooo_rob_full_test
#-------------------------------------------------------------------------
# A long-latency MUL holds the ROB head; following ALU ops fill the rest
# of the ROB and eventually force the D stage to stall.

def gen_ooo_rob_full_test():
  return """
    csrr x1, mngr2proc   < 2
    csrr x2, mngr2proc   < 3

    mul x3, x1, x2       # x3 = 6 (occupies ROB entry 0)

    # Rapidly fill the remaining ROB entries
    add x4, x1, x1       # x4 = 4
    add x5, x2, x2       # x5 = 6
    add x6, x4, x1       # x6 = 6
    add x7, x5, x2       # x7 = 9
    add x8, x1, x2       # x8 = 5
    add x9, x8, x1       # x9 = 7
    add x10, x9, x2      # x10 = 10

    # ROB full. This instruction will stall in the D stage.
    add x11, x10, x1     # x11 = 12

    csrw proc2mngr, x3   > 6
    csrw proc2mngr, x10  > 10
    csrw proc2mngr, x11  > 12
  """

#-------------------------------------------------------------------------
# gen_ooo_iq_full_test
#-------------------------------------------------------------------------
# Fills the Issue Queue (4 entries) to trigger a D-stage stall while the
# ROB (8 entries) is only partially full -- distinguishes the IQ-full
# stall path from the ROB-full stall path.

def gen_ooo_iq_full_test():
  return """
    csrr x1, mngr2proc   < 2
    csrr x2, mngr2proc   < 3

    # 1. Bottleneck instruction (occupies 1 ROB, 0 IQ once issued)
    mul x3, x1, x2       # x3 = 6 (takes 4 cycles)

    # 2. Trap 4 instructions in the IQ waiting for x3.
    #    They take 4 ROB entries and 4 IQ entries. IQ is now FULL.
    add x4, x3, x1       # IQ entry 0
    add x5, x3, x1       # IQ entry 1
    add x6, x3, x1       # IQ entry 2
    add x7, x3, x1       # IQ entry 3

    # 3. The 5th dependent instruction.
    #    The IQ is full, so this MUST stall the D stage even though the
    #    ROB still has 3 free entries.
    add x8, x3, x1       # stalls in D stage

    csrw proc2mngr, x3   > 6
    csrw proc2mngr, x8   > 8
  """

#-------------------------------------------------------------------------
# gen_ooo_freelist_wrap_around_test
#-------------------------------------------------------------------------
# Executes more instructions than there are physical registers (64) to
# ensure the ROB recycles physical registers back to the rename freelist
# without leaks.

def gen_ooo_freelist_wrap_around_test():
  # 70 independent addi instructions, continually overwriting x2.
  # Triggers 70 WAW hazards => 70 physical register allocations.
  asm_code = "csrr x1, mngr2proc < 1\n"
  for i in range(70):
    asm_code += f"    addi x2, x1, {i}\n"

  # Final value of x2 should be 1 + 69 = 70
  asm_code += "    csrw proc2mngr, x2 > 70\n"
  return asm_code

#=========================================================================
# Section 4: Writeback path
#=========================================================================

#-------------------------------------------------------------------------
# gen_ooo_tri_wb_test
#-------------------------------------------------------------------------
# Exercises all three PRF write ports concurrently. A slow MUL, a
# dependent ALU, and an in-flight lw are scheduled so that their
# writeback cycles can collide. This stresses:
#   * three concurrent PRF writes  (wr_en0/1/2 firing same cycle)
#   * three concurrent ROB completions (wb0/1/2)
#   * three concurrent IQ wake-ups (rf_wen0/1/2)
# Note: this strictly subsumes the dual-writeback (ALU+MUL only) case.

def gen_ooo_tri_wb_test():
  return """
    csrr x1,  mngr2proc < 2
    csrr x2,  mngr2proc < 3
    csrr x3,  mngr2proc < 10
    csrr x4,  mngr2proc < 20
    csrr x5,  mngr2proc < 7
    csrr x6,  mngr2proc < 8
    csrr x20, mngr2proc < 0x00002000
    csrr x21, mngr2proc < 0x00000055

    # Seed memory so the lw has a known value to fetch.
    sw   x21, 0(x20)

    # Three concurrent execution channels:
    mul  x7,  x1, x2      # MUL channel (port 1) -> x7 = 6
    lw   x11, 0(x20)      # MEM channel (port 2) -> x11 = 0x55

    # Independent ALU ops to position timing so the ALU writeback
    # can land on the same cycle as the MUL/lw writebacks.
    add  x8,  x3, x4      # x8 = 30
    add  x9,  x5, x6      # x9 = 15
    add  x10, x3, x9      # ALU channel (port 0) -> x10 = 25 (RAW on x9)

    csrw proc2mngr, x7  > 6
    csrw proc2mngr, x8  > 30
    csrw proc2mngr, x9  > 15
    csrw proc2mngr, x10 > 25
    csrw proc2mngr, x11 > 0x00000055

    .data
    .word 0x00000000
  """

#-------------------------------------------------------------------------
# gen_ooo_back_to_back_bypass_test
#-------------------------------------------------------------------------
# A tight chain of data dependencies stresses the combinational bypass
# network (IQ wake-up). The IQ must wake up and issue one instruction per
# cycle without inserting any bubbles.

def gen_ooo_back_to_back_bypass_test():
  return """
    csrr x1, mngr2proc   < 1

    add x2, x1, x1       # x2 = 2
    add x3, x2, x2       # x3 = 4
    add x4, x3, x3       # x4 = 8
    add x5, x4, x4       # x5 = 16
    add x6, x5, x5       # x6 = 32

    csrw proc2mngr, x6   > 32
  """

#=========================================================================
# Section 5: Boundary cases
#=========================================================================

#-------------------------------------------------------------------------
# gen_ooo_x0_penetration_test
#-------------------------------------------------------------------------
# x0 must completely bypass the scoreboard and register renaming.
# Dependent instructions should not wait for a long-latency operation
# whose architectural destination is x0.

def gen_ooo_x0_penetration_test():
  return """
    csrr x1, mngr2proc   < 10
    csrr x2, mngr2proc   < 20

    # 1. Slow instruction "writing" to x0
    mul x0, x1, x2       # would be 200, but x0 stays 0; takes 4 cycles

    # 2. Fast instruction reading from x0.
    #    The IQ must NOT block this on the MUL: x0 reads the hardwired 0
    #    from p0, bypassing the MUL entirely.
    add x3, x0, x1       # x3 = 0 + 10 = 10

    # 3. Follow-up to prove x3 actually executed early
    add x4, x3, x1       # x4 = 10 + 10 = 20

    csrw proc2mngr, x3   > 10
    csrw proc2mngr, x4   > 20
  """

#=========================================================================
# Section 6: Memory pipeline (Stage 1: in-order lw/sw)
#=========================================================================
# These tests target the Stage 1 mem-pipe design:
#   * a dedicated address adder + dmem-request channel parallel to the
#     ALU and MUL execution channels;
#   * in-order issue between mem instructions (no memory-disambiguation
#     hardware yet);
#   * in-flight=1 backpressure from the mem-pipe to the IQ;
#   * a third PRF write port for lw response data.

#-------------------------------------------------------------------------
# gen_ooo_mem_bypass_arith_test
#-------------------------------------------------------------------------
# An independent arithmetic instruction must be able to issue past a
# mem instruction sitting in the IQ. Verifies that mem-pipe occupancy
# does not block the arithmetic dispatch path.

def gen_ooo_mem_bypass_arith_test():
  return """
    csrr x1, mngr2proc   < 0x00002000
    csrr x2, mngr2proc   < 0xdeadbeef
    csrr x5, mngr2proc   < 7
    csrr x6, mngr2proc   < 11
    csrr x9, mngr2proc   < 100

    # Long-latency MUL holds the ALU/MUL channel.
    mul x3, x5, x6       # x3 = 77 (4 cycles)

    # Mem instruction; sits in the mem-pipe waiting on dmem.
    sw  x2, 0(x1)

    # Independent ADDs: must overtake the sw in the IQ and finish early.
    add x7, x5, x9       # x7 = 107
    add x8, x6, x9       # x8 = 111

    # Reload to verify the sw actually committed its data.
    lw  x4, 0(x1)

    csrw proc2mngr, x7   > 107
    csrw proc2mngr, x8   > 111
    csrw proc2mngr, x3   > 77
    csrw proc2mngr, x4   > 0xdeadbeef

    .data
    .word 0x00000000
  """

#-------------------------------------------------------------------------
# gen_ooo_arith_bypass_mem_test
#-------------------------------------------------------------------------
# Reverse of the previous test: a mem instruction must be able to issue
# past stalled arithmetic. Verifies that ALU/MUL stall does not block
# the mem-pipe dispatch path.

def gen_ooo_arith_bypass_mem_test():
  return """
    csrr x1, mngr2proc   < 0x00002000
    csrr x5, mngr2proc   < 6
    csrr x6, mngr2proc   < 7

    # Long-latency MUL pending in the ALU/MUL channel.
    mul x3, x5, x6       # x3 = 42 (4 cycles)
    # Dependent ADD trapped in the IQ behind the MUL.
    add x4, x3, x5       # x4 = 48 (waits for MUL)

    # Independent lw: must overtake the trapped add and finish early.
    lw  x7, 0(x1)        # x7 = 0xcafef00d

    csrw proc2mngr, x7   > 0xcafef00d
    csrw proc2mngr, x3   > 42
    csrw proc2mngr, x4   > 48

    .data
    .word 0xcafef00d
  """

#-------------------------------------------------------------------------
# gen_ooo_mem_order_test
#-------------------------------------------------------------------------
# Mem instructions must remain in program order relative to each other
# even though arithmetic instructions may overtake them. A sw followed
# by a lw to the same address must read the freshly stored value.

def gen_ooo_mem_order_test():
  return """
    csrr x1, mngr2proc   < 0x00002000
    csrr x2, mngr2proc   < 0xaaaa1111
    csrr x3, mngr2proc   < 0xbbbb2222
    csrr x9, mngr2proc   < 5

    # Two stores to different addresses.
    sw  x2, 0(x1)
    sw  x3, 4(x1)

    # Two loads, each reading what the matching sw just wrote.
    lw  x4, 0(x1)
    lw  x5, 4(x1)

    # An independent add interleaved to confirm arithmetic still runs.
    add x6, x9, x9       # x6 = 10

    csrw proc2mngr, x4   > 0xaaaa1111
    csrw proc2mngr, x5   > 0xbbbb2222
    csrw proc2mngr, x6   > 10

    .data
    .word 0x00000000
    .word 0x00000000
  """

#-------------------------------------------------------------------------
# gen_ooo_lw_dependent_test
#-------------------------------------------------------------------------
# An ADD dependent on a lw result must wait in the IQ until the lw
# response writes back through the third PRF port and the corresponding
# wake-up signal (rf_wen2) clears the scoreboard busy bit.
# Independent instructions in between must not stall.

def gen_ooo_lw_dependent_test():
  return """
    csrr x1, mngr2proc   < 0x00002000
    csrr x6, mngr2proc   < 100
    csrr x7, mngr2proc   < 200
    csrr x8, mngr2proc   < 300

    lw  x3, 0(x1)        # x3 = 0x12345678

    # Dependent on x3 -- must wait for lw writeback to wake up.
    add x4, x3, x6       # x4 = 0x12345678 + 100

    # Independent of x3 -- must issue early, ahead of the dependent add.
    add x5, x7, x8       # x5 = 500

    csrw proc2mngr, x5   > 500
    csrw proc2mngr, x3   > 0x12345678
    csrw proc2mngr, x4   > 0x123456dc

    .data
    .word 0x12345678
  """

#-------------------------------------------------------------------------
# gen_ooo_lw_base_dep_test
#-------------------------------------------------------------------------
# A lw whose BASE register is produced by a slow MUL. The lw must remain
# in the IQ until the MUL writes back and rs1_bypass_hit clears its
# scoreboard busy bit. This is the producer-side counterpart to
# gen_ooo_lw_dependent_test (which tests the consumer side of a lw).
# Without this test, an IQ bug that special-cased mem entries away from
# the normal wake-up path could go undetected.

def gen_ooo_lw_base_dep_test():
  return """
    csrr x1,  mngr2proc < 0x00001000
    csrr x2,  mngr2proc < 2
    csrr x6,  mngr2proc < 100
    csrr x7,  mngr2proc < 200

    # Slow MUL produces the base address.
    mul  x10, x1, x2     # x10 = 0x00002000 (4 cycles)

    # lw rs1=x10 -- must wait for MUL writeback before issuing into MemUnit.
    lw   x3,  0(x10)     # x3 = 0xCAFEBABE

    # Independent ADD overtakes both the MUL and the trapped lw.
    add  x4,  x6, x7     # x4 = 300

    csrw proc2mngr, x4   > 300
    csrw proc2mngr, x10  > 0x00002000
    csrw proc2mngr, x3   > 0xCAFEBABE

    .data
    .word 0xCAFEBABE
  """

#-------------------------------------------------------------------------
# gen_ooo_sw_data_dep_test
#-------------------------------------------------------------------------
# A sw whose DATA register (rs2) is produced by a slow MUL. The sw must
# remain in the IQ until the MUL writes back. Verifies that rs2 wake-up
# works for mem entries (sw uses rs2 for store data, unlike lw which
# treats rs2 as unused).

def gen_ooo_sw_data_dep_test():
  return """
    csrr x1,  mngr2proc < 0x00002000
    csrr x2,  mngr2proc < 6
    csrr x3,  mngr2proc < 7
    csrr x6,  mngr2proc < 100
    csrr x7,  mngr2proc < 200

    # Slow MUL produces the value to be stored.
    mul  x10, x2, x3     # x10 = 42 (4 cycles)

    # sw rs2=x10 -- must wait for MUL before issuing into MemUnit.
    sw   x10, 0(x1)

    # Independent ADD overtakes.
    add  x4,  x6, x7     # x4 = 300

    # Reload to verify the sw committed the post-MUL value.
    lw   x5,  0(x1)      # x5 = 42

    csrw proc2mngr, x4   > 300
    csrw proc2mngr, x10  > 42
    csrw proc2mngr, x5   > 42

    .data
    .word 0x00000000
  """

#-------------------------------------------------------------------------
# gen_ooo_mem_inflight_test
#-------------------------------------------------------------------------
# Stresses the in-flight=1 backpressure from the mem-pipe back to the IQ.
# A burst of stores followed by reloads forces the IQ to serialize all
# mem instructions while still allowing surrounding arithmetic to run.
# Best run with delays=True so dmem occasionally stalls.

def gen_ooo_mem_inflight_test():
  return """
    csrr x1,  mngr2proc < 0x00002000
    csrr x2,  mngr2proc < 0x11111111
    csrr x3,  mngr2proc < 0x22222222
    csrr x4,  mngr2proc < 0x33333333
    csrr x5,  mngr2proc < 0x44444444
    csrr x10, mngr2proc < 9

    # Burst of four stores; mem-pipe must serialize them (in-flight=1).
    sw  x2, 0(x1)
    sw  x3, 4(x1)
    sw  x4, 8(x1)
    sw  x5, 12(x1)

    # Independent arithmetic interleaved -- should still progress while
    # the mem-pipe is busy.
    add x11, x10, x10    # x11 = 18

    # Burst of four loads reading back what we just stored.
    lw  x20, 0(x1)
    lw  x21, 4(x1)
    lw  x22, 8(x1)
    lw  x23, 12(x1)

    csrw proc2mngr, x11  > 18
    csrw proc2mngr, x20  > 0x11111111
    csrw proc2mngr, x21  > 0x22222222
    csrw proc2mngr, x22  > 0x33333333
    csrw proc2mngr, x23  > 0x44444444

    .data
    .word 0x00000000
    .word 0x00000000
    .word 0x00000000
    .word 0x00000000
  """

def gen_ooo_extended_overtake_test():
  return """
    csrr x2,  mngr2proc < 2
    csrr x3,  mngr2proc < 3
    csrr x5,  mngr2proc < 4
    csrr x7,  mngr2proc < 10
    csrr x8,  mngr2proc < 20
    csrr x10, mngr2proc < 5
    csrr x11, mngr2proc < 7
    csrr x12, mngr2proc < 100
    csrr x13, mngr2proc < 50

    # ------------------------------------------------------------
    # Part 1: classic OoO overtake
    # x4 depends on the slow mul result x1, so it should stay in IQ.
    # x6 and x9 are independent and should be able to overtake.
    # ------------------------------------------------------------

    mul x1,  x2, x3        # x1  = 6   slow, 4-cycle mul
    add x4,  x1, x5        # x4  = 10  RAW on x1, waits in IQ
    add x6,  x7, x8        # x6  = 30  independent, overtakes
    sub x9,  x8, x7        # x9  = 10  independent, overtakes

    # ------------------------------------------------------------
    # Part 2: another independent mul in flight
    # This checks that the processor does not block all later muls
    # just because one mul is already in the multiplier pipeline.
    # ------------------------------------------------------------

    mul x14, x10, x11      # x14 = 35  second independent mul
    add x15, x6,  x9       # x15 = 40  uses fast ALU results
    sub x16, x12, x13      # x16 = 50  independent ALU op

    # ------------------------------------------------------------
    # Part 3: join slow and fast dependency chains
    # x17 waits for x14.
    # x18 waits for both x4 and x17.
    # ------------------------------------------------------------

    add x17, x14, x5       # x17 = 39  waits for second mul
    add x18, x4,  x17      # x18 = 49  joins two dependent chains

    # ------------------------------------------------------------
    # Part 4: third mul plus independent ALU path
    # x22 should be ready early, while x20 waits for x19.
    # ------------------------------------------------------------

    mul x19, x7,  x5       # x19 = 40  third mul
    add x22, x6,  x16      # x22 = 80  independent of x19
    add x20, x19, x16      # x20 = 90  waits for x19
    sub x21, x20, x18      # x21 = 41  final join

    # ------------------------------------------------------------
    # Part 5: rename / WAW / RAW test
    # x24 should use the OLD x23 produced by mul.
    # The later add writes a NEW x23.
    # x25 should use the NEW x23, not the old one.
    # ------------------------------------------------------------

    mul x23, x2,  x8       # old x23 = 40
    add x24, x23, x5       # x24 = 44, depends on old x23
    add x23, x7,  x8       # new x23 = 30, WAW with old x23
    sub x25, x23, x5       # x25 = 26, depends on new x23

    # ------------------------------------------------------------
    # Check final architectural state
    # ------------------------------------------------------------

    csrw proc2mngr, x1  > 6
    csrw proc2mngr, x4  > 10
    csrw proc2mngr, x6  > 30
    csrw proc2mngr, x9  > 10

    csrw proc2mngr, x14 > 35
    csrw proc2mngr, x15 > 40
    csrw proc2mngr, x16 > 50
    csrw proc2mngr, x17 > 39
    csrw proc2mngr, x18 > 49

    csrw proc2mngr, x19 > 40
    csrw proc2mngr, x20 > 90
    csrw proc2mngr, x21 > 41
    csrw proc2mngr, x22 > 80

    csrw proc2mngr, x23 > 30
    csrw proc2mngr, x24 > 44
    csrw proc2mngr, x25 > 26
  """