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
  'commit_val_lane0* commit_has_rd_lane0* commit_rd_addr_lane0* commit_rd_paddr_old_lane0* '
  'commit_val_lane1* commit_has_rd_lane1* commit_rd_addr_lane1* commit_rd_paddr_old_lane1*'
)

#-------------------------------------------------------------------------
# Two adjacent ready entries commit together
#-------------------------------------------------------------------------

def test_dual_allocate_dual_commit( cmdline_opts ):
  dut = ProcReorderBuffer()

  run_test_vector_sim( dut, [
    TEST_FMT,

    # Allocate tags 0 and 1.
    [ 1, 1, 1, 10,  1, 1, 2, 11,
      0, 0,  0, 0,  0, 0,  0, 0,
      0, 1, 1, 0,
      0, '?', '?', '?',  0, '?', '?', '?' ],

    # Complete both entries. Completion is visible on the next cycle.
    [ 0, 0, 0, 0,  0, 0, 0, 0,
      1, 0,  1, 1,  0, 0,  0, 0,
      '?', '?', 1, 0,
      0, '?', '?', '?',  0, '?', '?', '?' ],

    # Both retire in order in the same cycle.
    [ 0, 0, 0, 0,  0, 0, 0, 0,
      0, 0,  0, 0,  0, 0,  0, 0,
      '?', '?', 1, 0,
      1, 1, 1, 10,  1, 1, 2, 11 ],

    # ROB is empty after the dual commit.
    [ 0, 0, 0, 0,  0, 0, 0, 0,
      0, 0,  0, 0,  0, 0,  0, 0,
      '?', '?', 1, 0,
      0, '?', '?', '?',  0, '?', '?', '?' ],
  ], cmdline_opts )

#-------------------------------------------------------------------------
# Younger ready entry cannot commit around an older pending entry
#-------------------------------------------------------------------------

def test_lane1_cannot_bypass_lane0( cmdline_opts ):
  dut = ProcReorderBuffer()

  run_test_vector_sim( dut, [
    TEST_FMT,

    [ 1, 1, 5, 30,  1, 0, 0, 0,
      0, 0,  0, 0,  0, 0,  0, 0,
      0, 1, 1, 0,
      0, '?', '?', '?',  0, '?', '?', '?' ],

    # Complete only the younger store at tag 1.
    [ 0, 0, 0, 0,  0, 0, 0, 0,
      0, 0,  0, 0,  0, 0,  1, 1,
      '?', '?', 1, 0,
      0, '?', '?', '?',  0, '?', '?', '?' ],

    # The ready younger entry cannot retire by itself.
    [ 0, 0, 0, 0,  0, 0, 0, 0,
      0, 0,  0, 0,  0, 0,  0, 0,
      '?', '?', 1, 0,
      0, '?', '?', '?',  0, '?', '?', '?' ],

    # Complete the older load at tag 0.
    [ 0, 0, 0, 0,  0, 0, 0, 0,
      0, 0,  0, 0,  0, 0,  1, 0,
      '?', '?', 1, 0,
      0, '?', '?', '?',  0, '?', '?', '?' ],

    # Both now retire together; lane1 carries no destination metadata.
    [ 0, 0, 0, 0,  0, 0, 0, 0,
      0, 0,  0, 0,  0, 0,  0, 0,
      '?', '?', 1, 0,
      1, 1, 5, 30,  1, 0, 0, 0 ],
  ], cmdline_opts )

#-------------------------------------------------------------------------
# A single ready head still commits when the next entry is pending
#-------------------------------------------------------------------------

