#=========================================================================
# Cache
#=========================================================================

from pymtl3 import *
from pymtl3.passes.backends.verilog import *
from pymtl3.stdlib.mem.ifcs    import MemRequesterIfc, MemResponderIfc
from pymtl3.stdlib.mem         import mk_mem_msg

class Cache( VerilogPlaceholder, Component ):
  def construct( s ):

    MemReqMsg16B, MemRespMsg16B = mk_mem_msg( 8, 32, 128 )

    s.proc2cache = MemResponderIfc( MemReqMsg16B, MemRespMsg16B )
    s.cache2mem  = MemRequesterIfc( MemReqMsg16B, MemRespMsg16B )

