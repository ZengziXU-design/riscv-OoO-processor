#=========================================================================
# CacheFL_subword_test.py
#=========================================================================

import pytest

from random import seed, randint, choice

from pymtl3 import *
from pymtl3.stdlib.mem        import MemMsgType
from pymtl3.stdlib.test_utils import mk_test_case_table

from cache.test.harness import req, resp, run_test
from cache.CacheFL      import CacheFL

seed(0xa4e28cc2)

#-------------------------------------------------------------------------
# cmp_wo_test_field
#-------------------------------------------------------------------------
# The test field in the cache response is used to indicate if the
# corresponding memory access resulted in a hit or a miss. However, the
# FL model always sets the test field to zero since it does not track
# hits/misses. So we need to do something special to ignore the test
# field when using the FL model. To do this, we can pass in a specialized
# comparison function to the StreamSinkFL.

def cmp_wo_test_field( msg, ref ):

  if msg.type_ != ref.type_:
    return False

  if msg.len != ref.len:
    return False

  if msg.opaque != msg.opaque:
    return False

  if ref.data != msg.data:
    return False

  # do not check the test field

  return True

#-------------------------------------------------------------------------
# Data
#-------------------------------------------------------------------------
# These functions are used to specify the address/data to preload into
# the main memory before running a test.

# 64B of sequential data

def data_64B():
  return [
    # addr      data
    0x00001000, 0x03020100,
    0x00001004, 0x07060504,
    0x00001008, 0x0b0a0908,
    0x0000100c, 0x0f0e0d0c,
    0x00001010, 0x13121110,
    0x00001014, 0x17161514,
    0x00001018, 0x1b1a1918,
    0x0000101c, 0x1f1e1d1c,
    0x00001020, 0x23222120,
    0x00001024, 0x27262524,
    0x00001028, 0x2b2a2928,
    0x0000102c, 0x2f2e2d2c,
    0x00001030, 0x33323130,
    0x00001034, 0x37363534,
    0x00001038, 0x3b3a3938,
    0x0000103c, 0x3f3e3d3c,
  ]

# 16KB of sequential data

def data_16KB():
  data = []
  for i in range(4096):
    data.extend([0x00001000+i*4,0xabcd1000+i*4])
  return data

# 1024B of random data organized as cache lines

def data_random():
  seed(0xdeadbeef)
  data = []
  for i in range(256):
    data.extend([0x00001000+i*4,randint(0,0xffffffff)])
  return data

#----------------------------------------------------------------------
# Test Cases for Read Hits
#----------------------------------------------------------------------

# Single read hit byte

def read_hit_byte():
  return [
    #    type  opq  addr   len data                type  opq  test len data
    req( 'in', 0x0, 0x1000, 4, 0xdeadbeef ), resp( 'in', 0x0, 0,   4,  0          ),
    req( 'rd', 0x0, 0x1000, 1, 0          ), resp( 'rd', 0x0, 1,   1,  0x000000ef ),
  ]

# Single read hit halfword

def read_hit_hword():
  return [
    #    type  opq  addr   len data                type  opq  test len data
    req( 'in', 0x0, 0x1000, 4, 0xdeadbeef ), resp( 'in', 0x0, 0,   4,  0          ),
    req( 'rd', 0x0, 0x1000, 2, 0          ), resp( 'rd', 0x0, 1,   2,  0x0000beef ),
  ]

# Read every byte of cacheline

