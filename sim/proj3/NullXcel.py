#=========================================================================
# NullXcel PyMTL Wrapper
#=========================================================================

from pymtl3 import *
from pymtl3.passes.backends.verilog import *
from pymtl3.stdlib.xcel      import XcelMsgType, mk_xcel_msg
from pymtl3.stdlib.xcel.ifcs import XcelResponderIfc

class NullXcel( VerilogPlaceholder, Component ):
  def construct( s ):

    XcelReqMsg, XcelRespMsg = mk_xcel_msg( 5, 32 )

    s.xcel = XcelResponderIfc( XcelReqMsg, XcelRespMsg )

