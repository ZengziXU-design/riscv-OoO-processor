#=========================================================================
# ProcIssueQueue unit tests
#=========================================================================
# Updated for the mem-pipe revision. The IQ now has three new behaviors:
#
#   (1) input_is_mem flag: PreDecode classifies lw/sw, IQ stores it per entry.
#   (2) mem_issue_rdy:  feedback from MemUnit. A mem entry only dispatches
#                       when both entry_ready=1 AND mem_issue_rdy=1.
#   (3) Memory ordering: oldest in-flight mem issues first; younger mem
#                        cannot pass it. Younger ALU/MUL CAN still pass
#                        a stalled mem (this is the OoO-over-mem feature).
#   (4) rf_wen2/rf_waddr2: third writeback port (lw response) participates
#                          in same-cycle wakeup bypass and scoreboard clear.
#
# CSR remains a full barrier (only issues at head, blocks all younger).

from pymtl3 import *
from pymtl3.stdlib.test_utils import run_test_vector_sim
from proj3.ProcIssueQueue import ProcIssueQueue

TEST_FMT = (
  'input_val input_inst input_rob_tag input_is_csr input_is_mem '
  'input_rs1_addr input_rs1_valid input_rs2_addr input_rs2_valid input_rd_addr input_rd_valid '
  'dispatch_rdy mem_issue_rdy '
  'rf_wen0 rf_waddr0 rf_wen1 rf_waddr1 rf_wen2 rf_waddr2 '
  'input_rdy* dispatch_val* dispatch_inst* dispatch_rob_tag* '
  'dispatch_rs1_addr* dispatch_rs2_addr* dispatch_rd_addr* dispatch_rd_valid*'
)

#-------------------------------------------------------------------------
# Test 1: Basic Independent Dispatch (No Hazards)
#-------------------------------------------------------------------------
def test_basic_dispatch( cmdline_opts ):
  dut = ProcIssueQueue()

  run_test_vector_sim( dut, [
    (TEST_FMT),
    # Cycle 1: Insert Inst A (writes to p5). Enters IQ; nothing dispatches yet.
    [ 1, 0x0000000A, 1, 0, 0,   0, 0, 0, 0, 5, 1,    1, 1,   0, 0, 0, 0, 0, 0,
      1, 0, '?', '?', '?', '?', '?', '?' ],

    # Cycle 2: Insert Inst B (writes to p6). Inst A is in IQ and ready -> dispatches.
    [ 1, 0x0000000B, 2, 0, 0,   0, 0, 0, 0, 6, 1,    1, 1,   0, 0, 0, 0, 0, 0,
      1, 1, 0x0000000A, 1, 0, 0, 5, 1 ],

    # Cycle 3: Stop inserting. Inst B in IQ, ready -> dispatches.
    [ 0, 0x00000000, 0, 0, 0,   0, 0, 0, 0, 0, 0,    1, 1,   0, 0, 0, 0, 0, 0,
      1, 1, 0x0000000B, 2, 0, 0, 6, 1 ],

    # Cycle 4: IQ empty.
    [ 0, 0x00000000, 0, 0, 0,   0, 0, 0, 0, 0, 0,    1, 1,   0, 0, 0, 0, 0, 0,
      1, 0, '?', '?', '?', '?', '?', '?' ],
  ], cmdline_opts )


