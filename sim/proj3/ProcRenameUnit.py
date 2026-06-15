#=========================================================================
# ProcRenameUnit PyMTL Wrapper
#=========================================================================

from pymtl3 import *
from pymtl3.passes.backends.verilog import *

class ProcRenameUnit( VerilogPlaceholder, Component ):
  def construct( s, p_preg_addr_nbits=6 ):
    s.rename_en_D           = InPort ( 1 )
    s.rename_rdy_D          = OutPort( 1 )

    s.rs1_addr_D_lane0      = InPort ( 5 )
    s.rs2_addr_D_lane0      = InPort ( 5 )
    s.rd_addr_D_lane0       = InPort ( 5 )

    s.rs1_valid_D_lane0     = InPort ( 1 )
    s.rs2_valid_D_lane0     = InPort ( 1 )
    s.rd_valid_D_lane0      = InPort ( 1 )

    s.rs1_addr_D_lane1      = InPort ( 5 )
    s.rs2_addr_D_lane1      = InPort ( 5 )
    s.rd_addr_D_lane1       = InPort ( 5 )

    s.rs1_valid_D_lane1     = InPort ( 1 )
    s.rs2_valid_D_lane1     = InPort ( 1 )
    s.rd_valid_D_lane1      = InPort ( 1 )

    s.rs1_paddr_D_lane0     = OutPort( p_preg_addr_nbits )
    s.rs2_paddr_D_lane0     = OutPort( p_preg_addr_nbits )
    s.rs1_paddr_valid_D_lane0 = OutPort( 1 )
    s.rs2_paddr_valid_D_lane0 = OutPort( 1 )

    s.rs1_paddr_D_lane1     = OutPort( p_preg_addr_nbits )
    s.rs2_paddr_D_lane1     = OutPort( p_preg_addr_nbits )
    s.rs1_paddr_valid_D_lane1 = OutPort( 1 )
    s.rs2_paddr_valid_D_lane1 = OutPort( 1 )

    s.rd_rename_valid_D_lane0 = OutPort( 1 )
    s.rd_paddr_old_D_lane0  = OutPort( p_preg_addr_nbits )
    s.rd_paddr_new_D_lane0  = OutPort( p_preg_addr_nbits )

    s.rd_rename_valid_D_lane1 = OutPort( 1 )
    s.rd_paddr_old_D_lane1  = OutPort( p_preg_addr_nbits )
    s.rd_paddr_new_D_lane1  = OutPort( p_preg_addr_nbits )

    s.commit_rd_valid_C_lane0     = InPort ( 1 )
    s.commit_rd_paddr_old_C_lane0 = InPort ( p_preg_addr_nbits )
    s.commit_rd_valid_C_lane1     = InPort ( 1 )
    s.commit_rd_paddr_old_C_lane1 = InPort ( p_preg_addr_nbits )
