#=========================================================================
# ProcReorderBuffer unit tests
#=========================================================================
# Updated for the mem-pipe revision: ROB now exposes a third writeback
# completion port (wb2) for lw / sw completing out of the M stage.

from pymtl3 import *
from pymtl3.stdlib.test_utils import run_test_vector_sim
from proj3.ProcReorderBuffer import ProcReorderBuffer

TEST_FMT = (
  'alloc_req alloc_has_rd alloc_rd_addr alloc_rd_paddr_old '
  'wb0_req wb0_tag wb1_req wb1_tag wb2_req wb2_tag '
  'alloc_tag* rob_full* '
  'commit_val* commit_has_rd* commit_rd_addr* commit_rd_paddr_old*'
)

#-------------------------------------------------------------------------
# test 1: Basic In-Order Allocate, Writeback, Commit  (ALU port wb0)
#-------------------------------------------------------------------------
def test_in_order( cmdline_opts ):
  dut = ProcReorderBuffer()

  run_test_vector_sim( dut, [
    (TEST_FMT),
#   alloc alloc alloc alloc  | wb0   wb0 | wb1   wb1 | wb2   wb2 | alloc rob   | commit commit commit commit
#   req   has   rd    p_old  | req   tag | req   tag | req   tag | >tag* full* | val*  has*   rd*    p_old*
# -------------------------------------------------------------------------------------------------------------
    # Cycle 1: Allocate Inst 0 (e.g. ALU writes to x1, old paddr=10) -> tag 0
    [ 1,    1,    1,    10,    0,    0,    0,    0,    0,    0,    0,    0,      0,     '?',   '?',   '?'  ],
    # Cycle 2: Writeback Inst 0 on Port 0 (ALU)
    [ 0,    0,    0,    0,     1,    0,    0,    0,    0,    0,    1,    0,      0,     '?',   '?',   '?'  ],
    # Cycle 3: Commit Inst 0
    [ 0,    0,    0,    0,     0,    0,    0,    0,    0,    0,    1,    0,      1,     1,     1,     10   ],
    # Cycle 4: Idle
    [ 0,    0,    0,    0,     0,    0,    0,    0,    0,    0,    1,    0,      0,     '?',   '?',   '?'  ],
  ], cmdline_opts )


#-------------------------------------------------------------------------
# test 2: Out-of-Order Writeback, In-Order Commit (wb0 + wb1 / ALU vs MUL)
#-------------------------------------------------------------------------
def test_out_of_order( cmdline_opts ):
  dut = ProcReorderBuffer()

  run_test_vector_sim( dut, [
    (TEST_FMT),
#   alloc alloc alloc alloc  | wb0   wb0 | wb1   wb1 | wb2   wb2 | alloc rob   | commit commit commit commit
#   req   has   rd    p_old  | req   tag | req   tag | req   tag | >tag* full* | val*  has*   rd*    p_old*
# -------------------------------------------------------------------------------------------------------------
    # Cycle 1: Allocate Inst 0 (slow MUL to x2)  -> tag 0
    [ 1,    1,    2,    11,    0,    0,    0,    0,    0,    0,    0,    0,      0,     '?',   '?',   '?'  ],
    # Cycle 2: Allocate Inst 1 (fast ADD to x3)  -> tag 1
    [ 1,    1,    3,    12,    0,    0,    0,    0,    0,    0,    1,    0,      0,     '?',   '?',   '?'  ],
    # Cycle 3: Writeback Inst 1 early (ADD on wb0). Head is still tag 0 -> no commit yet.
    [ 0,    0,    0,    0,     1,    1,    0,    0,    0,    0,    2,    0,      0,     '?',   '?',   '?'  ],
    # Cycle 4: Writeback Inst 0 later (MUL on wb1).
    [ 0,    0,    0,    0,     0,    0,    1,    0,    0,    0,    2,    0,      0,     '?',   '?',   '?'  ],
    # Cycle 5: Inst 0 commits (head moves to 1).
    [ 0,    0,    0,    0,     0,    0,    0,    0,    0,    0,    2,    0,      1,     1,     2,     11   ],
    # Cycle 6: Inst 1 commits.
    [ 0,    0,    0,    0,     0,    0,    0,    0,    0,    0,    2,    0,      1,     1,     3,     12   ],
    # Cycle 7: Idle (ROB empty again).
    [ 0,    0,    0,    0,     0,    0,    0,    0,    0,    0,    2,    0,      0,     '?',   '?',   '?'  ],
  ], cmdline_opts )