#-------------------------------------------------------------------------
# Test 2: RAW Hazard and Bypass Wakeup (via wb0)
#-------------------------------------------------------------------------
def test_raw_hazard_wakeup( cmdline_opts ):
  dut = ProcIssueQueue()

  run_test_vector_sim( dut, [
    (TEST_FMT),
    # Cycle 1: Insert Inst A (writes to p10).
    [ 1, 0x0000000A, 1, 0, 0,   0, 0, 0, 0, 10, 1,   1, 1,   0, 0, 0, 0, 0, 0,
      1, 0, '?', '?', '?', '?', '?', '?' ],

    # Cycle 2: Insert Inst B (rs1=p10, rd=p11). Inst A is independent -> dispatches.
    [ 1, 0x0000000B, 2, 0, 0,   10, 1, 0, 0, 11, 1,  1, 1,   0, 0, 0, 0, 0, 0,
      1, 1, 0x0000000A, 1, 0, 0, 10, 1 ],

    # Cycle 3: B is in IQ but rs1=p10 is busy on the scoreboard -> NOT ready.
    [ 0, 0x00000000, 0, 0, 0,   0, 0, 0, 0, 0, 0,    1, 1,   0, 0, 0, 0, 0, 0,
      1, 0, '?', '?', '?', '?', '?', '?' ],

    # Cycle 4: wb0 fires for p10 -> bypass hits, B wakes up combinationally.
    [ 0, 0x00000000, 0, 0, 0,   0, 0, 0, 0, 0, 0,    1, 1,   1, 10, 0, 0, 0, 0,
      1, 1, 0x0000000B, 2, 10, 0, 11, 1 ],

    # Cycle 5: IQ empty.
    [ 0, 0x00000000, 0, 0, 0,   0, 0, 0, 0, 0, 0,    1, 1,   0, 0, 0, 0, 0, 0,
      1, 0, '?', '?', '?', '?', '?', '?' ],
  ], cmdline_opts )


#-------------------------------------------------------------------------
# Test 3: Mem dispatch basic (single lw, ready, MemUnit available)
#-------------------------------------------------------------------------
# A lw is ready and MemUnit can accept -> issues normally.
def test_mem_dispatch_basic( cmdline_opts ):
  dut = ProcIssueQueue()

  run_test_vector_sim( dut, [
    (TEST_FMT),
    # Cycle 1: Insert lw (rs1=p2, rd=p5). is_mem=1.
    [ 1, 0x10000001, 1, 0, 1,   2, 1, 0, 0, 5, 1,    1, 1,   0, 0, 0, 0, 0, 0,
      1, 0, '?', '?', '?', '?', '?', '?' ],

    # Cycle 2: lw is in IQ, rs1=p2 is not busy (no prior producer), mem_issue_rdy=1.
    # Dispatch logic: i=0 is mem, !seen_mem, ready && mem_issue_rdy=1 -> issue.
    [ 0, 0x00000000, 0, 0, 0,   0, 0, 0, 0, 0, 0,    1, 1,   0, 0, 0, 0, 0, 0,
      1, 1, 0x10000001, 1, 2, 0, 5, 1 ],

    # Cycle 3: IQ empty.
    [ 0, 0x00000000, 0, 0, 0,   0, 0, 0, 0, 0, 0,    1, 1,   0, 0, 0, 0, 0, 0,
      1, 0, '?', '?', '?', '?', '?', '?' ],
  ], cmdline_opts )


#-------------------------------------------------------------------------
# Test 4: Mem stalled by MemUnit busy, then released
#-------------------------------------------------------------------------
# A lw sits in IQ ready, but mem_issue_rdy=0 -> cannot issue. When
# mem_issue_rdy becomes 1, it issues immediately (combinationally).
def test_mem_blocked_by_unit( cmdline_opts ):
  dut = ProcIssueQueue()

  run_test_vector_sim( dut, [
    (TEST_FMT),
    # Cycle 1: Insert lw. mem_issue_rdy=0 (MemUnit busy with a prior request).
    [ 1, 0x10000001, 1, 0, 1,   2, 1, 0, 0, 5, 1,    1, 0,   0, 0, 0, 0, 0, 0,
      1, 0, '?', '?', '?', '?', '?', '?' ],

    # Cycle 2: lw in IQ, ready, but mem_issue_rdy=0 -> blocked.
    [ 0, 0x00000000, 0, 0, 0,   0, 0, 0, 0, 0, 0,    1, 0,   0, 0, 0, 0, 0, 0,
      1, 0, '?', '?', '?', '?', '?', '?' ],

    # Cycle 3: still blocked.
    [ 0, 0x00000000, 0, 0, 0,   0, 0, 0, 0, 0, 0,    1, 0,   0, 0, 0, 0, 0, 0,
      1, 0, '?', '?', '?', '?', '?', '?' ],

    # Cycle 4: mem_issue_rdy goes high -> lw issues this same cycle.
    [ 0, 0x00000000, 0, 0, 0,   0, 0, 0, 0, 0, 0,    1, 1,   0, 0, 0, 0, 0, 0,
      1, 1, 0x10000001, 1, 2, 0, 5, 1 ],

    # Cycle 5: IQ empty.
    [ 0, 0x00000000, 0, 0, 0,   0, 0, 0, 0, 0, 0,    1, 1,   0, 0, 0, 0, 0, 0,
      1, 0, '?', '?', '?', '?', '?', '?' ],
  ], cmdline_opts )


