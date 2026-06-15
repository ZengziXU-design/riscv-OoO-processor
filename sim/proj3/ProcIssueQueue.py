#=========================================================================
# ProcIssueQueue PyMTL Wrapper
#=========================================================================

from pymtl3 import *
from pymtl3.passes.backends.verilog import *

class ProcIssueQueue( VerilogPlaceholder, Component ):
  def construct( s, p_num_entries=8, p_prf_addr_nbits=6, p_rob_tag_nbits=4 ):

    s.input_val_lane0 = InPort ( 1 )
    s.input_val_lane1 = InPort ( 1 )
    s.input_rdy       = OutPort( 1 )

    s.input_inst_lane0    = InPort ( 32 )
    s.input_rob_tag_lane0 = InPort ( p_rob_tag_nbits )
    s.input_is_csr_lane0  = InPort ( 1 )
    s.input_is_mem_lane0  = InPort ( 1 )
    s.input_is_mul_lane0  = InPort ( 1 )

    s.input_inst_lane1    = InPort ( 32 )
    s.input_rob_tag_lane1 = InPort ( p_rob_tag_nbits )
    s.input_is_csr_lane1  = InPort ( 1 )
    s.input_is_mem_lane1  = InPort ( 1 )
    s.input_is_mul_lane1  = InPort ( 1 )

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

    s.alu0_dispatch_val      = OutPort( 1 )
    s.alu0_dispatch_rdy      = InPort ( 1 )
    s.alu0_dispatch_inst     = OutPort( 32 )
    s.alu0_dispatch_rob_tag  = OutPort( p_rob_tag_nbits )
    s.alu0_dispatch_rs1_addr = OutPort( p_prf_addr_nbits )
    s.alu0_dispatch_rs2_addr = OutPort( p_prf_addr_nbits )
    s.alu0_dispatch_rd_addr  = OutPort( p_prf_addr_nbits )
    s.alu0_dispatch_rd_valid = OutPort( 1 )

    s.alu1_dispatch_val      = OutPort( 1 )
    s.alu1_dispatch_rdy      = InPort ( 1 )
    s.alu1_dispatch_inst     = OutPort( 32 )
    s.alu1_dispatch_rob_tag  = OutPort( p_rob_tag_nbits )
    s.alu1_dispatch_rs1_addr = OutPort( p_prf_addr_nbits )
    s.alu1_dispatch_rs2_addr = OutPort( p_prf_addr_nbits )
    s.alu1_dispatch_rd_addr  = OutPort( p_prf_addr_nbits )
    s.alu1_dispatch_rd_valid = OutPort( 1 )

    s.mul_dispatch_val      = OutPort( 1 )
    s.mul_dispatch_rdy      = InPort ( 1 )
    s.mul_dispatch_inst     = OutPort( 32 )
    s.mul_dispatch_rob_tag  = OutPort( p_rob_tag_nbits )
    s.mul_dispatch_rs1_addr = OutPort( p_prf_addr_nbits )
    s.mul_dispatch_rs2_addr = OutPort( p_prf_addr_nbits )
    s.mul_dispatch_rd_addr  = OutPort( p_prf_addr_nbits )
    s.mul_dispatch_rd_valid = OutPort( 1 )

    s.mem_dispatch_val      = OutPort( 1 )
    s.mem_dispatch_rdy      = InPort ( 1 )
    s.mem_dispatch_inst     = OutPort( 32 )
    s.mem_dispatch_rob_tag  = OutPort( p_rob_tag_nbits )
    s.mem_dispatch_rs1_addr = OutPort( p_prf_addr_nbits )
    s.mem_dispatch_rs2_addr = OutPort( p_prf_addr_nbits )
    s.mem_dispatch_rd_addr  = OutPort( p_prf_addr_nbits )
    s.mem_dispatch_rd_valid = OutPort( 1 )

    s.rf_wen_alu0   = InPort ( 1 )
    s.rf_waddr_alu0 = InPort ( p_prf_addr_nbits )
    s.rf_wen_alu1   = InPort ( 1 )
    s.rf_waddr_alu1 = InPort ( p_prf_addr_nbits )
    s.rf_wen_mul    = InPort ( 1 )
    s.rf_waddr_mul  = InPort ( p_prf_addr_nbits )
    s.rf_wen_mem    = InPort ( 1 )
    s.rf_waddr_mem  = InPort ( p_prf_addr_nbits )