def read_hit_cacheline_byte():
  return [
    #    type  opq   addr   len data                type  opq   test len data
    req( 'in', 0x00, 0x1000, 4, 0xdeadbeef ), resp( 'in', 0x00, 0,   4,  0    ),
    req( 'in', 0x01, 0x1004, 4, 0xcafeefac ), resp( 'in', 0x01, 0,   4,  0    ),
    req( 'in', 0x02, 0x1008, 4, 0xc0ffee00 ), resp( 'in', 0x02, 0,   4,  0    ),
    req( 'in', 0x03, 0x100c, 4, 0xabcdef02 ), resp( 'in', 0x03, 0,   4,  0    ),

    req( 'rd', 0x04, 0x1000, 1, 0          ), resp( 'rd', 0x04, 1,   1,  0x000000ef ),
    req( 'rd', 0x05, 0x1001, 1, 0          ), resp( 'rd', 0x05, 1,   1,  0x000000be ),
    req( 'rd', 0x06, 0x1002, 1, 0          ), resp( 'rd', 0x06, 1,   1,  0x000000ad ),
    req( 'rd', 0x07, 0x1003, 1, 0          ), resp( 'rd', 0x07, 1,   1,  0x000000de ),

    req( 'rd', 0x08, 0x1004, 1, 0          ), resp( 'rd', 0x08, 1,   1,  0x000000ac ),
    req( 'rd', 0x09, 0x1005, 1, 0          ), resp( 'rd', 0x09, 1,   1,  0x000000ef ),
    req( 'rd', 0x0a, 0x1006, 1, 0          ), resp( 'rd', 0x0a, 1,   1,  0x000000fe ),
    req( 'rd', 0x0b, 0x1007, 1, 0          ), resp( 'rd', 0x0b, 1,   1,  0x000000ca ),

    req( 'rd', 0x0c, 0x1008, 1, 0          ), resp( 'rd', 0x0c, 1,   1,  0x00000000 ),
    req( 'rd', 0x0d, 0x1009, 1, 0          ), resp( 'rd', 0x0d, 1,   1,  0x000000ee ),
    req( 'rd', 0x0e, 0x100a, 1, 0          ), resp( 'rd', 0x0e, 1,   1,  0x000000ff ),
    req( 'rd', 0x0f, 0x100b, 1, 0          ), resp( 'rd', 0x0f, 1,   1,  0x000000c0 ),

    req( 'rd', 0x10, 0x100c, 1, 0          ), resp( 'rd', 0x10, 1,   1,  0x00000002 ),
    req( 'rd', 0x11, 0x100d, 1, 0          ), resp( 'rd', 0x11, 1,   1,  0x000000ef ),
    req( 'rd', 0x12, 0x100e, 1, 0          ), resp( 'rd', 0x12, 1,   1,  0x000000cd ),
    req( 'rd', 0x13, 0x100f, 1, 0          ), resp( 'rd', 0x13, 1,   1,  0x000000ab ),
  ]

# Read every halfword of cacheline

def read_hit_cacheline_hword():
  return [
    #    type  opq   addr   len data                type  opq   test len data
    req( 'in', 0x00, 0x1000, 4, 0xdeadbeef ), resp( 'in', 0x00, 0,   4,  0    ),
    req( 'in', 0x01, 0x1004, 4, 0xcafeefac ), resp( 'in', 0x01, 0,   4,  0    ),
    req( 'in', 0x02, 0x1008, 4, 0xc0ffee00 ), resp( 'in', 0x02, 0,   4,  0    ),
    req( 'in', 0x03, 0x100c, 4, 0xabcdef02 ), resp( 'in', 0x03, 0,   4,  0    ),

    req( 'rd', 0x04, 0x1000, 2, 0          ), resp( 'rd', 0x04, 1,   2,  0x0000beef ),
    req( 'rd', 0x05, 0x1001, 2, 0          ), resp( 'rd', 0x05, 1,   2,  0x0000adbe ),
    req( 'rd', 0x06, 0x1002, 2, 0          ), resp( 'rd', 0x06, 1,   2,  0x0000dead ),
    req( 'rd', 0x07, 0x1003, 2, 0          ), resp( 'rd', 0x07, 1,   2,  0x0000acde ),

    req( 'rd', 0x08, 0x1004, 2, 0          ), resp( 'rd', 0x08, 1,   2,  0x0000efac ),
    req( 'rd', 0x09, 0x1005, 2, 0          ), resp( 'rd', 0x09, 1,   2,  0x0000feef ),
    req( 'rd', 0x0a, 0x1006, 2, 0          ), resp( 'rd', 0x0a, 1,   2,  0x0000cafe ),
    req( 'rd', 0x0b, 0x1007, 2, 0          ), resp( 'rd', 0x0b, 1,   2,  0x000000ca ),

    req( 'rd', 0x0c, 0x1008, 2, 0          ), resp( 'rd', 0x0c, 1,   2,  0x0000ee00 ),
    req( 'rd', 0x0d, 0x1009, 2, 0          ), resp( 'rd', 0x0d, 1,   2,  0x0000ffee ),
    req( 'rd', 0x0e, 0x100a, 2, 0          ), resp( 'rd', 0x0e, 1,   2,  0x0000c0ff ),
    req( 'rd', 0x0f, 0x100b, 2, 0          ), resp( 'rd', 0x0f, 1,   2,  0x000002c0 ),

    req( 'rd', 0x10, 0x100c, 2, 0          ), resp( 'rd', 0x10, 1,   2,  0x0000ef02 ),
    req( 'rd', 0x11, 0x100d, 2, 0          ), resp( 'rd', 0x11, 1,   2,  0x0000cdef ),
    req( 'rd', 0x12, 0x100e, 2, 0          ), resp( 'rd', 0x12, 1,   2,  0x0000abcd ),
  ]

