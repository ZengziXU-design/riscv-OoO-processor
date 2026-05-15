#=========================================================================
# CacheFL_wide_test.py
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

# Single read hits

def read_hit_8B():
  return [
    #    type  opq  addr   len data                                           type  opq  test len data
    req( 'in', 0x0, 0x1000, 0, 0xabcdef02_c0ffee00_cafeefac_deadbeef ), resp( 'in', 0x0, 0,   0,  0                   ),
    req( 'rd', 0x0, 0x1000, 8, 0                                     ), resp( 'rd', 0x0, 1,   8,  0xcafeefac_deadbeef ),
  ]

def read_hit_16B():
  return [
    #    type  opq  addr   len data                                           type  opq  test len data
    req( 'in', 0x0, 0x1000, 0, 0xabcdef02_c0ffee00_cafeefac_deadbeef ), resp( 'in', 0x0, 0,   0,  0                                     ),
    req( 'rd', 0x0, 0x1000, 0, 0 ),                                     resp( 'rd', 0x0, 1,   0,  0xabcdef02_c0ffee00_cafeefac_deadbeef ),
  ]

# Read every 8B from cacheline

def read_hit_cacheline_8B():
  return [
    #    type  opq   addr   len data                type  opq   test len data
    req( 'in', 0x00, 0x1000, 4, 0xdeadbeef ), resp( 'in', 0x00, 0,   4,  0                   ),
    req( 'in', 0x01, 0x1004, 4, 0xcafeefac ), resp( 'in', 0x01, 0,   4,  0                   ),
    req( 'in', 0x02, 0x1008, 4, 0xc0ffee00 ), resp( 'in', 0x02, 0,   4,  0                   ),
    req( 'in', 0x03, 0x100c, 4, 0xabcdef02 ), resp( 'in', 0x03, 0,   4,  0                   ),

    req( 'rd', 0x04, 0x1000, 8, 0          ), resp( 'rd', 0x04, 1,   8,  0xcafeefac_deadbeef ),
    req( 'rd', 0x05, 0x1001, 8, 0          ), resp( 'rd', 0x05, 1,   8,  0x00cafeef_acdeadbe ),
    req( 'rd', 0x06, 0x1002, 8, 0          ), resp( 'rd', 0x06, 1,   8,  0xee00cafe_efacdead ),
    req( 'rd', 0x07, 0x1003, 8, 0          ), resp( 'rd', 0x07, 1,   8,  0xffee00ca_feefacde ),
    req( 'rd', 0x08, 0x1004, 8, 0          ), resp( 'rd', 0x08, 1,   8,  0xc0ffee00_cafeefac ),
    req( 'rd', 0x09, 0x1005, 8, 0          ), resp( 'rd', 0x09, 1,   8,  0x02c0ffee_00cafeef ),
    req( 'rd', 0x0a, 0x1006, 8, 0          ), resp( 'rd', 0x0a, 1,   8,  0xef02c0ff_ee00cafe ),
    req( 'rd', 0x0b, 0x1007, 8, 0          ), resp( 'rd', 0x0b, 1,   8,  0xcdef02c0_ffee00ca ),
    req( 'rd', 0x0c, 0x1008, 8, 0          ), resp( 'rd', 0x0c, 1,   8,  0xabcdef02_c0ffee00 ),
  ]

#----------------------------------------------------------------------
# Test Cases for Write Hits
#----------------------------------------------------------------------

# Single writes

def write_hit_8B():
  return [
    #    type  opq  addr   len data                                           type  opq  test len data
    req( 'in', 0x0, 0x1000, 0, 0xabcdef02_c0ffee00_cafeefac_deadbeef ), resp( 'in', 0x0, 0,   0,  0                                     ),
    req( 'wr', 0x1, 0x1000, 8, 0x01020304_05060708                   ), resp( 'wr', 0x1, 1,   8,  0                                     ),
    req( 'rd', 0x2, 0x1000, 0, 0                                     ), resp( 'rd', 0x2, 1,   0,  0xabcdef02_c0ffee00_01020304_05060708 ),
  ]

def write_hit_16B():
  return [
    #    type  opq  addr   len data                                           type  opq  test len data
    req( 'in', 0x0, 0x1000, 0, 0xabcdef02_c0ffee00_cafeefac_deadbeef ), resp( 'in', 0x0, 0,   0,  0                                     ),
    req( 'wr', 0x1, 0x1000, 0, 0x01020304_05060708_090a0b0c_0d0e0f00 ), resp( 'wr', 0x1, 1,   0,  0                                     ),
    req( 'rd', 0x2, 0x1000, 0, 0                                     ), resp( 'rd', 0x2, 1,   0,  0x01020304_05060708_090a0b0c_0d0e0f00 ),
  ]