#-------------------------------------------------------------------------
# test 3: ROB Full Stall and Wrap-around
#-------------------------------------------------------------------------
def test_rob_full( cmdline_opts ):
  dut = ProcReorderBuffer()

  run_test_vector_sim( dut, [
    (TEST_FMT),
#   alloc alloc alloc alloc  | wb0   wb0 | wb1   wb1 | wb2   wb2 | alloc rob   | commit commit commit commit
#   req   has   rd    p_old  | req   tag | req   tag | req   tag | >tag* full* | val*  has*   rd*    p_old*
# -------------------------------------------------------------------------------------------------------------
    # Rapidly fill all 8 entries
    [ 1,    1,    10,   10,    0,    0,    0,    0,    0,    0,    0,    0,      0,     '?',   '?',   '?'  ], # slot 0
    [ 1,    1,    11,   11,    0,    0,    0,    0,    0,    0,    1,    0,      0,     '?',   '?',   '?'  ], # slot 1
    [ 1,    1,    12,   12,    0,    0,    0,    0,    0,    0,    2,    0,      0,     '?',   '?',   '?'  ], # slot 2
    [ 1,    1,    13,   13,    0,    0,    0,    0,    0,    0,    3,    0,      0,     '?',   '?',   '?'  ], # slot 3
    [ 1,    1,    14,   14,    0,    0,    0,    0,    0,    0,    4,    0,      0,     '?',   '?',   '?'  ], # slot 4
    [ 1,    1,    15,   15,    0,    0,    0,    0,    0,    0,    5,    0,      0,     '?',   '?',   '?'  ], # slot 5
    [ 1,    1,    16,   16,    0,    0,    0,    0,    0,    0,    6,    0,      0,     '?',   '?',   '?'  ], # slot 6
    [ 1,    1,    17,   17,    0,    0,    0,    0,    0,    0,    7,    0,      0,     '?',   '?',   '?'  ], # slot 7
    # Cycle 9: ROB FULL. alloc_req is ignored internally; rob_full goes high.
    # We simultaneously writeback slot 0 to free a spot next cycle.
    [ 1,    1,    18,   18,    1,    0,    0,    0,    0,    0,    0,    1,      0,     '?',   '?',   '?'  ],
    # Cycle 10: Slot 0 commits. rob_full is still 1 combinationally this cycle.
    [ 0,    0,    0,    0,     0,    0,    0,    0,    0,    0,    0,    1,      1,     1,     10,    10   ],
    # Cycle 11: Space available again.
    [ 0,    0,    0,    0,     0,    0,    0,    0,    0,    0,    0,    0,      0,     '?',   '?',   '?'  ],
  ], cmdline_opts )


#-------------------------------------------------------------------------
# test 4: lw completes via wb2 (mem port)
#-------------------------------------------------------------------------
# A load instruction allocates a ROB entry, sits pending while it waits for
# the dmem response, then is woken via wb2 and commits with has_rd=1.
def test_mem_lw( cmdline_opts ):
  dut = ProcReorderBuffer()

  run_test_vector_sim( dut, [
    (TEST_FMT),
#   alloc alloc alloc alloc  | wb0   wb0 | wb1   wb1 | wb2   wb2 | alloc rob   | commit commit commit commit
#   req   has   rd    p_old  | req   tag | req   tag | req   tag | >tag* full* | val*  has*   rd*    p_old*
# -------------------------------------------------------------------------------------------------------------
    # Cycle 1: Allocate LW to x5, old paddr=30 -> tag 0
    [ 1,    1,    5,    30,    0,    0,    0,    0,    0,    0,    0,    0,      0,     '?',   '?',   '?'  ],
    # Cycle 2: Memory still in flight, no writeback. Head=tag 0 still pending -> no commit.
    [ 0,    0,    0,    0,     0,    0,    0,    0,    0,    0,    1,    0,      0,     '?',   '?',   '?'  ],
    # Cycle 3: Memory still in flight -> still no commit.
    [ 0,    0,    0,    0,     0,    0,    0,    0,    0,    0,    1,    0,      0,     '?',   '?',   '?'  ],
    # Cycle 4: dmem response arrives -> wb2 fires for tag 0 (clears pending).
    [ 0,    0,    0,    0,     0,    0,    0,    0,    1,    0,    1,    0,      0,     '?',   '?',   '?'  ],
    # Cycle 5: LW commits with has_rd=1, returns p_old=30 to Rename.
    [ 0,    0,    0,    0,     0,    0,    0,    0,    0,    0,    1,    0,      1,     1,     5,     30   ],
    # Cycle 6: Idle.
    [ 0,    0,    0,    0,     0,    0,    0,    0,    0,    0,    1,    0,      0,     '?',   '?',   '?'  ],
  ], cmdline_opts )