#----------------------------------------------------------------------
# Test Cases for Write Hits
#----------------------------------------------------------------------

# Single write hit byte

def write_hit_byte():
  return [
    #    type  opq  addr   len data                type  opq  test len data
    req( 'in', 0x0, 0x1000, 4, 0xdeadbeef ), resp( 'in', 0x0, 0,   4,  0          ),
    req( 'wr', 0x1, 0x1000, 1, 0xcafecafe ), resp( 'wr', 0x1, 1,   1,  0          ),
    req( 'rd', 0x2, 0x1000, 4, 0          ), resp( 'rd', 0x2, 1,   4,  0xdeadbefe ),
  ]

# Single write hit halfword

def write_hit_hword():
  return [
    #    type  opq  addr   len data                type  opq  test len data
    req( 'in', 0x0, 0x1000, 4, 0xdeadbeef ), resp( 'in', 0x0, 0,   4,  0          ),
    req( 'wr', 0x1, 0x1000, 2, 0xcafecafe ), resp( 'wr', 0x1, 1,   2,  0          ),
    req( 'rd', 0x2, 0x1000, 4, 0          ), resp( 'rd', 0x2, 1,   4,  0xdeadcafe ),
  ]

# Write every byte of cacheline

def write_hit_cacheline_byte():
  return [
    #    type  opq   addr   len data                type  opq   test len data
    req( 'in', 0x00, 0x1000, 4, 0xdeadbeef ), resp( 'in', 0x00, 0,   4,  0    ),
    req( 'in', 0x01, 0x1004, 4, 0xcafeefac ), resp( 'in', 0x01, 0,   4,  0    ),
    req( 'in', 0x02, 0x1008, 4, 0xc0ffee00 ), resp( 'in', 0x02, 0,   4,  0    ),
    req( 'in', 0x03, 0x100c, 4, 0xabcdef02 ), resp( 'in', 0x03, 0,   4,  0    ),

    req( 'wr', 0x10, 0x1000, 1, 0x00000000 ), resp( 'wr', 0x10, 1,   1,  0          ),
    req( 'rd', 0x11, 0x1000, 4, 0          ), resp( 'rd', 0x11, 1,   4,  0xdeadbe00 ),
    req( 'wr', 0x12, 0x1001, 1, 0x00000001 ), resp( 'wr', 0x12, 1,   1,  0          ),
    req( 'rd', 0x13, 0x1000, 4, 0          ), resp( 'rd', 0x13, 1,   4,  0xdead0100 ),
    req( 'wr', 0x14, 0x1002, 1, 0x00000002 ), resp( 'wr', 0x14, 1,   1,  0          ),
    req( 'rd', 0x15, 0x1000, 4, 0          ), resp( 'rd', 0x15, 1,   4,  0xde020100 ),
    req( 'wr', 0x16, 0x1003, 1, 0x00000003 ), resp( 'wr', 0x16, 1,   1,  0          ),
    req( 'rd', 0x17, 0x1000, 4, 0          ), resp( 'rd', 0x17, 1,   4,  0x03020100 ),

    req( 'wr', 0x20, 0x1004, 1, 0x00000004 ), resp( 'wr', 0x20, 1,   1,  0          ),
    req( 'rd', 0x21, 0x1004, 4, 0          ), resp( 'rd', 0x21, 1,   4,  0xcafeef04 ),
    req( 'wr', 0x22, 0x1005, 1, 0x00000005 ), resp( 'wr', 0x22, 1,   1,  0          ),
    req( 'rd', 0x23, 0x1004, 4, 0          ), resp( 'rd', 0x23, 1,   4,  0xcafe0504 ),
    req( 'wr', 0x24, 0x1006, 1, 0x00000006 ), resp( 'wr', 0x24, 1,   1,  0          ),
    req( 'rd', 0x25, 0x1004, 4, 0          ), resp( 'rd', 0x25, 1,   4,  0xca060504 ),
    req( 'wr', 0x26, 0x1007, 1, 0x00000007 ), resp( 'wr', 0x26, 1,   1,  0          ),
    req( 'rd', 0x27, 0x1004, 4, 0          ), resp( 'rd', 0x27, 1,   4,  0x07060504 ),

    req( 'wr', 0x30, 0x1008, 1, 0x00000008 ), resp( 'wr', 0x30, 1,   1,  0          ),
    req( 'rd', 0x31, 0x1008, 4, 0          ), resp( 'rd', 0x31, 1,   4,  0xc0ffee08 ),
    req( 'wr', 0x32, 0x1009, 1, 0x00000009 ), resp( 'wr', 0x32, 1,   1,  0          ),
    req( 'rd', 0x33, 0x1008, 4, 0          ), resp( 'rd', 0x33, 1,   4,  0xc0ff0908 ),
    req( 'wr', 0x34, 0x100a, 1, 0x0000000a ), resp( 'wr', 0x34, 1,   1,  0          ),
    req( 'rd', 0x35, 0x1008, 4, 0          ), resp( 'rd', 0x35, 1,   4,  0xc00a0908 ),
    req( 'wr', 0x36, 0x100b, 1, 0x0000000b ), resp( 'wr', 0x36, 1,   1,  0          ),
    req( 'rd', 0x37, 0x1008, 4, 0          ), resp( 'rd', 0x37, 1,   4,  0x0b0a0908 ),

    req( 'wr', 0x40, 0x100c, 1, 0x0000000c ), resp( 'wr', 0x40, 1,   1,  0          ),
    req( 'rd', 0x41, 0x100c, 4, 0          ), resp( 'rd', 0x41, 1,   4,  0xabcdef0c ),
    req( 'wr', 0x42, 0x100d, 1, 0x0000000d ), resp( 'wr', 0x42, 1,   1,  0          ),
    req( 'rd', 0x43, 0x100c, 4, 0          ), resp( 'rd', 0x43, 1,   4,  0xabcd0d0c ),
    req( 'wr', 0x44, 0x100e, 1, 0x0000000e ), resp( 'wr', 0x44, 1,   1,  0          ),
    req( 'rd', 0x45, 0x100c, 4, 0          ), resp( 'rd', 0x45, 1,   4,  0xab0e0d0c ),
    req( 'wr', 0x46, 0x100f, 1, 0x0000000f ), resp( 'wr', 0x46, 1,   1,  0          ),
    req( 'rd', 0x47, 0x100c, 4, 0          ), resp( 'rd', 0x47, 1,   4,  0x0f0e0d0c ),
  ]

