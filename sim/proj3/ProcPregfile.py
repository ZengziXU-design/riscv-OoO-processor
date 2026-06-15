#=========================================================================
# ProcPregfile PyMTL Wrapper
#=========================================================================

from pymtl3 import *
from pymtl3.passes.backends.verilog import *

class ProcPregfile( VerilogPlaceholder, Component ):
  def construct( s ):
    # --------------------------------------------------
    # Read ports for issue slot 0
    # --------------------------------------------------
    s.rd_addr_issue0_rs1 = InPort ( 6 )
    s.rd_data_issue0_rs1 = OutPort( 32 )

    s.rd_addr_issue0_rs2 = InPort ( 6 )
    s.rd_data_issue0_rs2 = OutPort( 32 )

    # --------------------------------------------------
    # Read ports for issue slot 1
    # --------------------------------------------------
    s.rd_addr_issue1_rs1 = InPort ( 6 )
    s.rd_data_issue1_rs1 = OutPort( 32 )

    s.rd_addr_issue1_rs2 = InPort ( 6 )
    s.rd_data_issue1_rs2 = OutPort( 32 )

    # --------------------------------------------------
    # Write port for ALU0 / CSR
    # --------------------------------------------------
    s.wr_en_alu0   = InPort ( 1 )
    s.wr_addr_alu0 = InPort ( 6 )
    s.wr_data_alu0 = InPort ( 32 )

    # --------------------------------------------------
    # Write port for ALU1
    # --------------------------------------------------
    s.wr_en_alu1   = InPort ( 1 )
    s.wr_addr_alu1 = InPort ( 6 )
    s.wr_data_alu1 = InPort ( 32 )

    # --------------------------------------------------
    # Write port for MUL
    # --------------------------------------------------
    s.wr_en_mul   = InPort ( 1 )
    s.wr_addr_mul = InPort ( 6 )
    s.wr_data_mul = InPort ( 32 )

    # --------------------------------------------------
    # Write port for memory response data
    # --------------------------------------------------
    s.wr_en_mem   = InPort ( 1 )
    s.wr_addr_mem = InPort ( 6 )
    s.wr_data_mem = InPort ( 32 )
