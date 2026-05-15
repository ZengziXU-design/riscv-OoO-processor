#=========================================================================
# WriteDataUnit
#=========================================================================

from pymtl3 import *
from pymtl3.passes.backends.verilog import *

class WriteDataUnit( VerilogPlaceholder, Component ):
  def construct( s ):
    s.in_    = InPort(128)
    s.len    = InPort(4)
    s.offset = InPort(4)
    s.wben   = OutPort(16)
    s.out    = OutPort(128)