# Write every 8B of cacheline

def write_hit_cacheline_8B():
  return [
    #    type  opq   addr   len data                         type  opq   test len data
    req( 'in', 0x00, 0x1000, 4, 0xdeadbeef ),          resp( 'in', 0x00, 0,   4,  0    ),
    req( 'in', 0x01, 0x1004, 4, 0xcafeefac ),          resp( 'in', 0x01, 0,   4,  0    ),
    req( 'in', 0x02, 0x1008, 4, 0xc0ffee00 ),          resp( 'in', 0x02, 0,   4,  0    ),
    req( 'in', 0x03, 0x100c, 4, 0xabcdef02 ),          resp( 'in', 0x03, 0,   4,  0    ),

    req( 'wr', 0x10, 0x1000, 8, 0x01020304_05060708 ), resp( 'wr', 0x10, 1,   8,  0                                     ),
    req( 'rd', 0x11, 0x1000, 0, 0                   ), resp( 'rd', 0x11, 1,   0,  0xabcdef02_c0ffee00_01020304_05060708 ),
    req( 'wr', 0x12, 0x1001, 8, 0x01020304_05060708 ), resp( 'wr', 0x12, 1,   8,  0                                     ),
    req( 'rd', 0x13, 0x1000, 0, 0                   ), resp( 'rd', 0x13, 1,   0,  0xabcdef02_c0ffee01_02030405_06070808 ),
    req( 'wr', 0x14, 0x1002, 8, 0x01020304_05060708 ), resp( 'wr', 0x14, 1,   8,  0                                     ),
    req( 'rd', 0x15, 0x1000, 0, 0                   ), resp( 'rd', 0x15, 1,   0,  0xabcdef02_c0ff0102_03040506_07080808 ),
    req( 'wr', 0x16, 0x1003, 8, 0x01020304_05060708 ), resp( 'wr', 0x16, 1,   8,  0                                     ),
    req( 'rd', 0x17, 0x1000, 0, 0                   ), resp( 'rd', 0x17, 1,   0,  0xabcdef02_c0010203_04050607_08080808 ),

    req( 'wr', 0x20, 0x1004, 8, 0x01020304_05060708 ), resp( 'wr', 0x20, 1,   8,  0                                     ),
    req( 'rd', 0x21, 0x1000, 0, 0                   ), resp( 'rd', 0x21, 1,   0,  0xabcdef02_01020304_05060708_08080808 ),
    req( 'wr', 0x22, 0x1005, 8, 0x01020304_05060708 ), resp( 'wr', 0x22, 1,   8,  0                                     ),
    req( 'rd', 0x23, 0x1000, 0, 0                   ), resp( 'rd', 0x23, 1,   0,  0xabcdef01_02030405_06070808_08080808 ),
    req( 'wr', 0x24, 0x1006, 8, 0x01020304_05060708 ), resp( 'wr', 0x24, 1,   8,  0                                     ),
    req( 'rd', 0x25, 0x1000, 0, 0                   ), resp( 'rd', 0x25, 1,   0,  0xabcd0102_03040506_07080808_08080808 ),
    req( 'wr', 0x26, 0x1007, 8, 0x01020304_05060708 ), resp( 'wr', 0x26, 1,   8,  0                                     ),
    req( 'rd', 0x27, 0x1000, 0, 0                   ), resp( 'rd', 0x27, 1,   0,  0xab010203_04050607_08080808_08080808 ),

    req( 'wr', 0x30, 0x1008, 8, 0x01020304_05060708 ), resp( 'wr', 0x30, 1,   8,  0                                     ),
    req( 'rd', 0x31, 0x1000, 0, 0                   ), resp( 'rd', 0x31, 1,   0,  0x01020304_05060708_08080808_08080808 ),
  ]

#----------------------------------------------------------------------
# Test Cases for Refill on Read Miss
#----------------------------------------------------------------------

# Single read misses (uses data_64B)

def read_miss_8B():
  return [
    #    type  opq  addr   len data                type  opq  test len data
    req( 'rd', 0x0, 0x1000, 8, 0          ), resp( 'rd', 0x0, 0,   8,  0x07060504_03020100 ),
  ]

