#=========================================================================
# ProcReorderBuffer unit tests
#=========================================================================

from pymtl3 import *
from pymtl3.stdlib.test_utils import run_test_vector_sim
from proj3.ProcReorderBuffer import ProcReorderBuffer

TEST_FMT = (
  'alloc_req_lane0 alloc_has_rd_lane0 alloc_rd_addr_lane0 alloc_rd_paddr_old_lane0 '
  'alloc_req_lane1 alloc_has_rd_lane1 alloc_rd_addr_lane1 alloc_rd_paddr_old_lane1 '
  'wb_req_alu0 wb_tag_alu0 wb_req_alu1 wb_tag_alu1 '
  'wb_req_mul wb_tag_mul wb_req_mem wb_tag_mem '
  'alloc_tag_lane0* alloc_tag_lane1* rob_alloc_rdy_D* rob_full* '
  'commit_val* commit_has_rd* commit_rd_addr* commit_rd_paddr_old*'
)

#-------------------------------------------------------------------------
# dual allocate, dual ALU complete, single in-order commit
#-------------------------------------------------------------------------

def test_dual_allocate_in_order_commit( cmdline_opts ):
  dut = ProcReorderBuffer()

  run_test_vector_sim( dut, [
    TEST_FMT,

    # Allocate two instructions into tags 0 and 1.
    [ 1, 1, 1, 10,  1, 1, 2, 11,
      0, 0,  0, 0,  0, 0,  0, 0,
      0, 1, 1, 0,  0, '?', '?', '?' ],

    # Both complete in the same cycle through ALU0/ALU1.
    [ 0, 0, 0, 0,   0, 0, 0, 0,
      1, 0,  1, 1,  0, 0,  0, 0,
      '?', '?', 1, 0,  0, '?', '?', '?' ],

    # Commit remains single-wide: tag 0 first.
    [ 0, 0, 0, 0,   0, 0, 0, 0,
      0, 0,  0, 0,  0, 0,  0, 0,
      '?', '?', 1, 0,  1, 1, 1, 10 ],

    # Then tag 1.
    [ 0, 0, 0, 0,   0, 0, 0, 0,
      0, 0,  0, 0,  0, 0,  0, 0,
      '?', '?', 1, 0,  1, 1, 2, 11 ],

    # Empty.
    [ 0, 0, 0, 0,   0, 0, 0, 0,
      0, 0,  0, 0,  0, 0,  0, 0,
      '?', '?', 1, 0,  0, '?', '?', '?' ],
  ], cmdline_opts )

#-------------------------------------------------------------------------
# memory complete port and no-rd store metadata
#-------------------------------------------------------------------------

def test_mem_complete_load_store_pair( cmdline_opts ):
  dut = ProcReorderBuffer()

  run_test_vector_sim( dut, [
    TEST_FMT,

    # tag0 = lw x5 old p30, tag1 = sw with no rd.
    [ 1, 1, 5, 30,  1, 0, 0, 0,
      0, 0,  0, 0,  0, 0,  0, 0,
      0, 1, 1, 0,  0, '?', '?', '?' ],

    # Store completes first through MEM, but tag0 is still pending.
    [ 0, 0, 0, 0,   0, 0, 0, 0,
      0, 0,  0, 0,  0, 0,  1, 1,
      '?', '?', 1, 0,  0, '?', '?', '?' ],

    # Load completes later through MEM.
    [ 0, 0, 0, 0,   0, 0, 0, 0,
      0, 0,  0, 0,  0, 0,  1, 0,
      '?', '?', 1, 0,  0, '?', '?', '?' ],

    # Load commits first and returns old p30.
    [ 0, 0, 0, 0,   0, 0, 0, 0,
      0, 0,  0, 0,  0, 0,  0, 0,
      '?', '?', 1, 0,  1, 1, 5, 30 ],

    # Store commits next with has_rd=0.
    [ 0, 0, 0, 0,   0, 0, 0, 0,
      0, 0,  0, 0,  0, 0,  0, 0,
      '?', '?', 1, 0,  1, 0, 0, 0 ],
  ], cmdline_opts )

#-------------------------------------------------------------------------
# all four complete ports can clear entries in the same cycle
#-------------------------------------------------------------------------