# Write every halfword of cacheline

def write_hit_cacheline_hword():
  return [
    #    type  opq   addr   len data                type  opq   test len data
    req( 'in', 0x00, 0x1000, 4, 0xdeadbeef ), resp( 'in', 0x00, 0,   4,  0    ),
    req( 'in', 0x01, 0x1004, 4, 0xcafeefac ), resp( 'in', 0x01, 0,   4,  0    ),
    req( 'in', 0x02, 0x1008, 4, 0xc0ffee00 ), resp( 'in', 0x02, 0,   4,  0    ),
    req( 'in', 0x03, 0x100c, 4, 0xabcdef02 ), resp( 'in', 0x03, 0,   4,  0    ),

    req( 'wr', 0x10, 0x1000, 2, 0x00000100 ), resp( 'wr', 0x10, 1,   2,  0          ),
    req( 'rd', 0x11, 0x1000, 4, 0          ), resp( 'rd', 0x11, 1,   4,  0xdead0100 ),
    req( 'wr', 0x12, 0x1001, 2, 0x00000302 ), resp( 'wr', 0x12, 1,   2,  0          ),
    req( 'rd', 0x13, 0x1000, 4, 0          ), resp( 'rd', 0x13, 1,   4,  0xde030200 ),
    req( 'wr', 0x14, 0x1002, 2, 0x00000504 ), resp( 'wr', 0x14, 1,   2,  0          ),
    req( 'rd', 0x15, 0x1000, 4, 0          ), resp( 'rd', 0x15, 1,   4,  0x05040200 ),
    req( 'wr', 0x16, 0x1003, 2, 0x00000706 ), resp( 'wr', 0x16, 1,   2,  0          ),
    req( 'rd', 0x17, 0x1000, 4, 0          ), resp( 'rd', 0x17, 1,   4,  0x06040200 ),
    req( 'rd', 0x18, 0x1004, 4, 0          ), resp( 'rd', 0x18, 1,   4,  0xcafeef07 ),

    req( 'wr', 0x20, 0x1004, 2, 0x00000908 ), resp( 'wr', 0x20, 1,   2,  0          ),
    req( 'rd', 0x21, 0x1004, 4, 0          ), resp( 'rd', 0x21, 1,   4,  0xcafe0908 ),
    req( 'wr', 0x22, 0x1005, 2, 0x00000b0a ), resp( 'wr', 0x22, 1,   2,  0          ),
    req( 'rd', 0x23, 0x1004, 4, 0          ), resp( 'rd', 0x23, 1,   4,  0xca0b0a08 ),
    req( 'wr', 0x24, 0x1006, 2, 0x00000d0c ), resp( 'wr', 0x24, 1,   2,  0          ),
    req( 'rd', 0x25, 0x1004, 4, 0          ), resp( 'rd', 0x25, 1,   4,  0x0d0c0a08 ),
    req( 'wr', 0x26, 0x1007, 2, 0x00000f0e ), resp( 'wr', 0x26, 1,   2,  0          ),
    req( 'rd', 0x27, 0x1004, 4, 0          ), resp( 'rd', 0x27, 1,   4,  0x0e0c0a08 ),
    req( 'rd', 0x28, 0x1008, 4, 0          ), resp( 'rd', 0x28, 1,   4,  0xc0ffee0f ),

    req( 'wr', 0x30, 0x1008, 2, 0x00001110 ), resp( 'wr', 0x30, 1,   2,  0          ),
    req( 'rd', 0x31, 0x1008, 4, 0          ), resp( 'rd', 0x31, 1,   4,  0xc0ff1110 ),
    req( 'wr', 0x32, 0x1009, 2, 0x00001312 ), resp( 'wr', 0x32, 1,   2,  0          ),
    req( 'rd', 0x33, 0x1008, 4, 0          ), resp( 'rd', 0x33, 1,   4,  0xc0131210 ),
    req( 'wr', 0x34, 0x100a, 2, 0x00001514 ), resp( 'wr', 0x34, 1,   2,  0          ),
    req( 'rd', 0x35, 0x1008, 4, 0          ), resp( 'rd', 0x35, 1,   4,  0x15141210 ),
    req( 'wr', 0x36, 0x100b, 2, 0x00001716 ), resp( 'wr', 0x36, 1,   2,  0          ),
    req( 'rd', 0x37, 0x1008, 4, 0          ), resp( 'rd', 0x37, 1,   4,  0x16141210 ),
    req( 'rd', 0x38, 0x100c, 4, 0          ), resp( 'rd', 0x38, 1,   4,  0xabcdef17 ),

    req( 'wr', 0x40, 0x100c, 2, 0x00001918 ), resp( 'wr', 0x40, 1,   2,  0          ),
    req( 'rd', 0x41, 0x100c, 4, 0          ), resp( 'rd', 0x41, 1,   4,  0xabcd1918 ),
    req( 'wr', 0x42, 0x100d, 2, 0x00001b1a ), resp( 'wr', 0x42, 1,   2,  0          ),
    req( 'rd', 0x43, 0x100c, 4, 0          ), resp( 'rd', 0x43, 1,   4,  0xab1b1a18 ),
    req( 'wr', 0x44, 0x100e, 2, 0x00001d1c ), resp( 'wr', 0x44, 1,   2,  0          ),
    req( 'rd', 0x45, 0x100c, 4, 0          ), resp( 'rd', 0x45, 1,   4,  0x1d1c1a18 ),
  ]

