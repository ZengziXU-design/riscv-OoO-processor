#=========================================================================
# ReadDataUnit
#=========================================================================

from pymtl3 import *
from pymtl3.passes.backends.verilog import *

class ReadDataUnit( VerilogPlaceholder, Component ):
  def construct( s ):
    s.in_    = InPort(128)
    s.type_  = InPort(4)
    s.len    = InPort(4)
    s.offset = InPort(4)
    s.out    = OutPort(128)

