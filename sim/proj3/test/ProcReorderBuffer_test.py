#=========================================================================
# ProcReorderBuffer unit tests
#=========================================================================

from pymtl3 import *
from pymtl3.stdlib.test_utils import run_test_vector_sim
from proj3.ProcReorderBuffer import ProcReorderBuffer

TEST_FMT = (
  'alloc_req_lane0 alloc_has_rd_lane0 alloc_rd_addr_lane0 alloc_rd_paddr_old_lane0 '
  'alloc_req_lane1 alloc_has_rd_lane1 alloc_rd_addr_lane1 alloc_rd_paddr_old_lane1 '
  'wb0_req wb0_tag wb1_req wb1_tag wb2_req wb2_tag '
  'alloc_tag_lane0* alloc_tag_lane1* rob_alloc_rdy_D* rob_full* '
  'commit_val* commit_has_rd* commit_rd_addr* commit_rd_paddr_old*'
)

#-------------------------------------------------------------------------
# test 1: dual allocate, dual writeback, single in-order commit
#-------------------------------------------------------------------------

def test_dual_allocate_in_order_commit( cmdline_opts ):
  dut = ProcReorderBuffer()

  run_test_vector_sim( dut, [
    TEST_FMT,

    # Allocate two ready-later instructions into tags 0 and 1.
    [ 1, 1, 1, 10,   1, 1, 2, 11,   0, 0, 0, 0, 0, 0,
      0, 1, 1, 0,   0, '?', '?', '?' ],

    # Both complete in the same cycle through wb0/wb1.
    [ 0, 0, 0, 0,    0, 0, 0, 0,    1, 0, 1, 1, 0, 0,
      '?', '?', 1, 0,   0, '?', '?', '?' ],

    # Only one instruction commits per cycle: first tag 0.
    [ 0, 0, 0, 0,    0, 0, 0, 0,    0, 0, 0, 0, 0, 0,
      '?', '?', 1, 0,   1, 1, 1, 10 ],

    # Then tag 1.
    [ 0, 0, 0, 0,    0, 0, 0, 0,    0, 0, 0, 0, 0, 0,
      '?', '?', 1, 0,   1, 1, 2, 11 ],

    # Empty.
    [ 0, 0, 0, 0,    0, 0, 0, 0,    0, 0, 0, 0, 0, 0,
      '?', '?', 1, 0,   0, '?', '?', '?' ],
  ], cmdline_opts )

#-------------------------------------------------------------------------
# test 2: memory writeback port and no-rd store metadata
#-------------------------------------------------------------------------

def test_wb2_load_store_pair( cmdline_opts ):
  dut = ProcReorderBuffer()

  run_test_vector_sim( dut, [
    TEST_FMT,

    # tag0 = lw x5 old p30, tag1 = sw with no rd.
    [ 1, 1, 5, 30,   1, 0, 0, 0,    0, 0, 0, 0, 0, 0,
      0, 1, 1, 0,   0, '?', '?', '?' ],

    # Store completes first through wb2, but tag0 is still pending.
    [ 0, 0, 0, 0,    0, 0, 0, 0,    0, 0, 0, 0, 1, 1,
      '?', '?', 1, 0,   0, '?', '?', '?' ],

    # Load completes later through wb2.
    [ 0, 0, 0, 0,    0, 0, 0, 0,    0, 0, 0, 0, 1, 0,
      '?', '?', 1, 0,   0, '?', '?', '?' ],

    # Load commits first and returns old p30.
    [ 0, 0, 0, 0,    0, 0, 0, 0,    0, 0, 0, 0, 0, 0,
      '?', '?', 1, 0,   1, 1, 5, 30 ],

    # Store commits next with has_rd=0.
    [ 0, 0, 0, 0,    0, 0, 0, 0,    0, 0, 0, 0, 0, 0,
      '?', '?', 1, 0,   1, 0, 0, 0 ],
  ], cmdline_opts )

#-------------------------------------------------------------------------
# test 3: full / not-enough-space behavior
#-------------------------------------------------------------------------

def test_dual_allocate_capacity( cmdline_opts ):
  dut = ProcReorderBuffer()

  run_test_vector_sim( dut, [
    TEST_FMT,

    # Fill all eight entries with four dual-allocate cycles.
    [ 1, 1, 10, 10,  1, 1, 11, 11,  0, 0, 0, 0, 0, 0,
      0, 1, 1, 0,   0, '?', '?', '?' ],
    [ 1, 1, 12, 12,  1, 1, 13, 13,  0, 0, 0, 0, 0, 0,
      2, 3, 1, 0,   0, '?', '?', '?' ],
    [ 1, 1, 14, 14,  1, 1, 15, 15,  0, 0, 0, 0, 0, 0,
      4, 5, 1, 0,   0, '?', '?', '?' ],
    [ 1, 1, 16, 16,  1, 1, 17, 17,  0, 0, 0, 0, 0, 0,
      6, 7, 1, 0,   0, '?', '?', '?' ],

    # Full: dual allocate is not ready. Complete head tag 0.
    [ 1, 1, 18, 18,  1, 1, 19, 19,  1, 0, 0, 0, 0, 0,
      0, 1, 0, 1,   0, '?', '?', '?' ],

    # tag0 commits this cycle, but the current-cycle free count is still 0.
    [ 1, 1, 18, 18,  1, 1, 19, 19,  0, 0, 0, 0, 0, 0,
      0, 1, 0, 1,   1, 1, 10, 10 ],

    # Now there is one free entry. Dual allocate is still not ready.
    [ 1, 1, 18, 18,  1, 1, 19, 19,  0, 0, 0, 0, 0, 0,
      0, 1, 0, 0,   0, '?', '?', '?' ],

    # The frontend allocates a two-instruction group atomically, so one free
    # entry is still not enough even if only one alloc_req bit is asserted.
    [ 1, 1, 18, 18,  0, 0, 0, 0,   0, 0, 0, 0, 0, 0,
      0, '?', 0, 0,   0, '?', '?', '?' ],
  ], cmdline_opts )