#----------------------------------------------------------------------
# Test Cases for Refill on Read Miss
#----------------------------------------------------------------------

# Single read miss byte (uses data_64B)

def read_miss_byte():
  return [
    #    type  opq  addr   len data                type  opq  test len data
    req( 'rd', 0x0, 0x1001, 1, 0          ), resp( 'rd', 0x0, 0,   1,  0x000000001 ),
  ]

# Single read miss halfword (uses data_64B)

def read_miss_hword():
  return [
    #    type  opq  addr   len data                type  opq  test len data
    req( 'rd', 0x0, 0x1000, 2, 0          ), resp( 'rd', 0x0, 0,   2,  0x00000100 ),
  ]

# Read bytes from different cachelines that miss (uses data_16KB)

def read_miss_cachelines_byte():
  return [
    #    type  opq   addr   len data                type  opq   test len data
    req( 'rd', 0x00, 0x1000, 1, 0          ), resp( 'rd', 0x00, 0,   1,  0x00000000 ),
    req( 'rd', 0x01, 0x1010, 1, 0          ), resp( 'rd', 0x01, 0,   1,  0x00000010 ),
    req( 'rd', 0x02, 0x1020, 1, 0          ), resp( 'rd', 0x02, 0,   1,  0x00000020 ),
    req( 'rd', 0x03, 0x1030, 1, 0          ), resp( 'rd', 0x03, 0,   1,  0x00000030 ),

    req( 'rd', 0x04, 0x1040, 1, 0          ), resp( 'rd', 0x04, 0,   1,  0x00000040 ),
    req( 'rd', 0x05, 0x1050, 1, 0          ), resp( 'rd', 0x05, 0,   1,  0x00000050 ),
    req( 'rd', 0x06, 0x1060, 1, 0          ), resp( 'rd', 0x06, 0,   1,  0x00000060 ),
    req( 'rd', 0x07, 0x1070, 1, 0          ), resp( 'rd', 0x07, 0,   1,  0x00000070 ),

    req( 'rd', 0x08, 0x1080, 1, 0          ), resp( 'rd', 0x08, 0,   1,  0x00000080 ),
    req( 'rd', 0x09, 0x1090, 1, 0          ), resp( 'rd', 0x09, 0,   1,  0x00000090 ),
    req( 'rd', 0x0a, 0x10a0, 1, 0          ), resp( 'rd', 0x0a, 0,   1,  0x000000a0 ),
    req( 'rd', 0x0b, 0x10b0, 1, 0          ), resp( 'rd', 0x0b, 0,   1,  0x000000b0 ),

    req( 'rd', 0x0c, 0x10c0, 1, 0          ), resp( 'rd', 0x0c, 0,   1,  0x000000c0 ),
    req( 'rd', 0x0d, 0x10d0, 1, 0          ), resp( 'rd', 0x0d, 0,   1,  0x000000d0 ),
    req( 'rd', 0x0e, 0x10e0, 1, 0          ), resp( 'rd', 0x0e, 0,   1,  0x000000e0 ),
    req( 'rd', 0x0f, 0x10f0, 1, 0          ), resp( 'rd', 0x0f, 0,   1,  0x000000f0 ),
  ]

