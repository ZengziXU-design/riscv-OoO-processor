#=========================================================================
# ProcReorderBuffer PyMTL Wrapper
#=========================================================================

from pymtl3 import *
from pymtl3.passes.backends.verilog import *

class ProcReorderBuffer( VerilogPlaceholder, Component ):
  def construct( s, p_num_entries=16, p_preg_addr_nbits=6 ):

    tag_nbits = clog2( p_num_entries )

    # --------------------------------------------------------------------
    # Dispatch / Allocate Port
    # --------------------------------------------------------------------
    s.alloc_req_lane0          = InPort ( 1 )
    s.alloc_has_rd_lane0       = InPort ( 1 )
    s.alloc_rd_addr_lane0      = InPort ( 5 )
    s.alloc_rd_paddr_old_lane0 = InPort ( p_preg_addr_nbits )

    s.alloc_req_lane1          = InPort ( 1 )
    s.alloc_has_rd_lane1       = InPort ( 1 )
    s.alloc_rd_addr_lane1      = InPort ( 5 )
    s.alloc_rd_paddr_old_lane1 = InPort ( p_preg_addr_nbits )

    s.alloc_tag_lane0          = OutPort( tag_nbits )
    s.alloc_tag_lane1          = OutPort( tag_nbits )
    s.rob_alloc_rdy_D          = OutPort( 1 )
    s.rob_full                 = OutPort( 1 )

    # --------------------------------------------------------------------
    # Writeback / Complete Port: ALU0/CSR
    # --------------------------------------------------------------------
    s.wb_req_alu0         = InPort ( 1 )
    s.wb_tag_alu0         = InPort ( tag_nbits )

    # --------------------------------------------------------------------
    # Writeback / Complete Port: ALU1
    # --------------------------------------------------------------------
    s.wb_req_alu1         = InPort ( 1 )
    s.wb_tag_alu1         = InPort ( tag_nbits )

    # --------------------------------------------------------------------
    # Writeback / Complete Port: MUL
    # --------------------------------------------------------------------
    s.wb_req_mul          = InPort ( 1 )
    s.wb_tag_mul          = InPort ( tag_nbits )

    # --------------------------------------------------------------------
    # Writeback / Complete Port: MEM
    # --------------------------------------------------------------------
    s.wb_req_mem          = InPort ( 1 )
    s.wb_tag_mem          = InPort ( tag_nbits )

    # --------------------------------------------------------------------
    # Commit Port
    # --------------------------------------------------------------------
    s.commit_val_lane0          = OutPort( 1 )
    s.commit_has_rd_lane0       = OutPort( 1 )
    s.commit_rd_addr_lane0      = OutPort( 5 )
    s.commit_rd_paddr_old_lane0 = OutPort( p_preg_addr_nbits )

    s.commit_val_lane1          = OutPort( 1 )
    s.commit_has_rd_lane1       = OutPort( 1 )
    s.commit_rd_addr_lane1      = OutPort( 5 )
    s.commit_rd_paddr_old_lane1 = OutPort( p_preg_addr_nbits )
