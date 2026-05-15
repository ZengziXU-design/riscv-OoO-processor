#=========================================================================
# Proc PyMTL Wrapper
#=========================================================================

from pymtl3 import *
from pymtl3.passes.backends.verilog import *
from pymtl3.stdlib.stream.ifcs import IStreamIfc, OStreamIfc
from pymtl3.stdlib.mem.ifcs    import MemRequesterIfc
from pymtl3.stdlib.mem         import mk_mem_msg
from pymtl3.stdlib.xcel.ifcs   import XcelRequesterIfc
from pymtl3.stdlib.xcel        import mk_xcel_msg

class ProcOoO( VerilogPlaceholder, Component ):
  def construct( s ):

    MemReqMsg,  MemRespMsg  = mk_mem_msg( 8, 32, 32 )
    XcelReqMsg, XcelRespMsg = mk_xcel_msg( 5, 32 )

    s.mngr2proc   = IStreamIfc( Bits32 )
    s.proc2mngr   = OStreamIfc( Bits32 )

    s.xcel        = XcelRequesterIfc( XcelReqMsg, XcelRespMsg )

    s.imem        = MemRequesterIfc( MemReqMsg, MemRespMsg )
    s.dmem        = MemRequesterIfc( MemReqMsg, MemRespMsg )

    s.core_id     = InPort(32)
    s.commit_inst = OutPort()
    s.stats_en    = OutPort()