# Read halfwords from different cachelines that miss (uses data_16KB)

def read_miss_cachelines_hword():
  return [
    #    type  opq   addr   len data                type  opq   test len data
    req( 'rd', 0x00, 0x1000, 2, 0          ), resp( 'rd', 0x00, 0,   2,  0x00001000 ),
    req( 'rd', 0x01, 0x1010, 2, 0          ), resp( 'rd', 0x01, 0,   2,  0x00001010 ),
    req( 'rd', 0x02, 0x1020, 2, 0          ), resp( 'rd', 0x02, 0,   2,  0x00001020 ),
    req( 'rd', 0x03, 0x1030, 2, 0          ), resp( 'rd', 0x03, 0,   2,  0x00001030 ),

    req( 'rd', 0x04, 0x1040, 2, 0          ), resp( 'rd', 0x04, 0,   2,  0x00001040 ),
    req( 'rd', 0x05, 0x1050, 2, 0          ), resp( 'rd', 0x05, 0,   2,  0x00001050 ),
    req( 'rd', 0x06, 0x1060, 2, 0          ), resp( 'rd', 0x06, 0,   2,  0x00001060 ),
    req( 'rd', 0x07, 0x1070, 2, 0          ), resp( 'rd', 0x07, 0,   2,  0x00001070 ),

    req( 'rd', 0x08, 0x1080, 2, 0          ), resp( 'rd', 0x08, 0,   2,  0x00001080 ),
    req( 'rd', 0x09, 0x1090, 2, 0          ), resp( 'rd', 0x09, 0,   2,  0x00001090 ),
    req( 'rd', 0x0a, 0x10a0, 2, 0          ), resp( 'rd', 0x0a, 0,   2,  0x000010a0 ),
    req( 'rd', 0x0b, 0x10b0, 2, 0          ), resp( 'rd', 0x0b, 0,   2,  0x000010b0 ),

    req( 'rd', 0x0c, 0x10c0, 2, 0          ), resp( 'rd', 0x0c, 0,   2,  0x000010c0 ),
    req( 'rd', 0x0d, 0x10d0, 2, 0          ), resp( 'rd', 0x0d, 0,   2,  0x000010d0 ),
    req( 'rd', 0x0e, 0x10e0, 2, 0          ), resp( 'rd', 0x0e, 0,   2,  0x000010e0 ),
    req( 'rd', 0x0f, 0x10f0, 2, 0          ), resp( 'rd', 0x0f, 0,   2,  0x000010f0 ),
  ]