def read_miss_16B():
  return [
    #    type  opq  addr   len data                type  opq  test len data
    req( 'rd', 0x0, 0x1000, 0, 0          ), resp( 'rd', 0x0, 0,   0,  0x0f0e0d0c_0b0a0908_07060504_03020100 ),
  ]

# Read 8Bs from different cachelines that miss (uses data_16KB)

def read_miss_cachelines_8B():
  return [
    #    type  opq   addr   len data                type  opq   test len data
    req( 'rd', 0x00, 0x1000, 8, 0          ), resp( 'rd', 0x00, 0,   8,  0xabcd1004_abcd1000 ),
    req( 'rd', 0x01, 0x1010, 8, 0          ), resp( 'rd', 0x01, 0,   8,  0xabcd1014_abcd1010 ),
    req( 'rd', 0x02, 0x1020, 8, 0          ), resp( 'rd', 0x02, 0,   8,  0xabcd1024_abcd1020 ),
    req( 'rd', 0x03, 0x1030, 8, 0          ), resp( 'rd', 0x03, 0,   8,  0xabcd1034_abcd1030 ),

    req( 'rd', 0x04, 0x1040, 8, 0          ), resp( 'rd', 0x04, 0,   8,  0xabcd1044_abcd1040 ),
    req( 'rd', 0x05, 0x1050, 8, 0          ), resp( 'rd', 0x05, 0,   8,  0xabcd1054_abcd1050 ),
    req( 'rd', 0x06, 0x1060, 8, 0          ), resp( 'rd', 0x06, 0,   8,  0xabcd1064_abcd1060 ),
    req( 'rd', 0x07, 0x1070, 8, 0          ), resp( 'rd', 0x07, 0,   8,  0xabcd1074_abcd1070 ),

    req( 'rd', 0x08, 0x1080, 8, 0          ), resp( 'rd', 0x08, 0,   8,  0xabcd1084_abcd1080 ),
    req( 'rd', 0x09, 0x1090, 8, 0          ), resp( 'rd', 0x09, 0,   8,  0xabcd1094_abcd1090 ),
    req( 'rd', 0x0a, 0x10a0, 8, 0          ), resp( 'rd', 0x0a, 0,   8,  0xabcd10a4_abcd10a0 ),
    req( 'rd', 0x0b, 0x10b0, 8, 0          ), resp( 'rd', 0x0b, 0,   8,  0xabcd10b4_abcd10b0 ),

    req( 'rd', 0x0c, 0x10c0, 8, 0          ), resp( 'rd', 0x0c, 0,   8,  0xabcd10c4_abcd10c0 ),
    req( 'rd', 0x0d, 0x10d0, 8, 0          ), resp( 'rd', 0x0d, 0,   8,  0xabcd10d4_abcd10d0 ),
    req( 'rd', 0x0e, 0x10e0, 8, 0          ), resp( 'rd', 0x0e, 0,   8,  0xabcd10e4_abcd10e0 ),
    req( 'rd', 0x0f, 0x10f0, 8, 0          ), resp( 'rd', 0x0f, 0,   8,  0xabcd10f4_abcd10f0 ),
  ]

#----------------------------------------------------------------------
# Test Cases for Refill on Write Miss
#----------------------------------------------------------------------

# Single write misses (uses data_64B)

def write_miss_8B():
  return [
    #    type  opq  addr   len data                         type  opq  test len data
    req( 'wr', 0x0, 0x1000, 8, 0xcafeefac_deadbeef ), resp( 'wr', 0x0, 0,   8,  0                                     ),
    req( 'rd', 0x0, 0x1000, 0, 0                   ), resp( 'rd', 0x0, 1,   0,  0x0f0e0d0c_0b0a0908_cafeefac_deadbeef ),
  ]

def write_miss_16B():
  return [
    #    type  opq  addr   len data                                           type  opq  test len data
    req( 'wr', 0x0, 0x1000, 0, 0xabcdef02_c0ffee00_cafeefac_deadbeef ), resp( 'wr', 0x0, 0,   0,  0                                     ),
    req( 'rd', 0x0, 0x1000, 0, 0                                     ), resp( 'rd', 0x0, 1,   0,  0xabcdef02_c0ffee00_cafeefac_deadbeef ),
  ]

#----------------------------------------------------------------------
# Test Cases for Evict
#----------------------------------------------------------------------

# Write miss to two cachelines, and then a read to a third cacheline.
# This read to the third cacheline is guaranteed to cause an eviction on
# both the direct mapped and set associative caches. (uses data_16KB)

