#=========================================================================
# OoO_SingleCoreSysFL
#=========================================================================
# FL system: ProcFL + ICache (4B) + DCache (4B) wired to a 16B-wide
# memory bus, plus a NullXcelFL stub on the proc's xcel port.
#
# ProcFL was originally designed for a system that includes an
# accelerator and a multi-core core_id input. We instantiate the
# standard NullXcelFL stub for the xcel interface — this matches what
# proj3.test.harness.TestHarness already does, so xcel-related tests
# (e.g. inst_xcel) work identically at the unit-test and system levels.
# core_id is tied to 0 because this is a single-core system.

from pymtl3 import *

from pymtl3.stdlib.stream.ifcs import IStreamIfc, OStreamIfc
from pymtl3.stdlib.mem.ifcs    import MemRequesterIfc
from pymtl3.stdlib.mem         import mk_mem_msg

from proj3.ProcFL       import ProcFL
from proj3.NullXcelFL   import NullXcelFL
from cache.ICache4B     import ICache4B
from cache.DCache4B     import DCache4B


class OoO_SingleCoreSysFL( Component ):

  def construct( s ):

    # Memory bus is 16B-wide (a cache line per transaction).
    MemReqType, MemRespType = mk_mem_msg( 8, 32, 128 )

    #---------------------------------------------------------------------
    # External Interface
    #---------------------------------------------------------------------

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

    #---------------------------------------------------------------------
    # Components
    #---------------------------------------------------------------------

    s.proc      = ProcFL()
    s.icache    = ICache4B()
    s.dcache    = DCache4B()
    s.xcel_stub = NullXcelFL()

    # Single-core: core_id is hardwired to 0.
    s.proc.core_id //= 0

    #---------------------------------------------------------------------
    # Connections
    #---------------------------------------------------------------------

    # mngr <-> proc
    s.mngr2proc //= s.proc.mngr2proc
    s.proc2mngr //= s.proc.proc2mngr

    # proc <-> xcel stub
    # ProcFL.xcel is a Requester, NullXcelFL.xcel is a Responder;
    # PyMTL connects the matching streams in both directions.
    s.proc.xcel //= s.xcel_stub.xcel

    # proc <-> caches  (32-bit data on this side)
    s.proc.imem //= s.icache.proc2cache
    s.proc.dmem //= s.dcache.proc2cache

    # caches <-> memory  (128-bit data on this side)
    s.imem //= s.icache.cache2mem
    s.dmem //= s.dcache.cache2mem

    #---------------------------------------------------------------------
    # Stats / debug outputs
    #---------------------------------------------------------------------

    s.stats_en      //= s.proc.stats_en
    s.commit_inst   //= s.proc.commit_inst

    # The placeholder caches do not expose access/miss counters yet,
    # so we tie these to 0 at the system boundary.
    s.icache_access //= 0
    s.icache_miss   //= 0
    s.dcache_access //= 0
    s.dcache_miss   //= 0

  def line_trace( s ):
    return s.proc.line_trace()