#----------------------------------------------------------------------
# Test Cases for Refill on Write Miss
#----------------------------------------------------------------------

# Single write miss byte (uses data_64B)

def write_miss_byte():
  return [
    #    type  opq  addr   len data                type  opq  test len data
    req( 'wr', 0x0, 0x1000, 1, 0xdeadbeef ), resp( 'wr', 0x0, 0,   1,  0          ),
    req( 'rd', 0x0, 0x1000, 4, 0          ), resp( 'rd', 0x0, 1,   4,  0x030201ef ),
  ]

# Single write miss halfword (uses data_64B)

def write_miss_hword():
  return [
    #    type  opq  addr   len data                type  opq  test len data
    req( 'wr', 0x0, 0x1000, 2, 0xdeadbeef ), resp( 'wr', 0x0, 0,   2,  0          ),
    req( 'rd', 0x0, 0x1000, 4, 0          ), resp( 'rd', 0x0, 1,   4,  0x0302beef ),
  ]

#----------------------------------------------------------------------
# Test Cases for Evict
#----------------------------------------------------------------------

# Write miss to two cachelines, and then a read to a third cacheline.
# This read to the third cacheline is guaranteed to cause an eviction on
# both the direct mapped and set associative caches. (uses data_16KB)

def evict_byte():
  return [
    #    type  opq  addr   len data                type  opq  test len data
    req( 'wr', 0x0, 0x1000, 1, 0xcafecafe ), resp( 'wr', 0x0, 0,   1,  0          ),
    req( 'rd', 0x0, 0x1000, 4, 0          ), resp( 'rd', 0x0, 1,   4,  0xabcd10fe ),
    req( 'wr', 0x0, 0x2000, 1, 0xdeadbeef ), resp( 'wr', 0x0, 0,   1,  0          ),
    req( 'rd', 0x0, 0x2000, 4, 0          ), resp( 'rd', 0x0, 1,   4,  0xabcd20ef ),
    req( 'rd', 0x0, 0x3000, 4, 0          ), resp( 'rd', 0x0, 0,   4,  0xabcd3000 ), # conflicts
    req( 'rd', 0x0, 0x1000, 4, 0          ), resp( 'rd', 0x0, 0,   4,  0xabcd10fe ),
  ]

def evict_hword():
  return [
    #    type  opq  addr   len data                type  opq  test len data
    req( 'wr', 0x0, 0x1000, 2, 0xcafecafe ), resp( 'wr', 0x0, 0,   2,  0          ),
    req( 'rd', 0x0, 0x1000, 4, 0          ), resp( 'rd', 0x0, 1,   4,  0xabcdcafe ),
    req( 'wr', 0x0, 0x2000, 2, 0xdeadbeef ), resp( 'wr', 0x0, 0,   2,  0          ),
    req( 'rd', 0x0, 0x2000, 4, 0          ), resp( 'rd', 0x0, 1,   4,  0xabcdbeef ),
    req( 'rd', 0x0, 0x3000, 4, 0          ), resp( 'rd', 0x0, 0,   4,  0xabcd3000 ), # conflicts
    req( 'rd', 0x0, 0x1000, 4, 0          ), resp( 'rd', 0x0, 0,   4,  0xabcdcafe ),
  ]

#-------------------------------------------------------------------------
# Test case table
#-------------------------------------------------------------------------