def evict_8B():
  return [
    #    type  opq  addr   len data                         type  opq  test len data
    req( 'wr', 0x0, 0x1000, 8, 0xcafeefac_deadbeef ), resp( 'wr', 0x0, 0,   8,  0                   ),
    req( 'rd', 0x0, 0x1000, 8, 0                   ), resp( 'rd', 0x0, 1,   8,  0xcafeefac_deadbeef ),
    req( 'wr', 0x0, 0x2000, 8, 0xabcdef02_c0ffee00 ), resp( 'wr', 0x0, 0,   8,  0                   ),
    req( 'rd', 0x0, 0x2000, 8, 0                   ), resp( 'rd', 0x0, 1,   8,  0xabcdef02_c0ffee00 ),
    req( 'rd', 0x0, 0x3000, 4, 0                   ), resp( 'rd', 0x0, 0,   4,  0xabcd3000          ), # conflicts
    req( 'rd', 0x0, 0x1000, 0, 0                   ), resp( 'rd', 0x0, 0,   0,  0xabcd100c_abcd1008_cafeefac_deadbeef ),
  ]

def evict_16B():
  return [
    #    type  opq  addr   len data                                           type  opq  test len data
    req( 'wr', 0x0, 0x1000, 0, 0xabcdef02_c0ffee00_cafeefac_deadbeef ), resp( 'wr', 0x0, 0,   0,  0                                     ),
    req( 'rd', 0x0, 0x1000, 0, 0                                     ), resp( 'rd', 0x0, 1,   0,  0xabcdef02_c0ffee00_cafeefac_deadbeef ),
    req( 'wr', 0x0, 0x2000, 0, 0xa0b0c0d0_e0f01020_30405060_70809000 ), resp( 'wr', 0x0, 0,   0,  0                                     ),
    req( 'rd', 0x0, 0x2000, 0, 0                                     ), resp( 'rd', 0x0, 1,   0,  0xa0b0c0d0_e0f01020_30405060_70809000 ),
    req( 'rd', 0x0, 0x3000, 4, 0                                     ), resp( 'rd', 0x0, 0,   4,  0xabcd3000                            ), # conflicts
    req( 'rd', 0x0, 0x1000, 0, 0                                     ), resp( 'rd', 0x0, 0,   0,  0xabcdef02_c0ffee00_cafeefac_deadbeef ),
  ]

#-------------------------------------------------------------------------
# Test case table
#-------------------------------------------------------------------------

test_case_table = mk_test_case_table([
  (                            "msg_func                  mem_data_func stall lat src sink"),

  [ "read_hit_8B",              read_hit_8B,              None,         0.0,  0,  0,  0    ],
  [ "read_hit_16B",             read_hit_16B,             None,         0.0,  0,  0,  0    ],
  [ "read_hit_cacheline_8B",    read_hit_cacheline_8B,    None,         0.0,  0,  0,  0    ],

  [ "write_hit_8B",             write_hit_8B,             None,         0.0,  0,  0,  0    ],
  [ "write_hit_16B",            write_hit_16B,            None,         0.0,  0,  0,  0    ],
  [ "write_hit_cacheline_8B",   write_hit_cacheline_8B,   None,         0.0,  0,  0,  0    ],

  [ "read_miss_8B",             read_miss_8B,             data_64B,     0.0,  0,  0,  0    ],
  [ "read_miss_16B",            read_miss_16B,            data_64B,     0.0,  0,  0,  0    ],
  [ "read_miss_cachelines_8B",  read_miss_cachelines_8B,  data_16KB,    0.0,  0,  0,  0    ],

  [ "write_miss_8B",            write_miss_8B,            data_64B,     0.0,  0,  0,  0    ],
  [ "write_miss_16B",           write_miss_16B,           data_64B,     0.0,  0,  0,  0    ],

  [ "evict_8B",                 evict_8B,                 data_16KB,    0.0,  0,  0,  0    ],
  [ "evict_16B",                evict_16B,                data_16KB,    0.0,  0,  0,  0    ],
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

    len_   = choice([1,2,4,8,16])
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
    if len_ == 16:
      len_ = 0
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
  (           "msg_func  mem_data_func stall lat src sink"),
  [ "random",  random,   data_random,  0,    0,  0,  0    ],
])

# Notice how the we pass cmp_wo_test_field to our run_test helper
# function. This means that these random test cases will _not_ check the
# test bit (i.e., will _not_ check hit/miss).

@pytest.mark.parametrize( **test_case_table_random )
def test_subword_random( test_params ):
  run_test( CacheFL(), test_params, cmp_fun=cmp_wo_test_field )
