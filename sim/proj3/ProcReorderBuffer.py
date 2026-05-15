#=========================================================================
# ProcReorderBuffer PyMTL Wrapper
#=========================================================================

from pymtl3 import *
from pymtl3.passes.backends.verilog import *

class ProcReorderBuffer( VerilogPlaceholder, Component ):
  def construct( s ):

    # --------------------------------------------------------------------
    # Dispatch / Allocate Port
    # --------------------------------------------------------------------
    s.alloc_req           = InPort ( 1 )
    s.alloc_has_rd        = InPort ( 1 )
    s.alloc_rd_addr       = InPort ( 5 )
    s.alloc_rd_paddr_old  = InPort ( 6 )

    s.alloc_tag           = OutPort( 3 )  # fixed to 3 bits for p_num_entries=8
    s.rob_full            = OutPort( 1 )

    # --------------------------------------------------------------------
    # Writeback / Complete Port 0 (ALU/CSR)
    # --------------------------------------------------------------------
    s.wb0_req             = InPort ( 1 )
    s.wb0_tag             = InPort ( 3 )

    # --------------------------------------------------------------------
    # Writeback / Complete Port 1 (MUL)
    # --------------------------------------------------------------------
    s.wb1_req             = InPort ( 1 )
    s.wb1_tag             = InPort ( 3 )

    # --------------------------------------------------------------------
    # Writeback / Complete Port 2 (LW/SW from MemUnit M stage)
    # --------------------------------------------------------------------
    s.wb2_req             = InPort ( 1 )
    s.wb2_tag             = InPort ( 3 )

    # --------------------------------------------------------------------
    # Commit Port
    # --------------------------------------------------------------------
    s.commit_val          = OutPort( 1 )
    s.commit_has_rd       = OutPort( 1 )
    s.commit_rd_addr      = OutPort( 5 )
    s.commit_rd_paddr_old = OutPort( 6 )