test_case_table = mk_test_case_table([
  (                                    "msg_func                    mem_data_func stall lat src sink"),

  [ "read_hit_byte",                    read_hit_byte,              None,         0.0,  0,  0,  0    ],
  [ "read_hit_hword",                   read_hit_hword,             None,         0.0,  0,  0,  0    ],
  [ "read_hit_cacheline_byte",          read_hit_cacheline_byte,    None,         0.0,  0,  0,  0    ],
  [ "read_hit_cacheline_hword",         read_hit_cacheline_hword,   None,         0.0,  0,  0,  0    ],

  [ "write_hit_byte",                   write_hit_byte,             None,         0.0,  0,  0,  0    ],
  [ "write_hit_hword",                  write_hit_hword,            None,         0.0,  0,  0,  0    ],
  [ "write_hit_cacheline_byte",         write_hit_cacheline_byte,   None,         0.0,  0,  0,  0    ],
  [ "write_hit_cacheline_hword",        write_hit_cacheline_hword,  None,         0.0,  0,  0,  0    ],

  [ "read_miss_byte",                   read_miss_byte,             data_64B,     0.0,  0,  0,  0    ],
  [ "read_miss_hword",                  read_miss_hword,            data_64B,     0.0,  0,  0,  0    ],
  [ "read_miss_cachelines_byte",        read_miss_cachelines_byte,  data_16KB,    0.0,  0,  0,  0    ],
  [ "read_miss_cachelines_hword",       read_miss_cachelines_hword, data_16KB,    0.0,  0,  0,  0    ],

  [ "write_miss_byte",                  write_miss_byte,            data_64B,     0.0,  0,  0,  0    ],
  [ "write_miss_hword",                 write_miss_hword,           data_64B,     0.0,  0,  0,  0    ],

  [ "evict_byte",                       evict_byte,                 data_16KB,    0.0,  0,  0,  0    ],
  [ "evict_hword",                      evict_hword,                data_16KB,    0.0,  0,  0,  0    ],
])

@pytest.mark.parametrize( **test_case_table )
def test_subword( test_params ):
  run_test( CacheFL(), test_params, cmp_fun=cmp_wo_test_field )

#-------------------------------------------------------------------------
# Test Case with Random Addresses and Data
#-------------------------------------------------------------------------

class VerificationMemory:
  def __init__( self ):

    # Use the global data_random function

    data_array = data_random()

    # Organize verification memory as an array of bytes

    self.vmem = []
    for data in data_array[1::2]:
      self.vmem.append( data & 0x000000ff )
      self.vmem.append( (data & 0x0000ff00) >> 8  )
      self.vmem.append( (data & 0x00ff0000) >> 16 )
      self.vmem.append( (data & 0xff000000) >> 24 )

  def read( self, addr, len_ ):
    addr = addr - 0x00001000
    data = 0
    for i in range(len_):
      data = data | (self.vmem[addr+i] << 8*i)
    return data

  def write( self, addr, len_, data ):
    addr = addr - 0x00001000
    for i in range(len_):
      self.vmem[addr+i] = (data & (0xff << 8*i)) >> 8*i

  def random( self ):

    # random address and length that does not cross cachelines

    len_   = choice([1,2,4])
    offset = randint(0,16-len_)
    index  = randint(0,(len(self.vmem)//16)-1)
    addr   = 0x00001000 + index*16 + offset

    # random read

    if randint(0,1):
      data = self.read(addr,len_)
      return 'rd',addr,len_,data

    # random write

    else:
      data = randint(0,0xffffffff)
      self.write(addr,len_,data)
      return 'wr',addr,len_,data

def random():

  vmem = VerificationMemory()
  msgs = []

  for i in range(500):
    opaque = i & 0xff
    type_,addr,len_,data = vmem.random()
    if type_ == 'rd':
      msgs.extend([
        req( 'rd', opaque, addr, len_, 0 ),
        resp( 'rd', opaque, 0, len_, data ),
      ])
    else:
      msgs.extend([
        req( 'wr', opaque, addr, len_, data ),
        resp( 'wr', opaque, 0, len_, 0 ),
      ])

  return msgs

test_case_table_random = mk_test_case_table([
  (            "msg_func mem_data_func stall lat src sink"),
  [ "random",  random,   data_random,  0,    0,  0,  0    ],
])

# Notice how the we pass cmp_wo_test_field to our run_test helper
# function. This means that these random test cases will _not_ check the
# test bit (i.e., will _not_ check hit/miss).

@pytest.mark.parametrize( **test_case_table_random )
def test_subword_random( test_params ):
  run_test( CacheFL(), test_params, cmp_fun=cmp_wo_test_field )