def test_four_complete_ports( cmdline_opts ):
  dut = ProcReorderBuffer()

  run_test_vector_sim( dut, [
    TEST_FMT,

    # Allocate tags 0/1, then 2/3.
    [ 1, 1, 10, 20,  1, 1, 11, 21,
      0, 0,  0, 0,  0, 0,  0, 0,
      0, 1, 1, 0,  0, '?', '?', '?' ],

    [ 1, 1, 12, 22,  1, 1, 13, 23,
      0, 0,  0, 0,  0, 0,  0, 0,
      2, 3, 1, 0,  0, '?', '?', '?' ],

    # Complete all four entries through distinct FU ports.
    [ 0, 0, 0, 0,   0, 0, 0, 0,
      1, 0,  1, 1,  1, 2,  1, 3,
      '?', '?', 1, 0,  0, '?', '?', '?' ],

    # Commit remains one entry per cycle.
    [ 0, 0, 0, 0,   0, 0, 0, 0,
      0, 0,  0, 0,  0, 0,  0, 0,
      '?', '?', 1, 0,  1, 1, 10, 20 ],

    [ 0, 0, 0, 0,   0, 0, 0, 0,
      0, 0,  0, 0,  0, 0,  0, 0,
      '?', '?', 1, 0,  1, 1, 11, 21 ],

    [ 0, 0, 0, 0,   0, 0, 0, 0,
      0, 0,  0, 0,  0, 0,  0, 0,
      '?', '?', 1, 0,  1, 1, 12, 22 ],

    [ 0, 0, 0, 0,   0, 0, 0, 0,
      0, 0,  0, 0,  0, 0,  0, 0,
      '?', '?', 1, 0,  1, 1, 13, 23 ],
  ], cmdline_opts )

#-------------------------------------------------------------------------
# 16-entry capacity and atomic two-wide allocate readiness
#-------------------------------------------------------------------------

def test_dual_allocate_capacity_16_entries( cmdline_opts ):
  dut = ProcReorderBuffer()

  run_test_vector_sim( dut, [
    TEST_FMT,

    # Fill all sixteen entries with eight dual-allocate cycles.
    [ 1, 1,  1,  1,  1, 1,  2,  2,  0, 0,  0, 0,  0, 0,  0, 0,
      0,  1, 1, 0,  0, '?', '?', '?' ],
    [ 1, 1,  3,  3,  1, 1,  4,  4,  0, 0,  0, 0,  0, 0,  0, 0,
      2,  3, 1, 0,  0, '?', '?', '?' ],
    [ 1, 1,  5,  5,  1, 1,  6,  6,  0, 0,  0, 0,  0, 0,  0, 0,
      4,  5, 1, 0,  0, '?', '?', '?' ],
    [ 1, 1,  7,  7,  1, 1,  8,  8,  0, 0,  0, 0,  0, 0,  0, 0,
      6,  7, 1, 0,  0, '?', '?', '?' ],
    [ 1, 1,  9,  9,  1, 1, 10, 10,  0, 0,  0, 0,  0, 0,  0, 0,
      8,  9, 1, 0,  0, '?', '?', '?' ],
    [ 1, 1, 11, 11,  1, 1, 12, 12,  0, 0,  0, 0,  0, 0,  0, 0,
      10, 11, 1, 0,  0, '?', '?', '?' ],
    [ 1, 1, 13, 13,  1, 1, 14, 14,  0, 0,  0, 0,  0, 0,  0, 0,
      12, 13, 1, 0,  0, '?', '?', '?' ],
    [ 1, 1, 15, 15,  1, 1, 16, 16,  0, 0,  0, 0,  0, 0,  0, 0,
      14, 15, 1, 0,  0, '?', '?', '?' ],

    # Full: dual allocate is not ready. Complete head tag 0 through ALU0.
    [ 1, 1, 17, 17,  1, 1, 18, 18,  1, 0,  0, 0,  0, 0,  0, 0,
      0, 1, 0, 1,  0, '?', '?', '?' ],

    # tag0 commits this cycle, but current-cycle free count is still 0.
    [ 1, 1, 17, 17,  1, 1, 18, 18,  0, 0,  0, 0,  0, 0,  0, 0,
      0, 1, 0, 1,  1, 1, 1, 1 ],

    # Now there is one free entry. Atomic fetch2/dispatch2 still cannot alloc.
    [ 1, 1, 17, 17,  1, 1, 18, 18,  0, 0,  0, 0,  0, 0,  0, 0,
      0, 1, 0, 0,  0, '?', '?', '?' ],

    # One free entry is still not enough even with only one alloc_req bit set.
    [ 1, 1, 17, 17,  0, 0,  0,  0,  0, 0,  0, 0,  0, 0,  0, 0,
      0, '?', 0, 0,  0, '?', '?', '?' ],
  ], cmdline_opts )
