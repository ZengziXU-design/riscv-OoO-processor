#=========================================================================
# ProcMemunit PyMTL Wrapper
#=========================================================================
# Wraps the proj3_MemUnit single-stage memory unit. The Verilog top module
# is `proj3_MemUnit` (no "Proc" prefix), so this Python class is named to
# match. The file name still follows the project's `Proc*` file convention.

from pymtl3 import *
from pymtl3.passes.backends.verilog import *

class MemUnit( VerilogPlaceholder, Component ):
  def construct( s, p_paddr_nbits=6, p_rob_nbits=3 ):

    # --------------------------------------------------------------------
    # istream  (from IQ / Issue stage)
    # --------------------------------------------------------------------
    s.istream_val      = InPort ( 1 )
    s.istream_rdy      = OutPort( 1 )

    # Feedback to IQ scheduler: can MemUnit accept a mem inst this cycle?
    s.mem_issue_rdy    = OutPort( 1 )

    s.istream_base     = InPort ( 32 )
    s.istream_imm      = InPort ( 32 )
    s.istream_rd_paddr = InPort ( p_paddr_nbits )
    s.istream_rob_idx  = InPort ( p_rob_nbits )
    s.istream_is_sw    = InPort ( 1 )            # 0 for lw, 1 for sw
    s.istream_sw_data  = InPort ( 32 )

    # --------------------------------------------------------------------
    # dmem request channel
    # --------------------------------------------------------------------
    s.dmem_reqstream_val      = OutPort( 1 )
    s.dmem_reqstream_rdy      = InPort ( 1 )
    s.dmem_reqstream_msg_addr = OutPort( 32 )
    s.dmem_reqstream_msg_data = OutPort( 32 )
    s.dmem_reqstream_msg_type = OutPort( 3 )    # 0 = READ, 1 = WRITE

    # --------------------------------------------------------------------
    # dmem response channel
    # --------------------------------------------------------------------
    s.dmem_respstream_val      = InPort ( 1 )
    s.dmem_respstream_rdy      = OutPort( 1 )
    s.dmem_respstream_msg_data = InPort ( 32 )

    # --------------------------------------------------------------------
    # ostream  (writeback to PRF write-port-2 + ROB wb2)
    # --------------------------------------------------------------------
    s.ostream_val      = OutPort( 1 )
    s.ostream_rdy      = InPort ( 1 )
    s.ostream_rf_wen   = OutPort( 1 )            # 0 for sw (no PRF write)
    s.ostream_data     = OutPort( 32 )
    s.ostream_rd_paddr = OutPort( p_paddr_nbits )
    s.ostream_rob_idx  = OutPort( p_rob_nbits )