#-------------------------------------------------------------------------
# Test 5: Mem-Mem in-order issue
#-------------------------------------------------------------------------
# Two mem instructions both ready in IQ. The OLDER one must issue first;
# the younger mem cannot pass. After the older issues, mem_issue_rdy=0
# briefly (MemUnit just got busy), then becomes 1 again so the younger
# can issue.
def test_mem_in_order( cmdline_opts ):
  dut = ProcIssueQueue()

  run_test_vector_sim( dut, [
    (TEST_FMT),
    # Cycle 1: Insert lw1 (rd=p5). IQ was empty -> nothing dispatches yet.
    [ 1, 0x10000001, 1, 0, 1,   2, 1, 0, 0, 5, 1,    1, 1,   0, 0, 0, 0, 0, 0,
      1, 0, '?', '?', '?', '?', '?', '?' ],

    # Cycle 2: Insert lw2 (rd=p6). mem_issue_rdy=0 to keep lw1 in IQ.
    # lw1 is mem, ready, but mem_issue_rdy=0 -> seen_mem=1, no issue.
    # lw2 enters at slot 1 next cycle.
    [ 1, 0x10000002, 2, 0, 1,   3, 1, 0, 0, 6, 1,    1, 0,   0, 0, 0, 0, 0, 0,
      1, 0, '?', '?', '?', '?', '?', '?' ],

    # Cycle 3: Both lw1 (slot 0) and lw2 (slot 1) in IQ, both ready.
    # mem_issue_rdy=1 -> OLDER (lw1) issues, lw2 stays.
    [ 0, 0x00000000, 0, 0, 0,   0, 0, 0, 0, 0, 0,    1, 1,   0, 0, 0, 0, 0, 0,
      1, 1, 0x10000001, 1, 2, 0, 5, 1 ],

    # Cycle 4: lw2 compressed to slot 0. mem_issue_rdy=0 (MemUnit busy with lw1).
    [ 0, 0x00000000, 0, 0, 0,   0, 0, 0, 0, 0, 0,    1, 0,   0, 0, 0, 0, 0, 0,
      1, 0, '?', '?', '?', '?', '?', '?' ],

    # Cycle 5: mem_issue_rdy=1 -> lw2 issues.
    [ 0, 0x00000000, 0, 0, 0,   0, 0, 0, 0, 0, 0,    1, 1,   0, 0, 0, 0, 0, 0,
      1, 1, 0x10000002, 2, 3, 0, 6, 1 ],

    # Cycle 6: IQ empty.
    [ 0, 0x00000000, 0, 0, 0,   0, 0, 0, 0, 0, 0,    1, 1,   0, 0, 0, 0, 0, 0,
      1, 0, '?', '?', '?', '?', '?', '?' ],
  ], cmdline_opts )


