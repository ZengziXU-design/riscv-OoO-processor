#=========================================================================
# test_harness
#=========================================================================
# Includes a test harness that composes a processor, src/sink, and test
# memory, and a run_test function.

import struct

from pymtl3 import *

from pymtl3.stdlib.mem import MemoryFL, mk_mem_msg, MemMsgType
from pymtl3.stdlib.stream import StreamSourceFL, StreamSinkFL
from pymtl3.stdlib.test_utils import run_sim

from proj3.tinyrv2_encoding import assemble

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
# SingleCoreTestHarness
#=========================================================================

class SingleCoreTestHarness(Component):

  #-----------------------------------------------------------------------
  # constructor
  #-----------------------------------------------------------------------

  def construct( s, Sys ):
    s.commit_inst = OutPort()

    s.src  = StreamSourceFL( Bits32, [] )
    s.sink = StreamSinkFL( Bits32, [] )
    s.sys  = Sys()

    s.mem  = MemoryFL(2, mem_ifc_dtypes=[mk_mem_msg(8,32,128),mk_mem_msg(8,32,128)] )

    s.sys.commit_inst //= s.commit_inst

    # System <-> Proc/Mngr

    s.src.ostream   //= s.sys.mngr2proc
    s.sys.proc2mngr //= s.sink.istream

    # System <-> Memory

    s.sys.imem //= s.mem.ifc[0]
    s.sys.dmem //= s.mem.ifc[1]

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

    imem_reqstr = "  "
    if s.mem.ifc[0].reqstream.val and s.mem.ifc[0].reqstream.rdy:
      imem_reqstr = MemMsgType.str[int(s.mem.ifc[0].reqstream.msg.type_)]

    imem_respstr = "  "
    if s.mem.ifc[0].respstream.val and s.mem.ifc[0].respstream.rdy:
      imem_respstr = MemMsgType.str[int(s.mem.ifc[0].respstream.msg.type_)]

    imem_str = "     "
    if imem_reqstr != "  " or imem_respstr != "  ":
      imem_str = f"{imem_reqstr}>{imem_respstr}"

    dmem_reqstr = "  "
    if s.mem.ifc[1].reqstream.val and s.mem.ifc[1].reqstream.rdy:
      dmem_reqstr = MemMsgType.str[int(s.mem.ifc[1].reqstream.msg.type_)]

    dmem_respstr = "  "
    if s.mem.ifc[1].respstream.val and s.mem.ifc[1].respstream.rdy:
      dmem_respstr = MemMsgType.str[int(s.mem.ifc[1].respstream.msg.type_)]

    dmem_str = "     "
    if dmem_reqstr != "  " or dmem_respstr != "  ":
      dmem_str = f"{dmem_reqstr}>{dmem_respstr}"

    mem_str = f"{imem_str}|{dmem_str}"

    return s.src.line_trace()  + " >" + \
           ("*" if s.sys.stats_en else " ") + \
           s.sys.line_trace() + " " + \
           mem_str + " > " + \
           s.sink.line_trace()

#=========================================================================
# run_test
#=========================================================================

def run_score_test( Sys, gen_test, delays=False, cmdline_opts=None ):

  # Instantiate model

  th = SingleCoreTestHarness( Sys )

  # Set parameters

  if delays:

    th.set_param( "top.src.construct",
                     initial_delay=0, interval_delay=20,
                     interval_delay_mode='random' )

    th.set_param( "top.sink.construct",
                     initial_delay=0, interval_delay=20,
                     interval_delay_mode='random' )

    th.set_param( "top.mem.construct",
                     stall_prob=0.5, extra_latency=3 )

  th.elaborate()

  asm_prog = None
  if isinstance( gen_test, str ):
    asm_prog = gen_test
  else:
    asm_prog = gen_test()

  # print(asm_prog)
  mem_image = assemble( asm_prog )
  th.load( mem_image )

  run_sim( th, cmdline_opts, duts=['sys'] )

#=========================================================================
# MultiCoreTestHarness
#=========================================================================

