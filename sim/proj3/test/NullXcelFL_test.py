#=========================================================================
# NullXcelFL_test
#=========================================================================

import pytest
import random
import struct

random.seed(0xdeadbeef)

from pymtl3 import *
from pymtl3.stdlib.test_utils import mk_test_case_table, run_sim
from pymtl3.stdlib.stream     import StreamSourceFL, StreamSinkFL
from pymtl3.stdlib.xcel       import XcelMsgType, mk_xcel_msg

from proj3.NullXcelFL import NullXcelFL

XcelReqMsg, XcelRespMsg = mk_xcel_msg( 5, 32 )

#-------------------------------------------------------------------------
# TestHarness
#-------------------------------------------------------------------------

class TestHarness( Component ):

  def construct( s, NullXcelType ):

    s.src  = StreamSourceFL( XcelReqMsg )
    s.xcel = NullXcelType
    s.sink = StreamSinkFL( XcelRespMsg )

    s.src.ostream  //= s.xcel.xcel.reqstream
    s.sink.istream //= s.xcel.xcel.respstream

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return s.src.line_trace()  + " > " + \
           s.xcel.line_trace() + " > " + \
           s.sink.line_trace()

#-------------------------------------------------------------------------
# make messages
#-------------------------------------------------------------------------

def xreq( type_, raddr, data ):
  if type_ == 'rd':
    return XcelReqMsg( XcelMsgType.READ, raddr, data )
  else:
    return XcelReqMsg( XcelMsgType.WRITE, raddr, data )

def xresp( type_, data ):
  if type_ == 'rd':
    return XcelRespMsg( XcelMsgType.READ, data )
  else:
    return XcelRespMsg( XcelMsgType.WRITE, data )

#-------------------------------------------------------------------------
# Test Case: basic
#-------------------------------------------------------------------------

basic_msgs = [
  xreq( 'wr', 0, 0xa  ), xresp( 'wr', 0x0 ),
  xreq( 'rd', 0, 0x0  ), xresp( 'rd', 0xa ),
]

#-------------------------------------------------------------------------
# Test Case: stream
#-------------------------------------------------------------------------

stream_msgs = [
  xreq( 'wr', 0, 0xa  ), xresp( 'wr', 0x0 ),
  xreq( 'wr', 0, 0xb  ), xresp( 'wr', 0x0 ),
  xreq( 'rd', 0, 0x0  ), xresp( 'rd', 0xb ),
  xreq( 'wr', 0, 0xc  ), xresp( 'wr', 0x0 ),
  xreq( 'wr', 0, 0xd  ), xresp( 'wr', 0x0 ),
  xreq( 'rd', 0, 0x0  ), xresp( 'rd', 0xd ),
]

#-------------------------------------------------------------------------
# Test Case: random
#-------------------------------------------------------------------------

random.seed(0xdeadbeef)
random_msgs = []
for i in range(20):
  data = random.randint(0,0xffffffff)
  random_msgs.extend([ xreq( 'wr', 0, data ), xresp( 'wr', 0,   ) ])
  random_msgs.extend([ xreq( 'rd', 0, 0    ), xresp( 'rd', data ) ])

#-------------------------------------------------------------------------
# Test Case Table
#-------------------------------------------------------------------------

test_case_table = mk_test_case_table([
  (              "msgs         src_delay sink_delay"),
  [ "basic",      basic_msgs,  0,        0,   ],
  [ "stream",     stream_msgs, 0,        0,   ],
  [ "random_0x0", random_msgs, 0,        0,   ],
  [ "random_5x0", random_msgs, 5,        0,   ],
  [ "random_0x5", random_msgs, 0,        5,   ],
  [ "random_3x9", random_msgs, 3,        9,   ],
])

#-------------------------------------------------------------------------
# Test cases
#-------------------------------------------------------------------------

@pytest.mark.parametrize( **test_case_table )
def test( cmdline_opts, test_params ):

  th = TestHarness( NullXcelFL() )

  th.set_param("top.src.construct",
    msgs=test_params.msgs[::2],
    initial_delay=test_params.src_delay+3,
    interval_delay=test_params.src_delay )

  th.set_param("top.sink.construct",
    msgs=test_params.msgs[1::2],
    initial_delay=test_params.sink_delay+3,
    interval_delay=test_params.sink_delay )

  run_sim( th, cmdline_opts, duts=['xcel'] )