#-------------------------------------------------------------------------
# Test 6: ALU passes a stalled mem (out-of-order over mem)
#-------------------------------------------------------------------------
# An older mem is blocked by mem_issue_rdy=0. A younger ALU is ready.
# The ALU must dispatch even though there's an older mem in IQ ahead of it.
# This is the key OoO-over-mem property.
def test_alu_passes_stalled_mem( cmdline_opts ):
  dut = ProcIssueQueue()

  run_test_vector_sim( dut, [
    (TEST_FMT),
    # Cycle 1: Insert lw (mem, rs1=p2, rd=p5). mem_issue_rdy=0 (MemUnit busy).
    [ 1, 0x10000001, 1, 0, 1,   2, 1, 0, 0, 5, 1,    1, 0,   0, 0, 0, 0, 0, 0,
      1, 0, '?', '?', '?', '?', '?', '?' ],

    # Cycle 2: Insert ALU (rs1=p20, rd=p7). lw still blocked, mem_issue_rdy=0.
    # Dispatch logic during this cycle: lw is mem, ready, but mem_rdy=0 ->
    # seen_mem=1, no issue, no stop_search. IQ[1] not yet valid -> no issue.
    # ALU enters slot 1 next cycle.
    [ 1, 0xA0000002, 2, 0, 0,   20, 1, 0, 0, 7, 1,   1, 0,   0, 0, 0, 0, 0, 0,
      1, 0, '?', '?', '?', '?', '?', '?' ],

    # Cycle 3: Both lw (slot 0) and ALU (slot 1) in IQ, both ready.
    # mem_issue_rdy still 0. Dispatch:
    #   i=0: lw is mem, ready, mem_rdy=0 -> seen_mem=1, NO stop_search.
    #   i=1: ALU is alu, ready -> issue!
    # The younger ALU dispatches past the stalled older mem. <-- THE POINT
    [ 0, 0x00000000, 0, 0, 0,   0, 0, 0, 0, 0, 0,    1, 0,   0, 0, 0, 0, 0, 0,
      1, 1, 0xA0000002, 2, 20, 0, 7, 1 ],

    # Cycle 4: mem_issue_rdy=1 -> lw finally issues.
    [ 0, 0x00000000, 0, 0, 0,   0, 0, 0, 0, 0, 0,    1, 1,   0, 0, 0, 0, 0, 0,
      1, 1, 0x10000001, 1, 2, 0, 5, 1 ],

    # Cycle 5: IQ empty.
    [ 0, 0x00000000, 0, 0, 0,   0, 0, 0, 0, 0, 0,    1, 1,   0, 0, 0, 0, 0, 0,
      1, 0, '?', '?', '?', '?', '?', '?' ],
  ], cmdline_opts )


#-------------------------------------------------------------------------
# Test 7: rf_wen2 wakeup (lw writeback path)
#-------------------------------------------------------------------------
# A consumer depends on a paddr that will be written back via wb2 (the
# MemUnit response port). When rf_wen2/rf_waddr2 fires, the consumer's
# rs1_bypass_hit must trigger and entry_ready must go high in the same
# cycle so dispatch happens combinationally.
def test_wb2_wakeup( cmdline_opts ):
  dut = ProcIssueQueue()

  run_test_vector_sim( dut, [
    (TEST_FMT),
    # Cycle 1: Insert producer P (rd=p15). After this, scoreboard[15]=1.
    [ 1, 0xAAAA0001, 1, 0, 0,   0, 0, 0, 0, 15, 1,   1, 1,   0, 0, 0, 0, 0, 0,
      1, 0, '?', '?', '?', '?', '?', '?' ],

    # Cycle 2: Insert consumer C (rs1=p15, rd=p20). P dispatches this cycle.
    [ 1, 0xCCCC0002, 2, 0, 0,   15, 1, 0, 0, 20, 1,  1, 1,   0, 0, 0, 0, 0, 0,
      1, 1, 0xAAAA0001, 1, 0, 0, 15, 1 ],

    # Cycle 3: C is in IQ, but scoreboard[15]=1 still and no wb fires -> NOT ready.
    [ 0, 0x00000000, 0, 0, 0,   0, 0, 0, 0, 0, 0,    1, 1,   0, 0, 0, 0, 0, 0,
      1, 0, '?', '?', '?', '?', '?', '?' ],

    # Cycle 4: rf_wen2 fires for p15 (the lw response writes back via port 2).
    # rs1_bypass_hit via wb2 -> entry_ready=1 same cycle -> C dispatches.
    [ 0, 0x00000000, 0, 0, 0,   0, 0, 0, 0, 0, 0,    1, 1,   0, 0, 0, 0, 1, 15,
      1, 1, 0xCCCC0002, 2, 15, 0, 20, 1 ],

    # Cycle 5: IQ empty.
    [ 0, 0x00000000, 0, 0, 0,   0, 0, 0, 0, 0, 0,    1, 1,   0, 0, 0, 0, 0, 0,
      1, 0, '?', '?', '?', '?', '?', '?' ],
  ], cmdline_opts )