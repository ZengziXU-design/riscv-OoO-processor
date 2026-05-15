#=========================================================================
# test_harness
#=========================================================================
# Includes a test harness that composes a processor, src/sink, and test
# memory, and a run_test function.

import struct

from pymtl3 import *

from pymtl3.stdlib.mem import MemoryFL, mk_mem_msg
from pymtl3.stdlib.xcel import mk_xcel_msg
from pymtl3.stdlib.stream import StreamSourceFL, StreamSinkFL
from pymtl3.stdlib.test_utils import run_sim

from proj3.tinyrv2_encoding import assemble
from proj3.NullXcelFL import NullXcelFL

#=========================================================================
# TestHarness
#=========================================================================
# Use this with pytest parameterize so that the name of the function that
# generates the assembly test ends up as part of the actual test case
# name. Here is an example:
#
#  @pytest.mark.parametrize( "name,gen_test", [
#    asm_test( gen_basic_test  ),
#    asm_test( gen_bypass_test ),
#    asm_test( gen_value_test  ),
#  ])
#  def test( name, gen_test ):
#    run_test( ProcXFL, gen_test )
#

def asm_test( func ):
  name = func.__name__
  if name.startswith("gen_"):
    name = name[4:]
  if name.endswith("_test"):
    name = name[:-5]

  return (name,func)

#=========================================================================
# TestHarness
#=========================================================================

class TestHarness(Component):

  #-----------------------------------------------------------------------
  # constructor
  #-----------------------------------------------------------------------

  def construct( s, ProcType ):

    s.commit_inst = OutPort()

    s.src  = StreamSourceFL( Bits32, [] )
    s.sink = StreamSinkFL( Bits32, [] )
    s.proc = ProcType()
    s.xcel = NullXcelFL()
    s.mem  = MemoryFL(2, mem_ifc_dtypes=2*[mk_mem_msg(8,32,32)] )

    s.proc.commit_inst //= s.commit_inst

    # Processor <-> Proc/Mngr
    s.src.ostream    //= s.proc.mngr2proc
    s.proc.proc2mngr //= s.sink.istream

    # Processor <-> Memory
    s.proc.imem //= s.mem.ifc[0]
    s.proc.dmem //= s.mem.ifc[1]

    # Processor <-> Xcel
    s.proc.xcel //= s.xcel.xcel

    # Starting F16 we turn core_id into input ports to
    # enable module reusability. In the past it was passed as arguments.
    s.proc.core_id //= 0

  #-----------------------------------------------------------------------
  # load
  #-----------------------------------------------------------------------

  def load( self, mem_image ):

    # Iterate over the sections

    sections = mem_image.get_sections()
    for section in sections:

      # For .mngr2proc sections, copy section into mngr2proc src

      if section.name == ".mngr2proc":
        for bits in struct.iter_unpack("<I", section.data):
          self.src.msgs.append( b32(bits[0]) )

      # For .proc2mngr sections, copy section into proc2mngr_ref src

      elif section.name == ".proc2mngr":
        for bits in struct.iter_unpack("<I", section.data):
          self.sink.msgs.append( b32(bits[0]) )

      # For all other sections, simply copy them into the memory

      else:
        start_addr = section.addr
        stop_addr  = section.addr + len(section.data)
        self.mem.mem.mem[start_addr:stop_addr] = section.data

  #-----------------------------------------------------------------------
  # cleanup
  #-----------------------------------------------------------------------

  def cleanup( s ):
    del s.mem.mem[:]

  #-----------------------------------------------------------------------
  # done
  #-----------------------------------------------------------------------

  def done( s ):
    return s.src.done() and s.sink.done()

  #-----------------------------------------------------------------------
  # line_trace
  #-----------------------------------------------------------------------

  def line_trace( s ):
    return s.src.line_trace()  + " >" + \
           ("- " if s.proc.stats_en else "  ") + \
           s.proc.line_trace() + "|" + \
           s.xcel.line_trace() + "|" + \
           s.mem.line_trace()  + " > " + \
           s.sink.line_trace()

#=========================================================================
# run_test
#=========================================================================

def run_test( ProcModel, gen_test, delays=False, cmdline_opts=None ):

  # Instantiate model

  model = TestHarness( ProcModel )

  # Set parameters

  if delays:

    model.set_param( "top.src.construct",
                     initial_delay=0, interval_delay=20,
                     interval_delay_mode='random' )

    model.set_param( "top.sink.construct",
                     initial_delay=0, interval_delay=20,
                     interval_delay_mode='random' )

    model.set_param( "top.mem.construct",
                     stall_prob=0.5, extra_latency=3 )

  model.elaborate()

  asm_prog = None
  if isinstance( gen_test, str ):
    asm_prog = gen_test
  else:
    asm_prog = gen_test()

  # print(asm_prog)
  mem_image = assemble( asm_prog )
  model.load( mem_image )

  run_sim( model, cmdline_opts, duts=['proc'] )