def test_single_commit_when_second_entry_pending( cmdline_opts ):
  dut = ProcReorderBuffer()

  run_test_vector_sim( dut, [
    TEST_FMT,

    [ 1, 1, 3, 20,  1, 1, 4, 21,
      0, 0,  0, 0,  0, 0,  0, 0,
      0, 1, 1, 0,
      0, '?', '?', '?',  0, '?', '?', '?' ],

    [ 0, 0, 0, 0,  0, 0, 0, 0,
      1, 0,  0, 0,  0, 0,  0, 0,
      '?', '?', 1, 0,
      0, '?', '?', '?',  0, '?', '?', '?' ],

    # Only tag 0 is ready, so exactly one instruction retires.
    [ 0, 0, 0, 0,  0, 0, 0, 0,
      0, 0,  0, 0,  0, 0,  0, 0,
      '?', '?', 1, 0,
      1, 1, 3, 20,  0, '?', '?', '?' ],

    [ 0, 0, 0, 0,  0, 0, 0, 0,
      0, 0,  1, 1,  0, 0,  0, 0,
      '?', '?', 1, 0,
      0, '?', '?', '?',  0, '?', '?', '?' ],

    # The former lane1 entry is now the oldest and retires on lane0.
    [ 0, 0, 0, 0,  0, 0, 0, 0,
      0, 0,  0, 0,  0, 0,  0, 0,
      '?', '?', 1, 0,
      1, 1, 4, 21,  0, '?', '?', '?' ],
  ], cmdline_opts )

#-------------------------------------------------------------------------
# Four completion ports can make four entries ready for two-cycle retire
#-------------------------------------------------------------------------

def test_four_complete_ports_two_wide_commit( cmdline_opts ):
  dut = ProcReorderBuffer()

  run_test_vector_sim( dut, [
    TEST_FMT,

    [ 1, 1, 10, 20,  1, 1, 11, 21,
      0, 0,  0, 0,  0, 0,  0, 0,
      0, 1, 1, 0,
      0, '?', '?', '?',  0, '?', '?', '?' ],

    [ 1, 1, 12, 22,  1, 1, 13, 23,
      0, 0,  0, 0,  0, 0,  0, 0,
      2, 3, 1, 0,
      0, '?', '?', '?',  0, '?', '?', '?' ],

    [ 0, 0, 0, 0,  0, 0, 0, 0,
      1, 0,  1, 1,  1, 2,  1, 3,
      '?', '?', 1, 0,
      0, '?', '?', '?',  0, '?', '?', '?' ],

    [ 0, 0, 0, 0,  0, 0, 0, 0,
      0, 0,  0, 0,  0, 0,  0, 0,
      '?', '?', 1, 0,
      1, 1, 10, 20,  1, 1, 11, 21 ],

    [ 0, 0, 0, 0,  0, 0, 0, 0,
      0, 0,  0, 0,  0, 0,  0, 0,
      '?', '?', 1, 0,
      1, 1, 12, 22,  1, 1, 13, 23 ],
  ], cmdline_opts )

#-------------------------------------------------------------------------
# Full ROB regains two free entries after a dual commit
#-------------------------------------------------------------------------

def test_capacity_recovers_after_dual_commit( cmdline_opts ):
  dut = ProcReorderBuffer()
  vectors = [ TEST_FMT ]

  # Fill all sixteen entries with eight atomic dual allocations.
  for pair in range( 8 ):
    tag0 = pair * 2
    tag1 = tag0 + 1
    vectors.append([
      1, 1, tag0 + 1, tag0 + 1,  1, 1, tag1 + 1, tag1 + 1,
      0, 0,  0, 0,  0, 0,  0, 0,
      tag0, tag1, 1, 0,
      0, '?', '?', '?',  0, '?', '?', '?'
    ])

  # Full ROB cannot accept another atomic pair. Complete both head entries.
  vectors.append([
    1, 1, 17, 17,  1, 1, 18, 18,
    1, 0,  1, 1,  0, 0,  0, 0,
    0, 1, 0, 1,
    0, '?', '?', '?',  0, '?', '?', '?'
  ])

  # Commit uses the current entries, so allocate readiness remains conservative.
  vectors.append([
    1, 1, 17, 17,  1, 1, 18, 18,
    0, 0,  0, 0,  0, 0,  0, 0,
    0, 1, 0, 1,
    1, 1, 1, 1,  1, 1, 2, 2
  ])

  # On the next cycle two slots are free and atomic allocation is ready again.
  vectors.append([
    1, 1, 17, 17,  1, 1, 18, 18,
    0, 0,  0, 0,  0, 0,  0, 0,
    0, 1, 1, 0,
    0, '?', '?', '?',  0, '?', '?', '?'
  ])

  run_test_vector_sim( dut, vectors, cmdline_opts )
