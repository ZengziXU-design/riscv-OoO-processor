#=========================================================================
# ProcPregfile PyMTL Wrapper
#=========================================================================

from pymtl3 import *
from pymtl3.passes.backends.verilog import *

class ProcPregfile( VerilogPlaceholder, Component ):
  def construct( s ):
    # --------------------------------------------------
    # Read port 0
    # --------------------------------------------------
    s.rd_addr0 = InPort ( 6 )
    s.rd_data0 = OutPort( 32 )

    # --------------------------------------------------
    # Read port 1
    # --------------------------------------------------
    s.rd_addr1 = InPort ( 6 )
    s.rd_data1 = OutPort( 32 )

    # --------------------------------------------------
    # Write port 0  (ALU / CSR  - X stage)
    # --------------------------------------------------
    s.wr_en0   = InPort ( 1 )
    s.wr_addr0 = InPort ( 6 )
    s.wr_data0 = InPort ( 32 )

    # --------------------------------------------------
    # Write port 1  (MUL  - Y3 stage)
    # --------------------------------------------------
    s.wr_en1   = InPort ( 1 )
    s.wr_addr1 = InPort ( 6 )
    s.wr_data1 = InPort ( 32 )

    # --------------------------------------------------
    # Write port 2  (LW response from MemUnit  - M stage)
    # --------------------------------------------------
    s.wr_en2   = InPort ( 1 )
    s.wr_addr2 = InPort ( 6 )
    s.wr_data2 = InPort ( 32 )