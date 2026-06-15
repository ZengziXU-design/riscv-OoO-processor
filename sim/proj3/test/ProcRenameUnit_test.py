#=========================================================================
# ProcRenameUnit unit tests
#=========================================================================

from pymtl3 import *
from pymtl3.stdlib.test_utils import run_test_vector_sim

from proj3.ProcRenameUnit import ProcRenameUnit

TEST_FMT = (
  'rename_en_D '
  'rs1_addr_D_lane0 rs2_addr_D_lane0 rd_addr_D_lane0 '
  'rs1_valid_D_lane0 rs2_valid_D_lane0 rd_valid_D_lane0 '
  'rs1_addr_D_lane1 rs2_addr_D_lane1 rd_addr_D_lane1 '
  'rs1_valid_D_lane1 rs2_valid_D_lane1 rd_valid_D_lane1 '
  'commit_rd_valid_C_lane0 commit_rd_paddr_old_C_lane0 '
  'commit_rd_valid_C_lane1 commit_rd_paddr_old_C_lane1 '
  'rename_rdy_D* '
  'rs1_paddr_D_lane0* rs2_paddr_D_lane0* '
  'rs1_paddr_valid_D_lane0* rs2_paddr_valid_D_lane0* '
  'rd_rename_valid_D_lane0* rd_paddr_old_D_lane0* rd_paddr_new_D_lane0* '
  'rs1_paddr_D_lane1* rs2_paddr_D_lane1* '
  'rs1_paddr_valid_D_lane1* rs2_paddr_valid_D_lane1* '
  'rd_rename_valid_D_lane1* rd_paddr_old_D_lane1* rd_paddr_new_D_lane1*'
)

#-------------------------------------------------------------------------
# test dual-lane sequential behavior of rename unit
#-------------------------------------------------------------------------

def test_rename_dual_lane_basic( cmdline_opts ):
  dut = ProcRenameUnit()

  # Initial state after reset:
  #   - RAT maps x0..x31 to p0..p31
  #   - p32..p63 are free, so lane0 gets p32 and lane1 gets p33
  #   - lane1 sees lane0's same-cycle destination rename

  run_test_vector_sim( dut, [
    TEST_FMT,

    # Read-only: lane1 rs1=x3 forwards lane0's new p32.
    [ 0,
      1, 2, 3,   1, 1, 1,
      3, 4, 5,   1, 1, 1,
      0, 0,  0, 0,
      1,
      1, 2,      1, 1,      1, 3, 32,
      32, 4,     1, 1,      1, 5, 33 ],

    # Commit the pair: x3->p32, x5->p33.
    [ 1,
      1, 2, 3,   1, 1, 1,
      3, 4, 5,   1, 1, 1,
      0, 0,  0, 0,
      1,
      1, 2,      1, 1,      1, 3, 32,
      32, 4,     1, 1,      1, 5, 33 ],

    # x0 destination does not allocate. lane1 uses first free p34.
    [ 1,
      3, 5, 0,   1, 1, 1,
      5, 0, 6,   1, 0, 1,
      0, 0,  0, 0,
      1,
      32, 33,    1, 1,      0, 0, 34,
      33, 0,     1, 0,      1, 6, 34 ],

    # WAW within the pair: lane1 old pdst is lane0 new p35.
    [ 1,
      0, 0, 7,   0, 0, 1,
      0, 0, 7,   0, 0, 1,
      0, 0,  0, 0,
      1,
      0, 0,      0, 0,      1, 7, 35,
      0, 0,      0, 0,      1, 35, 36 ],

    # Reclaim p3 and p5 together; they become visible on the next cycle.
    [ 0,
      7, 0, 0,   1, 0, 0,
      0, 0, 0,   0, 0, 0,
      1, 3,  1, 5,
      1,
      36, 0,     1, 0,      0, 0, 37,
      0, 0,      0, 0,      0, 0, 37 ],

    # The two reclaimed low-numbered registers are allocated before p37.
    [ 1,
      0, 0, 0,   0, 0, 0,
      0, 0, 8,   0, 0, 1,
      0, 0,  0, 0,
      1,
      0, 0,      0, 0,      0, 0, 3,
      0, 0,      0, 0,      1, 8, 3 ],

    # p5 remains free and is selected next.
    [ 1,
      0, 0, 0,   0, 0, 0,
      0, 0, 9,   0, 0, 1,
      0, 0,  0, 0,
      1,
      0, 0,      0, 0,      0, 0, 5,
      0, 0,      0, 0,      1, 9, 5 ],
  ], cmdline_opts )
