#=========================================================================
# SRAM.py
#=========================================================================

from pymtl3 import *
from pymtl3.passes.backends.verilog import *

class SRAM( VerilogPlaceholder, Component ):

  # removed mask_size=0 parameter for now

  def construct( s, p_num_entries=256, p_data_nbits=32 ):

    s.port0_val   = InPort ()
    s.port0_type  = InPort ()
    s.port0_idx   = InPort ( clog2(p_num_entries) )
    s.port0_wben  = InPort ( p_data_nbits//8 )
    s.port0_wdata = InPort ( p_data_nbits )
    s.port0_rdata = OutPort( p_data_nbits )

    # if mask_size > 0:
    #   s.port0_wben = InPort( mk_bits(mask_size) )

