#=========================================================================
# ProcIssueQueue PyMTL Wrapper
#=========================================================================

from pymtl3 import *
from pymtl3.passes.backends.verilog import *

class ProcIssueQueue( VerilogPlaceholder, Component ):
  def construct( s, p_num_entries=8, p_prf_addr_nbits=6, p_rob_tag_nbits=3 ):

    # --------------------------------------------------------------------
    # Upstream interface (From D stage)
    # --------------------------------------------------------------------
    s.input_val_lane0   = InPort ( 1 )
    s.input_val_lane1   = InPort ( 1 )
    s.input_rdy         = OutPort( 1 )

    s.input_inst_lane0    = InPort ( 32 )
    s.input_rob_tag_lane0 = InPort ( p_rob_tag_nbits )
    s.input_is_csr_lane0  = InPort ( 1 )
    s.input_is_mem_lane0  = InPort ( 1 )

    s.input_inst_lane1    = InPort ( 32 )
    s.input_rob_tag_lane1 = InPort ( p_rob_tag_nbits )
    s.input_is_csr_lane1  = InPort ( 1 )
    s.input_is_mem_lane1  = InPort ( 1 )

    s.input_rs1_addr_lane0  = InPort ( p_prf_addr_nbits )
    s.input_rs1_valid_lane0 = InPort ( 1 )
    s.input_rs2_addr_lane0  = InPort ( p_prf_addr_nbits )
    s.input_rs2_valid_lane0 = InPort ( 1 )
    s.input_rd_addr_lane0   = InPort ( p_prf_addr_nbits )
    s.input_rd_valid_lane0  = InPort ( 1 )

    s.input_rs1_addr_lane1  = InPort ( p_prf_addr_nbits )
    s.input_rs1_valid_lane1 = InPort ( 1 )
    s.input_rs2_addr_lane1  = InPort ( p_prf_addr_nbits )
    s.input_rs2_valid_lane1 = InPort ( 1 )
    s.input_rd_addr_lane1   = InPort ( p_prf_addr_nbits )
    s.input_rd_valid_lane1  = InPort ( 1 )

    # --------------------------------------------------------------------
    # Downstream interface (To Execution / Issue stage)
    # --------------------------------------------------------------------
    s.dispatch_val      = OutPort( 1 )
    s.dispatch_rdy      = InPort ( 1 )

    s.mem_issue_rdy     = InPort ( 1 )   # NEW: feedback from MemUnit M-stage

    s.dispatch_inst     = OutPort( 32 )
    s.dispatch_rob_tag  = OutPort( p_rob_tag_nbits )
    s.dispatch_rs1_addr = OutPort( p_prf_addr_nbits )
    s.dispatch_rs2_addr = OutPort( p_prf_addr_nbits )
    s.dispatch_rd_addr  = OutPort( p_prf_addr_nbits )
    s.dispatch_rd_valid = OutPort( 1 )

    # --------------------------------------------------------------------
    # Writeback feedback (3 ports: ALU, MUL, LW)
    # --------------------------------------------------------------------
    s.rf_wen0           = InPort ( 1 )
    s.rf_waddr0         = InPort ( p_prf_addr_nbits )
    s.rf_wen1           = InPort ( 1 )
    s.rf_waddr1         = InPort ( p_prf_addr_nbits )
    s.rf_wen2           = InPort ( 1 )                    # NEW: lw response wakeup
    s.rf_waddr2         = InPort ( p_prf_addr_nbits )     # NEW