#-------------------------------------------------------------------------
# test 5: sw completes via wb2 (no rd path)
#-------------------------------------------------------------------------
# A store has no architectural destination, so alloc_has_rd=0 and the
# commit must report has_rd=0 even though wb2 fires. This protects the
# Rename freelist from getting an unwanted release.
def test_mem_sw( cmdline_opts ):
  dut = ProcReorderBuffer()

  run_test_vector_sim( dut, [
    (TEST_FMT),
#   alloc alloc alloc alloc  | wb0   wb0 | wb1   wb1 | wb2   wb2 | alloc rob   | commit commit commit commit
#   req   has   rd    p_old  | req   tag | req   tag | req   tag | >tag* full* | val*  has*   rd*    p_old*
# -------------------------------------------------------------------------------------------------------------
    # Cycle 1: Allocate SW (has_rd=0) -> tag 0
    [ 1,    0,    0,    0,     0,    0,    0,    0,    0,    0,    0,    0,      0,     '?',   '?',   '?'  ],
    # Cycle 2: Wait for dmem to ack the store. Pending -> no commit.
    [ 0,    0,    0,    0,     0,    0,    0,    0,    0,    0,    1,    0,      0,     '?',   '?',   '?'  ],
    # Cycle 3: dmem ack -> wb2 fires for tag 0.
    [ 0,    0,    0,    0,     0,    0,    0,    0,    1,    0,    1,    0,      0,     '?',   '?',   '?'  ],
    # Cycle 4: SW commits with has_rd=0 (no PRF freeing).
    [ 0,    0,    0,    0,     0,    0,    0,    0,    0,    0,    1,    0,      1,     0,     0,     0    ],
    # Cycle 5: Idle.
    [ 0,    0,    0,    0,     0,    0,    0,    0,    0,    0,    1,    0,      0,     '?',   '?',   '?'  ],
  ], cmdline_opts )


#-------------------------------------------------------------------------
# test 6: Three writeback ports fire in the same cycle
#-------------------------------------------------------------------------
# Verifies that wb0 / wb1 / wb2 do not interfere when they each clear a
# different ROB tag's pending bit on the same edge. After the triple
# writeback, all three instructions must commit in program order on
# successive cycles.
def test_three_port_wb( cmdline_opts ):
  dut = ProcReorderBuffer()

  run_test_vector_sim( dut, [
    (TEST_FMT),
#   alloc alloc alloc alloc  | wb0   wb0 | wb1   wb1 | wb2   wb2 | alloc rob   | commit commit commit commit
#   req   has   rd    p_old  | req   tag | req   tag | req   tag | >tag* full* | val*  has*   rd*    p_old*
# -------------------------------------------------------------------------------------------------------------
    # Cycle 1: Allocate ALU inst (rd=1, p_old=20)  -> tag 0
    [ 1,    1,    1,    20,    0,    0,    0,    0,    0,    0,    0,    0,      0,     '?',   '?',   '?'  ],
    # Cycle 2: Allocate MUL inst (rd=2, p_old=21)  -> tag 1
    [ 1,    1,    2,    21,    0,    0,    0,    0,    0,    0,    1,    0,      0,     '?',   '?',   '?'  ],
    # Cycle 3: Allocate LW inst  (rd=3, p_old=22)  -> tag 2
    [ 1,    1,    3,    22,    0,    0,    0,    0,    0,    0,    2,    0,      0,     '?',   '?',   '?'  ],
    # Cycle 4: Triple writeback in the same cycle: ALU/wb0 tag 0, MUL/wb1 tag 1, LW/wb2 tag 2.
    [ 0,    0,    0,    0,     1,    0,    1,    1,    1,    2,    3,    0,      0,     '?',   '?',   '?'  ],
    # Cycle 5: Inst 0 commits (head=0 -> 1).
    [ 0,    0,    0,    0,     0,    0,    0,    0,    0,    0,    3,    0,      1,     1,     1,     20   ],
    # Cycle 6: Inst 1 commits (head=1 -> 2).
    [ 0,    0,    0,    0,     0,    0,    0,    0,    0,    0,    3,    0,      1,     1,     2,     21   ],
    # Cycle 7: Inst 2 commits (head=2 -> 3).
    [ 0,    0,    0,    0,     0,    0,    0,    0,    0,    0,    3,    0,      1,     1,     3,     22   ],
    # Cycle 8: Idle (ROB empty).
    [ 0,    0,    0,    0,     0,    0,    0,    0,    0,    0,    3,    0,      0,     '?',   '?',   '?'  ],
  ], cmdline_opts )