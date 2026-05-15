#=========================================================================
# ProcRenameUnit unit tests
#=========================================================================

from pymtl3 import *
from pymtl3.stdlib.test_utils import run_test_vector_sim

from proj3.ProcRenameUnit import ProcRenameUnit

#-------------------------------------------------------------------------
# test sequential behavior of rename unit
#-------------------------------------------------------------------------

def test_rename_basic( cmdline_opts ):
  dut = ProcRenameUnit()

  # Note: The test vectors are executed sequentially, one per clock cycle.
  # Initial State after reset: 
  #   - rat[i] == i (Register Alias Table maps architectural register i to physical register i)
  #   - freelist_free[32..63] == 1, others == 0. First available free register is p32.

  run_test_vector_sim( dut, [
    ('rename_en_D rs1_addr_D rs2_addr_D rd_addr_D rs1_valid_D rs2_valid_D rd_valid_D commit_rd_valid_C commit_rd_paddr_old_C '
     'rename_rdy_D* rs1_paddr_D* rs2_paddr_D* rs1_paddr_valid_D* rs2_paddr_valid_D* rd_rename_valid_D* rd_paddr_old_D* rd_paddr_new_D*'),
    
    # Cycle 0: No rename operation (rename_en = 0). Read-only test.
    # Read x1, x2; write to x3. Expected outputs:
    #   - rs1_paddr should map to p1, rs2_paddr should map to p2 (current RAT mapping)
    #   - rd_paddr_old should be p3 (old physical mapping of x3)
    #   - Next available free register should be p32
    #   - rd_rename_valid_D = 1 (x3 is a valid rename target)
    [ 0,          1,         2,         3,        1,          1,          1,         0,                0,
      1,            1,           2,           1,                 1,                 1,                 3,              32 ],
    
    # Cycle 1: Execute rename operation (rename_en = 1) -> x3 will be mapped to p32.
    # Combinational output remains the same as Cycle 0 (lookahead from before the update).
    # After clock edge, the RAT will be updated: x3 -> p32
    [ 1,          1,         2,         3,        0,          0,          1,         0,                0,
      1,            1,           2,           0,                 0,                 1,                 3,              32 ],
    
    # Cycle 2: Verify x3 is now mapped to p32. Attempt to rename x0.
    # x0 cannot be renamed (rd_rename_valid_D must be 0), so the free list is not consumed.
    # Next available free register should be p33 (p32 is now taken).
    [ 1,          3,         0,         0,        1,          1,          1,         0,                0,
      1,            32,          0,           1,                 1,                 0,                 0,              33 ],
      
    # Cycle 3: Trigger commit operation to reclaim old physical register.
    # Commit x3's old physical register p3 back to the free list.
    # After clock edge, p3 becomes available again.
    [ 0,          0,         0,         0,        0,          0,          0,         1,                3,
      1,            0,           0,           0,                 0,                 0,                 0,              33 ],
      
    # Cycle 4: Verify commit effect. Reclaimed register p3 is now the first available free register.
    # (Freelist scans from low to high, so p3 reappears before p33)
    # Rename x4 to the newly reclaimed physical register p3.
    [ 1,          0,         0,         4,        0,          0,          1,         0,                0,
      1,            0,           0,           0,                 0,                 1,                 4,              3  ],
      
  ], cmdline_opts )