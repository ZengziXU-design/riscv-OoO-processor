#=========================================================================
# ProcPreDecode PyMTL Wrapper
#=========================================================================

from pymtl3 import *
from pymtl3.passes.backends.verilog import *

class ProcPreDecode( VerilogPlaceholder, Component ):
  def construct( s ):
    # Inputs
    s.inst      = InPort ( 32 )

    # Outputs: Unpacked Addresses
    s.rs1_addr  = OutPort( 5 )
    s.rs2_addr  = OutPort( 5 )
    s.rd_addr   = OutPort( 5 )

    # Outputs: Valid Bits
    s.rs1_valid = OutPort( 1 )
    s.rs2_valid = OutPort( 1 )
    s.rd_valid  = OutPort( 1 )

    # Outputs: Instruction-class flags
    #   is_csr -> opcode == 7'b1110011  (CSRR / CSRW)
    #   is_mem -> opcode == 7'b0000011 (LW) || 7'b0100011 (SW)
    s.is_csr    = OutPort( 1 )
    s.is_mem    = OutPort( 1 )
    s.is_mul    = OutPort( 1 )
