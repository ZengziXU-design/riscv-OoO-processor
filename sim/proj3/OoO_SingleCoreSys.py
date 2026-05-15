#=========================================================================
# Single Core System PyMTL Wrapper
#=========================================================================

from pymtl3 import *
from pymtl3.passes.backends.verilog import *
from pymtl3.stdlib.stream.ifcs import IStreamIfc, OStreamIfc
from pymtl3.stdlib.mem.ifcs    import MemRequesterIfc
from pymtl3.stdlib.mem         import mk_mem_msg

class OoO_SingleCoreSys( VerilogPlaceholder, Component ):
  def construct( s ):

    MemReqType, MemRespType = mk_mem_msg( 8, 32, 128 )

    s.mngr2proc     = IStreamIfc( Bits32 )
    s.proc2mngr     = OStreamIfc( Bits32 )
    s.imem          = MemRequesterIfc( MemReqType, MemRespType )
    s.dmem          = MemRequesterIfc( MemReqType, MemRespType )

    s.stats_en      = OutPort()
    s.commit_inst   = OutPort()
    s.icache_access = OutPort()
    s.icache_miss   = OutPort()
    s.dcache_access = OutPort()
    s.dcache_miss   = OutPort()