class MultiCoreTestHarness(Component):

  #-----------------------------------------------------------------------
  # constructor
  #-----------------------------------------------------------------------

  def construct( s, Sys ):
    s.commit_inst = OutPort()

    s.srcs  = [ StreamSourceFL( Bits32, [] ) for _ in range(4) ]
    s.sinks = [ StreamSinkFL( Bits32, [] )   for _ in range(4) ]
    s.sys   = Sys()

    s.mem  = MemoryFL(2, mem_ifc_dtypes=[mk_mem_msg(8,32,128),mk_mem_msg(8,32,128)] )

    s.sys.commit_inst //= s.commit_inst

    # System <-> Proc/Mngr

    for i in range(4):
      s.srcs[i].ostream  //= s.sys.mngr2proc[i]
      s.sys.proc2mngr[i] //= s.sinks[i].istream

    # System <-> Memory

    s.sys.imem //= s.mem.ifc[0]
    s.sys.dmem //= s.mem.ifc[1]

  #-----------------------------------------------------------------------
  # load
  #-----------------------------------------------------------------------

  def load( self, mem_image ):

    # Iterate over the sections

    sections = mem_image.get_sections()
    for section in sections:

      # For .mngr2proc sections, copy section into mngr2proc src

      if section.name == ".mngr2proc":
        for i in range(4):
          for bits in struct.iter_unpack("<I", section.data):
            self.srcs[i].msgs.append( b32(bits[0]) )

      elif section.name.startswith(".mngr2proc_"):
        idx = int( section.name.split("_")[1] )
        for bits in struct.iter_unpack("<I", section.data):
          self.srcs[idx].msgs.append( b32(bits[0]) )

      # For .proc2mngr sections, copy section into proc2mngr_ref src

      elif section.name == ".proc2mngr":
        for i in range(4):
          for bits in struct.iter_unpack("<I", section.data):
            self.sinks[i].msgs.append( b32(bits[0]) )

      elif section.name.startswith(".proc2mngr_"):
        idx = int( section.name.split("_")[1] )
        for bits in struct.iter_unpack("<I", section.data):
          self.sinks[idx].msgs.append( b32(bits[0]) )

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
    for i in range(4):
      if not s.srcs[i].done() or not s.sinks[i].done():
        return False
    return True

  #-----------------------------------------------------------------------
  # line_trace
  #-----------------------------------------------------------------------

  def line_trace( s ):

    imem_reqstr = "  "
    if s.mem.ifc[0].reqstream.val and s.mem.ifc[0].reqstream.rdy:
      imem_reqstr = MemMsgType.str[int(s.mem.ifc[0].reqstream.msg.type_)]

    imem_respstr = "  "
    if s.mem.ifc[0].respstream.val and s.mem.ifc[0].respstream.rdy:
      imem_respstr = MemMsgType.str[int(s.mem.ifc[0].respstream.msg.type_)]

    imem_str = "     "
    if imem_reqstr != "  " or imem_respstr != "  ":
      imem_str = f"{imem_reqstr}>{imem_respstr}"

    dmem_reqstr = "  "
    if s.mem.ifc[1].reqstream.val and s.mem.ifc[1].reqstream.rdy:
      dmem_reqstr = MemMsgType.str[int(s.mem.ifc[1].reqstream.msg.type_)]

    dmem_respstr = "  "
    if s.mem.ifc[1].respstream.val and s.mem.ifc[1].respstream.rdy:
      dmem_respstr = MemMsgType.str[int(s.mem.ifc[1].respstream.msg.type_)]

    dmem_str = "     "
    if dmem_reqstr != "  " or dmem_respstr != "  ":
      dmem_str = f"{dmem_reqstr}>{dmem_respstr}"

    mem_str = f"{imem_str}|{dmem_str}"

    srcs_str  = "|".join([ src.line_trace()  for src  in s.srcs  ])
    sinks_str = "|".join([ sink.line_trace() for sink in s.sinks ])

    return srcs_str + " >" + \
           ("*" if s.sys.stats_en else " ") + \
           s.sys.line_trace() + " " + \
           mem_str + " > " + \
           sinks_str

#=========================================================================
# run_test
#=========================================================================

def run_mcore_test( Sys, gen_test, delays=False, cmdline_opts=None ):

  # Instantiate model

  th = MultiCoreTestHarness( Sys )

  # Set parameters

  if delays:

    th.set_param( "top.src.construct",
                     initial_delay=0, interval_delay=20,
                     interval_delay_mode='random' )

    th.set_param( "top.sink.construct",
                     initial_delay=0, interval_delay=20,
                     interval_delay_mode='random' )

    th.set_param( "top.mem.construct",
                     stall_prob=0.5, extra_latency=3 )

  th.elaborate()

  asm_prog = None
  if isinstance( gen_test, str ):
    asm_prog = gen_test
  else:
    asm_prog = gen_test()

  # print(asm_prog)
  mem_image = assemble( asm_prog )
  th.load( mem_image )

  run_sim( th, cmdline_opts, duts=['sys'] )
