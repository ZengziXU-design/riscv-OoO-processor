#=========================================================================
# Blocking Cache FL Model
#=========================================================================
# A function level cache model which only passes cache requests and
# responses to the memory.

from pymtl3 import *
from pymtl3.stdlib.stream      import IStreamDeqAdapterFL, OStreamEnqAdapterFL
from pymtl3.stdlib.mem.ifcs    import MemRequesterIfc, MemResponderIfc
from pymtl3.stdlib.mem         import mk_mem_msg, MemMsgType, MemRequesterAdapterFL

class CacheFL( Component ):

  def construct( s ):

    # Interface

    MemReqMsg16B, MemRespMsg16B = mk_mem_msg( 8, 32, 128 )

    s.proc2cache = MemResponderIfc( MemReqMsg16B, MemRespMsg16B )
    s.cache2mem  = MemRequesterIfc( MemReqMsg16B, MemRespMsg16B )

    # Proc <-> Cache Adapters

    s.cache_reqstream_q  = IStreamDeqAdapterFL( MemReqMsg16B  )
    s.cache_respstream_q = OStreamEnqAdapterFL( MemRespMsg16B )

    connect( s.proc2cache.reqstream, s.cache_reqstream_q.istream   )
    connect( s.cache_respstream_q.ostream, s.proc2cache.respstream )

    # Cache <-> Memory Adapters

    s.mem_adapter = MemRequesterAdapterFL( MemReqMsg16B, MemRespMsg16B )

    connect( s.cache2mem, s.mem_adapter.requester )

    # Logic

    @update_once
    def logic():

      # Process cache request if input and output stream are both ready

      if s.cache_reqstream_q.deq.rdy() and s.cache_respstream_q.enq.rdy():

        # Dequeue cache request

        cachereq = s.cache_reqstream_q.deq()

        # By default the read data is always zero (i.e., for writes)

        data = Bits128(0)

        # Handle write transactions

        if (    ( cachereq.type_ == MemMsgType.WRITE_INIT )
             or ( cachereq.type_ == MemMsgType.WRITE ) ):
          s.mem_adapter.write( cachereq.addr, cachereq.len, cachereq.data )

        # Handle read transactions

        elif ( cachereq.type_ == MemMsgType.READ ):
          data = s.mem_adapter.read( cachereq.addr, cachereq.len )

          # Make sure response data is 128b

          if data.nbits < 128:
            data = zext(data,128)

        # Create appropriate cache response

        cacheresp = MemRespMsg16B( cachereq.type_, cachereq.opaque,
                                   Bits2(0), cachereq.len, data )

        # Enqueue cache response on output stream

        s.cache_respstream_q.enq( cacheresp )

  def line_trace(s):
    return "()"

