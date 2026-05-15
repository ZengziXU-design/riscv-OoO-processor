#=========================================================================
# CacheFL_test.py
#=========================================================================

import pytest

from random import seed, randint

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
    0x00001000, 0x000c0ffe,
    0x00001004, 0x10101010,
    0x00001008, 0x20202020,
    0x0000100c, 0x30303030,
    0x00001010, 0x40404040,
    0x00001014, 0x50505050,
    0x00001018, 0x60606060,
    0x0000101c, 0x70707070,
    0x00001020, 0x80808080,
    0x00001024, 0x90909090,
    0x00001028, 0xa0a0a0a0,
    0x0000102c, 0xb0b0b0b0,
    0x00001030, 0xc0c0c0c0,
    0x00001034, 0xd0d0d0d0,
    0x00001038, 0xe0e0e0e0,
    0x0000103c, 0xf0f0f0f0,
  ]

# 16KB of sequential data

def data_16KB():
  data = []
  for i in range(4096):
    data.extend([0x00001000+i*4,0xabcd1000+i*4])
  return data

# 1024B of random data

def data_random():
  seed(0xdeadbeef)
  data = []
  for i in range(256):
    data.extend([0x00001000+i*4,randint(0,0xffffffff)])
  return data

#----------------------------------------------------------------------
# Test Cases for Write Init
#----------------------------------------------------------------------

# Just make sure a single write init goes through the memory system.

def write_init_word():
  return [
    #    type  opq  addr   len data                type  opq  test len data
    req( 'in', 0x0, 0x1000, 4, 0xdeadbeef ), resp( 'in', 0x0, 0,   4,  0    ),
  ]

# Write init a word multiple times, also tests opaque bits

def write_init_multi_word():
  return [
    #    type  opq  addr   len data                type  opq  test len data
    req( 'in', 0x0, 0x1000, 4, 0xdeadbeef ), resp( 'in', 0x0, 0,   4,  0    ),
    req( 'in', 0x1, 0x1000, 4, 0xdeadbeef ), resp( 'in', 0x1, 0,   4,  0    ),
    req( 'in', 0x2, 0x1000, 4, 0xdeadbeef ), resp( 'in', 0x2, 0,   4,  0    ),
    req( 'in', 0x3, 0x1000, 4, 0xdeadbeef ), resp( 'in', 0x3, 0,   4,  0    ),
  ]

# Use write inits for each word in a cache line

def write_init_cacheline():
  return [
    #    type  opq  addr   len data                type  opq  test len data
    req( 'in', 0x0, 0x1000, 4, 0x01010101 ), resp( 'in', 0x0, 0,   4,  0    ),
    req( 'in', 0x1, 0x1004, 4, 0x02020202 ), resp( 'in', 0x1, 0,   4,  0    ),
    req( 'in', 0x2, 0x1008, 4, 0x03030303 ), resp( 'in', 0x2, 0,   4,  0    ),
    req( 'in', 0x3, 0x100c, 4, 0x04040404 ), resp( 'in', 0x3, 0,   4,  0    ),
  ]

# Write init one word in each cacheline in half the cache. For the direct
# mapped cache, this will write the first half of all the sets. For the
# set associative cache, this will write all of the sets in the first
# way.

def write_init_multi_cacheline():
  return [
    #    type  opq  addr   len data                type  opq  test len data
    req( 'in', 0x0, 0x0000, 4, 0x00000000 ), resp( 'in', 0x0, 0,   4,  0    ),
    req( 'in', 0x1, 0x1010, 4, 0x01010101 ), resp( 'in', 0x1, 0,   4,  0    ),
    req( 'in', 0x2, 0x2020, 4, 0x02020202 ), resp( 'in', 0x2, 0,   4,  0    ),
    req( 'in', 0x3, 0x3030, 4, 0x03030303 ), resp( 'in', 0x3, 0,   4,  0    ),
    req( 'in', 0x4, 0x4040, 4, 0x04040404 ), resp( 'in', 0x4, 0,   4,  0    ),
    req( 'in', 0x5, 0x5050, 4, 0x05050505 ), resp( 'in', 0x5, 0,   4,  0    ),
    req( 'in', 0x6, 0x6060, 4, 0x06060606 ), resp( 'in', 0x6, 0,   4,  0    ),
    req( 'in', 0x7, 0x7070, 4, 0x07070707 ), resp( 'in', 0x7, 0,   4,  0    ),
  ]

#----------------------------------------------------------------------
# Test Cases for Read Hits
#----------------------------------------------------------------------

# Single read hit

def read_hit_word():
  return [
    #    type  opq  addr   len data                type  opq  test len data
    req( 'in', 0x0, 0x1000, 4, 0xdeadbeef ), resp( 'in', 0x0, 0,   4,  0          ),
    req( 'rd', 0x0, 0x1000, 4, 0          ), resp( 'rd', 0x0, 1,   4,  0xdeadbeef ),
  ]

# Read same word multiple times, also tests opaque bits

def read_hit_multi_word():
  return [
    #    type  opq  addr   len data                type  opq  test len data
    req( 'in', 0x0, 0x1000, 4, 0xdeadbeef ), resp( 'in', 0x0, 0,   4,  0    ),

    req( 'rd', 0x0, 0x1000, 4, 0          ), resp( 'rd', 0x0, 1,   4,  0xdeadbeef ),
    req( 'rd', 0x1, 0x1000, 4, 0          ), resp( 'rd', 0x1, 1,   4,  0xdeadbeef ),
    req( 'rd', 0x2, 0x1000, 4, 0          ), resp( 'rd', 0x2, 1,   4,  0xdeadbeef ),
    req( 'rd', 0x3, 0x1000, 4, 0          ), resp( 'rd', 0x3, 1,   4,  0xdeadbeef ),
  ]

# Read every word in cache line

def read_hit_cacheline():
  return [
    #    type  opq  addr   len data                type  opq  test len data
    req( 'in', 0x0, 0x1000, 4, 0x01010101 ), resp( 'in', 0x0, 0,   4,  0    ),
    req( 'in', 0x1, 0x1004, 4, 0x02020202 ), resp( 'in', 0x1, 0,   4,  0    ),
    req( 'in', 0x2, 0x1008, 4, 0x03030303 ), resp( 'in', 0x2, 0,   4,  0    ),
    req( 'in', 0x3, 0x100c, 4, 0x04040404 ), resp( 'in', 0x3, 0,   4,  0    ),

    req( 'rd', 0x4, 0x1000, 4, 0          ), resp( 'rd', 0x4, 1,   4,  0x01010101 ),
    req( 'rd', 0x5, 0x1004, 4, 0          ), resp( 'rd', 0x5, 1,   4,  0x02020202 ),
    req( 'rd', 0x6, 0x1008, 4, 0          ), resp( 'rd', 0x6, 1,   4,  0x03030303 ),
    req( 'rd', 0x7, 0x100c, 4, 0          ), resp( 'rd', 0x7, 1,   4,  0x04040404 ),
  ]

# Read one word from each cacheline

def read_hit_multi_cacheline():
  return [
    #    type  opq  addr   len data                type  opq  test len data
    req( 'in', 0x0, 0x0000, 4, 0x00000000 ), resp( 'in', 0x0, 0,   4,  0          ),
    req( 'in', 0x1, 0x1010, 4, 0x01010101 ), resp( 'in', 0x1, 0,   4,  0          ),
    req( 'in', 0x2, 0x2020, 4, 0x02020202 ), resp( 'in', 0x2, 0,   4,  0          ),
    req( 'in', 0x3, 0x3030, 4, 0x03030303 ), resp( 'in', 0x3, 0,   4,  0          ),
    req( 'in', 0x4, 0x4040, 4, 0x04040404 ), resp( 'in', 0x4, 0,   4,  0          ),
    req( 'in', 0x5, 0x5050, 4, 0x05050505 ), resp( 'in', 0x5, 0,   4,  0          ),
    req( 'in', 0x6, 0x6060, 4, 0x06060606 ), resp( 'in', 0x6, 0,   4,  0          ),
    req( 'in', 0x7, 0x7070, 4, 0x07070707 ), resp( 'in', 0x7, 0,   4,  0          ),

    req( 'rd', 0x0, 0x0000, 4, 0          ), resp( 'rd', 0x0, 1,   4,  0x00000000 ),
    req( 'rd', 0x1, 0x1010, 4, 0          ), resp( 'rd', 0x1, 1,   4,  0x01010101 ),
    req( 'rd', 0x2, 0x2020, 4, 0          ), resp( 'rd', 0x2, 1,   4,  0x02020202 ),
    req( 'rd', 0x3, 0x3030, 4, 0          ), resp( 'rd', 0x3, 1,   4,  0x03030303 ),
    req( 'rd', 0x4, 0x4040, 4, 0          ), resp( 'rd', 0x4, 1,   4,  0x04040404 ),
    req( 'rd', 0x5, 0x5050, 4, 0          ), resp( 'rd', 0x5, 1,   4,  0x05050505 ),
    req( 'rd', 0x6, 0x6060, 4, 0          ), resp( 'rd', 0x6, 1,   4,  0x06060606 ),
    req( 'rd', 0x7, 0x7070, 4, 0          ), resp( 'rd', 0x7, 1,   4,  0x07070707 ),
  ]

#----------------------------------------------------------------------
# Test Cases for Write Hits
#----------------------------------------------------------------------

# Single write hit to one word

def write_hit_word():
  return [
    #    type  opq  addr   len data                type  opq  test len data
    req( 'in', 0x0, 0x1000, 4, 0xdeadbeef ), resp( 'in', 0x0, 0,   4,  0          ),
    req( 'wr', 0x0, 0x1000, 4, 0xcafecafe ), resp( 'wr', 0x0, 1,   4,  0          ),
    req( 'rd', 0x0, 0x1000, 4, 0          ), resp( 'rd', 0x0, 1,   4,  0xcafecafe ),
  ]

# Write/read word multiple times, also tests opaque bits

def write_hit_multi_word():
  return [
    #    type  opq  addr   len data                type  opq  test len data
    req( 'in', 0x0, 0x1000, 4, 0xdeadbeef ), resp( 'in', 0x0, 0,   4,  0          ),

    req( 'wr', 0x1, 0x1000, 4, 0x01010101 ), resp( 'wr', 0x1, 1,   4,  0          ),
    req( 'rd', 0x2, 0x1000, 4, 0          ), resp( 'rd', 0x2, 1,   4,  0x01010101 ),
    req( 'wr', 0x3, 0x1000, 4, 0x02020202 ), resp( 'wr', 0x3, 1,   4,  0          ),
    req( 'rd', 0x4, 0x1000, 4, 0          ), resp( 'rd', 0x4, 1,   4,  0x02020202 ),
    req( 'wr', 0x5, 0x1000, 4, 0x03030303 ), resp( 'wr', 0x5, 1,   4,  0          ),
    req( 'rd', 0x6, 0x1000, 4, 0          ), resp( 'rd', 0x6, 1,   4,  0x03030303 ),
    req( 'wr', 0x7, 0x1000, 4, 0x04040404 ), resp( 'wr', 0x7, 1,   4,  0          ),
    req( 'rd', 0x8, 0x1000, 4, 0          ), resp( 'rd', 0x8, 1,   4,  0x04040404 ),
  ]

# Write/read every word in cache line

def write_hit_cacheline():
  return [
    #    type  opq  addr   len data                type  opq  test len data
    req( 'in', 0x0, 0x1000, 4, 0x01010101 ), resp( 'in', 0x0, 0,   4,  0          ),
    req( 'in', 0x0, 0x1004, 4, 0x02020202 ), resp( 'in', 0x0, 0,   4,  0          ),
    req( 'in', 0x0, 0x1008, 4, 0x03030303 ), resp( 'in', 0x0, 0,   4,  0          ),
    req( 'in', 0x0, 0x100c, 4, 0x04040404 ), resp( 'in', 0x0, 0,   4,  0          ),

    req( 'wr', 0x1, 0x1000, 4, 0x01010101 ), resp( 'wr', 0x1, 1,   4,  0          ),
    req( 'wr', 0x3, 0x1004, 4, 0x02020202 ), resp( 'wr', 0x3, 1,   4,  0          ),
    req( 'wr', 0x5, 0x1008, 4, 0x03030303 ), resp( 'wr', 0x5, 1,   4,  0          ),
    req( 'wr', 0x7, 0x100c, 4, 0x04040404 ), resp( 'wr', 0x7, 1,   4,  0          ),

    req( 'rd', 0x2, 0x1000, 4, 0          ), resp( 'rd', 0x2, 1,   4,  0x01010101 ),
    req( 'rd', 0x4, 0x1004, 4, 0          ), resp( 'rd', 0x4, 1,   4,  0x02020202 ),
    req( 'rd', 0x6, 0x1008, 4, 0          ), resp( 'rd', 0x6, 1,   4,  0x03030303 ),
    req( 'rd', 0x8, 0x100c, 4, 0          ), resp( 'rd', 0x8, 1,   4,  0x04040404 ),
  ]

# Write/read one word from each cacheline

def write_hit_multi_cacheline():
  return [
    #    type  opq  addr   len data                type  opq  test len data
    req( 'in', 0x0, 0x0000, 4, 0x00000000 ), resp( 'in', 0x0, 0,   4,  0          ),
    req( 'in', 0x1, 0x1010, 4, 0x01010101 ), resp( 'in', 0x1, 0,   4,  0          ),
    req( 'in', 0x2, 0x2020, 4, 0x02020202 ), resp( 'in', 0x2, 0,   4,  0          ),
    req( 'in', 0x3, 0x3030, 4, 0x03030303 ), resp( 'in', 0x3, 0,   4,  0          ),
    req( 'in', 0x4, 0x4040, 4, 0x04040404 ), resp( 'in', 0x4, 0,   4,  0          ),
    req( 'in', 0x5, 0x5050, 4, 0x05050505 ), resp( 'in', 0x5, 0,   4,  0          ),
    req( 'in', 0x6, 0x6060, 4, 0x06060606 ), resp( 'in', 0x6, 0,   4,  0          ),
    req( 'in', 0x7, 0x7070, 4, 0x07070707 ), resp( 'in', 0x7, 0,   4,  0          ),

    req( 'wr', 0x0, 0x0000, 4, 0x10101010 ), resp( 'wr', 0x0, 1,   4,  0          ),
    req( 'wr', 0x1, 0x1010, 4, 0x11111111 ), resp( 'wr', 0x1, 1,   4,  0          ),
    req( 'wr', 0x2, 0x2020, 4, 0x12121212 ), resp( 'wr', 0x2, 1,   4,  0          ),
    req( 'wr', 0x3, 0x3030, 4, 0x13131313 ), resp( 'wr', 0x3, 1,   4,  0          ),
    req( 'wr', 0x4, 0x4040, 4, 0x14141414 ), resp( 'wr', 0x4, 1,   4,  0          ),
    req( 'wr', 0x5, 0x5050, 4, 0x15151515 ), resp( 'wr', 0x5, 1,   4,  0          ),
    req( 'wr', 0x6, 0x6060, 4, 0x16161616 ), resp( 'wr', 0x6, 1,   4,  0          ),
    req( 'wr', 0x7, 0x7070, 4, 0x17171717 ), resp( 'wr', 0x7, 1,   4,  0          ),

    req( 'rd', 0x0, 0x0000, 4, 0          ), resp( 'rd', 0x0, 1,   4,  0x10101010 ),
    req( 'rd', 0x1, 0x1010, 4, 0          ), resp( 'rd', 0x1, 1,   4,  0x11111111 ),
    req( 'rd', 0x2, 0x2020, 4, 0          ), resp( 'rd', 0x2, 1,   4,  0x12121212 ),
    req( 'rd', 0x3, 0x3030, 4, 0          ), resp( 'rd', 0x3, 1,   4,  0x13131313 ),
    req( 'rd', 0x4, 0x4040, 4, 0          ), resp( 'rd', 0x4, 1,   4,  0x14141414 ),
    req( 'rd', 0x5, 0x5050, 4, 0          ), resp( 'rd', 0x5, 1,   4,  0x15151515 ),
    req( 'rd', 0x6, 0x6060, 4, 0          ), resp( 'rd', 0x6, 1,   4,  0x16161616 ),
    req( 'rd', 0x7, 0x7070, 4, 0          ), resp( 'rd', 0x7, 1,   4,  0x17171717 ),
  ]

#----------------------------------------------------------------------
# Test Cases for Refill on Read Miss
#----------------------------------------------------------------------

# Single read miss (uses data_64B)

def read_miss_word():
  return [
    #    type  opq  addr   len data                type  opq  test len data
    req( 'rd', 0x0, 0x1000, 4, 0          ), resp( 'rd', 0x0, 0,   4,  0x000c0ffe ),
  ]

# Read same word multiple times, also tests opaque bits (uses data_64B)

def read_miss_multi_word():
  return [
    #    type  opq  addr   len data                type  opq  test len data
    req( 'rd', 0x0, 0x1000, 4, 0          ), resp( 'rd', 0x0, 0,   4,  0x000c0ffe ),
    req( 'rd', 0x1, 0x1000, 4, 0          ), resp( 'rd', 0x1, 1,   4,  0x000c0ffe ),
    req( 'rd', 0x2, 0x1000, 4, 0          ), resp( 'rd', 0x2, 1,   4,  0x000c0ffe ),
    req( 'rd', 0x3, 0x1000, 4, 0          ), resp( 'rd', 0x3, 1,   4,  0x000c0ffe ),
  ]

# Read every word in cache line (uses data_64B)

def read_miss_cacheline():
  return [
    #    type  opq  addr   len data                type  opq  test len data
    req( 'rd', 0x1, 0x1000, 4, 0          ), resp( 'rd', 0x1, 0,   4,  0x000c0ffe ),
    req( 'rd', 0x2, 0x1004, 4, 0          ), resp( 'rd', 0x2, 1,   4,  0x10101010 ),
    req( 'rd', 0x3, 0x1008, 4, 0          ), resp( 'rd', 0x3, 1,   4,  0x20202020 ),
    req( 'rd', 0x4, 0x100c, 4, 0          ), resp( 'rd', 0x4, 1,   4,  0x30303030 ),
  ]

# Read miss for each cacheline, then read hit for each cacheline (uses data_16KB)

def read_miss_multi_cacheline():
  return [
    #    type  opq  addr   len data                type  opq  test len data
    req( 'rd', 0x0, 0x1000, 4, 0          ), resp( 'rd', 0x0, 0,   4,  0xabcd1000 ),
    req( 'rd', 0x1, 0x1010, 4, 0          ), resp( 'rd', 0x1, 0,   4,  0xabcd1010 ),
    req( 'rd', 0x2, 0x1020, 4, 0          ), resp( 'rd', 0x2, 0,   4,  0xabcd1020 ),
    req( 'rd', 0x3, 0x1030, 4, 0          ), resp( 'rd', 0x3, 0,   4,  0xabcd1030 ),
    req( 'rd', 0x4, 0x1040, 4, 0          ), resp( 'rd', 0x4, 0,   4,  0xabcd1040 ),
    req( 'rd', 0x5, 0x1050, 4, 0          ), resp( 'rd', 0x5, 0,   4,  0xabcd1050 ),
    req( 'rd', 0x6, 0x1060, 4, 0          ), resp( 'rd', 0x6, 0,   4,  0xabcd1060 ),
    req( 'rd', 0x7, 0x1070, 4, 0          ), resp( 'rd', 0x7, 0,   4,  0xabcd1070 ),
    req( 'rd', 0x8, 0x1080, 4, 0          ), resp( 'rd', 0x8, 0,   4,  0xabcd1080 ),
    req( 'rd', 0x9, 0x1090, 4, 0          ), resp( 'rd', 0x9, 0,   4,  0xabcd1090 ),
    req( 'rd', 0xa, 0x10a0, 4, 0          ), resp( 'rd', 0xa, 0,   4,  0xabcd10a0 ),
    req( 'rd', 0xb, 0x10b0, 4, 0          ), resp( 'rd', 0xb, 0,   4,  0xabcd10b0 ),
    req( 'rd', 0xc, 0x10c0, 4, 0          ), resp( 'rd', 0xc, 0,   4,  0xabcd10c0 ),
    req( 'rd', 0xd, 0x10d0, 4, 0          ), resp( 'rd', 0xd, 0,   4,  0xabcd10d0 ),
    req( 'rd', 0xe, 0x10e0, 4, 0          ), resp( 'rd', 0xe, 0,   4,  0xabcd10e0 ),
    req( 'rd', 0xf, 0x10f0, 4, 0          ), resp( 'rd', 0xf, 0,   4,  0xabcd10f0 ),

    req( 'rd', 0x0, 0x1000, 4, 0          ), resp( 'rd', 0x0, 1,   4,  0xabcd1000 ),
    req( 'rd', 0x1, 0x1010, 4, 0          ), resp( 'rd', 0x1, 1,   4,  0xabcd1010 ),
    req( 'rd', 0x2, 0x1020, 4, 0          ), resp( 'rd', 0x2, 1,   4,  0xabcd1020 ),
    req( 'rd', 0x3, 0x1030, 4, 0          ), resp( 'rd', 0x3, 1,   4,  0xabcd1030 ),
    req( 'rd', 0x4, 0x1040, 4, 0          ), resp( 'rd', 0x4, 1,   4,  0xabcd1040 ),
    req( 'rd', 0x5, 0x1050, 4, 0          ), resp( 'rd', 0x5, 1,   4,  0xabcd1050 ),
    req( 'rd', 0x6, 0x1060, 4, 0          ), resp( 'rd', 0x6, 1,   4,  0xabcd1060 ),
    req( 'rd', 0x7, 0x1070, 4, 0          ), resp( 'rd', 0x7, 1,   4,  0xabcd1070 ),
    req( 'rd', 0x8, 0x1080, 4, 0          ), resp( 'rd', 0x8, 1,   4,  0xabcd1080 ),
    req( 'rd', 0x9, 0x1090, 4, 0          ), resp( 'rd', 0x9, 1,   4,  0xabcd1090 ),
    req( 'rd', 0xa, 0x10a0, 4, 0          ), resp( 'rd', 0xa, 1,   4,  0xabcd10a0 ),
    req( 'rd', 0xb, 0x10b0, 4, 0          ), resp( 'rd', 0xb, 1,   4,  0xabcd10b0 ),
    req( 'rd', 0xc, 0x10c0, 4, 0          ), resp( 'rd', 0xc, 1,   4,  0xabcd10c0 ),
    req( 'rd', 0xd, 0x10d0, 4, 0          ), resp( 'rd', 0xd, 1,   4,  0xabcd10d0 ),
    req( 'rd', 0xe, 0x10e0, 4, 0          ), resp( 'rd', 0xe, 1,   4,  0xabcd10e0 ),
    req( 'rd', 0xf, 0x10f0, 4, 0          ), resp( 'rd', 0xf, 1,   4,  0xabcd10f0 ),

    req( 'rd', 0x0, 0x1004, 4, 0          ), resp( 'rd', 0x0, 1,   4,  0xabcd1004 ),
    req( 'rd', 0x1, 0x1014, 4, 0          ), resp( 'rd', 0x1, 1,   4,  0xabcd1014 ),
    req( 'rd', 0x2, 0x1024, 4, 0          ), resp( 'rd', 0x2, 1,   4,  0xabcd1024 ),
    req( 'rd', 0x3, 0x1034, 4, 0          ), resp( 'rd', 0x3, 1,   4,  0xabcd1034 ),
    req( 'rd', 0x4, 0x1044, 4, 0          ), resp( 'rd', 0x4, 1,   4,  0xabcd1044 ),
    req( 'rd', 0x5, 0x1054, 4, 0          ), resp( 'rd', 0x5, 1,   4,  0xabcd1054 ),
    req( 'rd', 0x6, 0x1064, 4, 0          ), resp( 'rd', 0x6, 1,   4,  0xabcd1064 ),
    req( 'rd', 0x7, 0x1074, 4, 0          ), resp( 'rd', 0x7, 1,   4,  0xabcd1074 ),
    req( 'rd', 0x8, 0x1084, 4, 0          ), resp( 'rd', 0x8, 1,   4,  0xabcd1084 ),
    req( 'rd', 0x9, 0x1094, 4, 0          ), resp( 'rd', 0x9, 1,   4,  0xabcd1094 ),
    req( 'rd', 0xa, 0x10a4, 4, 0          ), resp( 'rd', 0xa, 1,   4,  0xabcd10a4 ),
    req( 'rd', 0xb, 0x10b4, 4, 0          ), resp( 'rd', 0xb, 1,   4,  0xabcd10b4 ),
    req( 'rd', 0xc, 0x10c4, 4, 0          ), resp( 'rd', 0xc, 1,   4,  0xabcd10c4 ),
    req( 'rd', 0xd, 0x10d4, 4, 0          ), resp( 'rd', 0xd, 1,   4,  0xabcd10d4 ),
    req( 'rd', 0xe, 0x10e4, 4, 0          ), resp( 'rd', 0xe, 1,   4,  0xabcd10e4 ),
    req( 'rd', 0xf, 0x10f4, 4, 0          ), resp( 'rd', 0xf, 1,   4,  0xabcd10f4 ),
  ]

#----------------------------------------------------------------------
# Test Cases for Refill on Write Miss
#----------------------------------------------------------------------

# Single write miss to one word (uses data_64B)

def write_miss_word():
  return [
    #    type  opq  addr   len data                type  opq  test len data
    req( 'wr', 0x0, 0x1000, 4, 0xcafecafe ), resp( 'wr', 0x0, 0,   4,  0          ),
    req( 'rd', 0x0, 0x1000, 4, 0          ), resp( 'rd', 0x0, 1,   4,  0xcafecafe ),
  ]

# Write/read word multiple times, also tests opaque bits (uses data_64B)

def write_miss_multi_word():
  return [
    #    type  opq  addr   len data                type  opq  test len data
    req( 'wr', 0x1, 0x1000, 4, 0x01010101 ), resp( 'wr', 0x1, 0,   4,  0          ),
    req( 'rd', 0x2, 0x1000, 4, 0          ), resp( 'rd', 0x2, 1,   4,  0x01010101 ),
    req( 'wr', 0x3, 0x1000, 4, 0x02020202 ), resp( 'wr', 0x3, 1,   4,  0          ),
    req( 'rd', 0x4, 0x1000, 4, 0          ), resp( 'rd', 0x4, 1,   4,  0x02020202 ),
    req( 'wr', 0x5, 0x1000, 4, 0x03030303 ), resp( 'wr', 0x5, 1,   4,  0          ),
    req( 'rd', 0x6, 0x1000, 4, 0          ), resp( 'rd', 0x6, 1,   4,  0x03030303 ),
    req( 'wr', 0x7, 0x1000, 4, 0x04040404 ), resp( 'wr', 0x7, 1,   4,  0          ),
    req( 'rd', 0x8, 0x1000, 4, 0          ), resp( 'rd', 0x8, 1,   4,  0x04040404 ),
  ]

# Write/read every word in cache line (uses data_64B)

def write_miss_cacheline():
  return [
    #    type  opq  addr   len data                type  opq  test len data
    req( 'wr', 0x1, 0x1000, 4, 0x01010101 ), resp( 'wr', 0x1, 0,   4,  0          ),
    req( 'wr', 0x2, 0x1004, 4, 0x02020202 ), resp( 'wr', 0x2, 1,   4,  0          ),
    req( 'wr', 0x3, 0x1008, 4, 0x03030303 ), resp( 'wr', 0x3, 1,   4,  0          ),
    req( 'wr', 0x4, 0x100c, 4, 0x04040404 ), resp( 'wr', 0x4, 1,   4,  0          ),

    req( 'rd', 0x5, 0x1000, 4, 0          ), resp( 'rd', 0x5, 1,   4,  0x01010101 ),
    req( 'rd', 0x6, 0x1004, 4, 0          ), resp( 'rd', 0x6, 1,   4,  0x02020202 ),
    req( 'rd', 0x7, 0x1008, 4, 0          ), resp( 'rd', 0x7, 1,   4,  0x03030303 ),
    req( 'rd', 0x8, 0x100c, 4, 0          ), resp( 'rd', 0x8, 1,   4,  0x04040404 ),
  ]

# Write/read one word from each cacheline (uses data_16KB)

def write_miss_multi_cacheline():
  return [
    #    type  opq  addr   len data                type  opq  test len data
    req( 'wr', 0x0, 0x1000, 4, 0x10101010 ), resp( 'wr', 0x0, 0,   4,  0          ),
    req( 'wr', 0x1, 0x1010, 4, 0x11111111 ), resp( 'wr', 0x1, 0,   4,  0          ),
    req( 'wr', 0x2, 0x1020, 4, 0x12121212 ), resp( 'wr', 0x2, 0,   4,  0          ),
    req( 'wr', 0x3, 0x1030, 4, 0x13131313 ), resp( 'wr', 0x3, 0,   4,  0          ),
    req( 'wr', 0x4, 0x1040, 4, 0x14141414 ), resp( 'wr', 0x4, 0,   4,  0          ),
    req( 'wr', 0x5, 0x1050, 4, 0x15151515 ), resp( 'wr', 0x5, 0,   4,  0          ),
    req( 'wr', 0x6, 0x1060, 4, 0x16161616 ), resp( 'wr', 0x6, 0,   4,  0          ),
    req( 'wr', 0x7, 0x1070, 4, 0x17171717 ), resp( 'wr', 0x7, 0,   4,  0          ),
    req( 'wr', 0x8, 0x1080, 4, 0x18181818 ), resp( 'wr', 0x8, 0,   4,  0          ),
    req( 'wr', 0x9, 0x1090, 4, 0x19191919 ), resp( 'wr', 0x9, 0,   4,  0          ),
    req( 'wr', 0xa, 0x10a0, 4, 0x1a1a1a1a ), resp( 'wr', 0xa, 0,   4,  0          ),
    req( 'wr', 0xb, 0x10b0, 4, 0x1b1b1b1b ), resp( 'wr', 0xb, 0,   4,  0          ),
    req( 'wr', 0xc, 0x10c0, 4, 0x1c1c1c1c ), resp( 'wr', 0xc, 0,   4,  0          ),
    req( 'wr', 0xd, 0x10d0, 4, 0x1d1d1d1d ), resp( 'wr', 0xd, 0,   4,  0          ),
    req( 'wr', 0xe, 0x10e0, 4, 0x1e1e1e1e ), resp( 'wr', 0xe, 0,   4,  0          ),
    req( 'wr', 0xf, 0x10f0, 4, 0x1f1f1f1f ), resp( 'wr', 0xf, 0,   4,  0          ),

    req( 'rd', 0x0, 0x1000, 4, 0          ), resp( 'rd', 0x0, 1,   4,  0x10101010 ),
    req( 'rd', 0x1, 0x1010, 4, 0          ), resp( 'rd', 0x1, 1,   4,  0x11111111 ),
    req( 'rd', 0x2, 0x1020, 4, 0          ), resp( 'rd', 0x2, 1,   4,  0x12121212 ),
    req( 'rd', 0x3, 0x1030, 4, 0          ), resp( 'rd', 0x3, 1,   4,  0x13131313 ),
    req( 'rd', 0x4, 0x1040, 4, 0          ), resp( 'rd', 0x4, 1,   4,  0x14141414 ),
    req( 'rd', 0x5, 0x1050, 4, 0          ), resp( 'rd', 0x5, 1,   4,  0x15151515 ),
    req( 'rd', 0x6, 0x1060, 4, 0          ), resp( 'rd', 0x6, 1,   4,  0x16161616 ),
    req( 'rd', 0x7, 0x1070, 4, 0          ), resp( 'rd', 0x7, 1,   4,  0x17171717 ),
    req( 'rd', 0x8, 0x1080, 4, 0          ), resp( 'rd', 0x8, 1,   4,  0x18181818 ),
    req( 'rd', 0x9, 0x1090, 4, 0          ), resp( 'rd', 0x9, 1,   4,  0x19191919 ),
    req( 'rd', 0xa, 0x10a0, 4, 0          ), resp( 'rd', 0xa, 1,   4,  0x1a1a1a1a ),
    req( 'rd', 0xb, 0x10b0, 4, 0          ), resp( 'rd', 0xb, 1,   4,  0x1b1b1b1b ),
    req( 'rd', 0xc, 0x10c0, 4, 0          ), resp( 'rd', 0xc, 1,   4,  0x1c1c1c1c ),
    req( 'rd', 0xd, 0x10d0, 4, 0          ), resp( 'rd', 0xd, 1,   4,  0x1d1d1d1d ),
    req( 'rd', 0xe, 0x10e0, 4, 0          ), resp( 'rd', 0xe, 1,   4,  0x1e1e1e1e ),
    req( 'rd', 0xf, 0x10f0, 4, 0          ), resp( 'rd', 0xf, 1,   4,  0x1f1f1f1f ),
  ]

#----------------------------------------------------------------------
# Test Cases for Evict
#----------------------------------------------------------------------

# Write miss to two cachelines, and then a read to a third cacheline.
# This read to the third cacheline is guaranteed to cause an eviction on
# both the direct mapped and set associative caches. (uses data_16KB)

def evict_word():
  return [
    #    type  opq  addr   len data                type  opq  test len data
    req( 'wr', 0x0, 0x1000, 4, 0xcafecafe ), resp( 'wr', 0x0, 0,   4,  0          ),
    req( 'rd', 0x0, 0x1000, 4, 0          ), resp( 'rd', 0x0, 1,   4,  0xcafecafe ),
    req( 'wr', 0x0, 0x2000, 4, 0x000c0ffe ), resp( 'wr', 0x0, 0,   4,  0          ),
    req( 'rd', 0x0, 0x2000, 4, 0          ), resp( 'rd', 0x0, 1,   4,  0x000c0ffe ),
    req( 'rd', 0x0, 0x3000, 4, 0          ), resp( 'rd', 0x0, 0,   4,  0xabcd3000 ), # conflicts
    req( 'rd', 0x0, 0x1000, 4, 0          ), resp( 'rd', 0x0, 0,   4,  0xcafecafe ),
  ]

# Write word and evict multiple times. Test is carefully crafted to
# ensure it applies to both direct mapped and set associative caches.
# (uses data_16KB)

def evict_multi_word():
  return [
    #    type  opq  addr   len data                type  opq  test len data
    req( 'wr', 0x0, 0x1000, 4, 0x01010101 ), resp( 'wr', 0x0, 0,   4,  0          ),
    req( 'rd', 0x1, 0x1000, 4, 0          ), resp( 'rd', 0x1, 1,   4,  0x01010101 ),
    req( 'wr', 0x2, 0x2000, 4, 0x11111111 ), resp( 'wr', 0x2, 0,   4,  0          ),
    req( 'rd', 0x3, 0x2000, 4, 0          ), resp( 'rd', 0x3, 1,   4,  0x11111111 ),
    req( 'rd', 0x4, 0x3000, 4, 0          ), resp( 'rd', 0x4, 0,   4,  0xabcd3000 ), # conflicts
    req( 'rd', 0x5, 0x2000, 4, 0          ), resp( 'rd', 0x5, 1,   4,  0x11111111 ), # make sure way1 is still LRU

    req( 'wr', 0x6, 0x1000, 4, 0x02020202 ), resp( 'wr', 0x6, 0,   4,  0          ),
    req( 'rd', 0x7, 0x1000, 4, 0          ), resp( 'rd', 0x7, 1,   4,  0x02020202 ),
    req( 'wr', 0x8, 0x2000, 4, 0x12121212 ), resp( 'wr', 0x8, 1,   4,  0          ),
    req( 'rd', 0x9, 0x2000, 4, 0          ), resp( 'rd', 0x9, 1,   4,  0x12121212 ),
    req( 'rd', 0xa, 0x3000, 4, 0          ), resp( 'rd', 0xa, 0,   4,  0xabcd3000 ), # conflicts
    req( 'rd', 0xb, 0x2000, 4, 0          ), resp( 'rd', 0xb, 1,   4,  0x12121212 ), # make sure way1 is still LRU

    req( 'wr', 0xc, 0x1000, 4, 0x03030303 ), resp( 'wr', 0xc, 0,   4,  0          ),
    req( 'rd', 0xd, 0x1000, 4, 0          ), resp( 'rd', 0xd, 1,   4,  0x03030303 ),
    req( 'wr', 0xe, 0x2000, 4, 0x13131313 ), resp( 'wr', 0xe, 1,   4,  0          ),
    req( 'rd', 0xf, 0x2000, 4, 0          ), resp( 'rd', 0xf, 1,   4,  0x13131313 ),
    req( 'rd', 0x0, 0x3000, 4, 0          ), resp( 'rd', 0x0, 0,   4,  0xabcd3000 ), # conflicts
    req( 'rd', 0x1, 0x2000, 4, 0          ), resp( 'rd', 0x1, 1,   4,  0x13131313 ), # make sure way1 is still LRU

    req( 'wr', 0x2, 0x1000, 4, 0x04040404 ), resp( 'wr', 0x2, 0,   4,  0          ),
    req( 'rd', 0x3, 0x1000, 4, 0          ), resp( 'rd', 0x3, 1,   4,  0x04040404 ),
    req( 'wr', 0x4, 0x2000, 4, 0x14141414 ), resp( 'wr', 0x4, 1,   4,  0          ),
    req( 'rd', 0x5, 0x2000, 4, 0          ), resp( 'rd', 0x5, 1,   4,  0x14141414 ),
    req( 'rd', 0x6, 0x3000, 4, 0          ), resp( 'rd', 0x6, 0,   4,  0xabcd3000 ), # conflicts
    req( 'rd', 0x7, 0x2000, 4, 0          ), resp( 'rd', 0x7, 1,   4,  0x14141414 ), # make sure way1 is still LRU

    req( 'rd', 0x8, 0x1000, 4, 0          ), resp( 'rd', 0x8, 0,   4,  0x04040404 ),
  ]

# Write every word on two cachelines, and then a read to a third
# cacheline. This read to the third cacheline is guaranteed to cause an
# eviction on both the direct mapped and set associative caches. (uses
# data_16KB)

def evict_cacheline():
  return [
    #    type  opq  addr   len data                type  opq  test len data
    req( 'wr', 0x0, 0x1000, 4, 0x01010101 ), resp( 'wr', 0x0, 0,   4,  0          ),
    req( 'wr', 0x1, 0x1004, 4, 0x02020202 ), resp( 'wr', 0x1, 1,   4,  0          ),
    req( 'wr', 0x2, 0x1008, 4, 0x03030303 ), resp( 'wr', 0x2, 1,   4,  0          ),
    req( 'wr', 0x3, 0x100c, 4, 0x04040404 ), resp( 'wr', 0x3, 1,   4,  0          ),

    req( 'wr', 0x4, 0x2000, 4, 0x11111111 ), resp( 'wr', 0x4, 0,   4,  0          ),
    req( 'wr', 0x5, 0x2004, 4, 0x12121212 ), resp( 'wr', 0x5, 1,   4,  0          ),
    req( 'wr', 0x6, 0x2008, 4, 0x13131313 ), resp( 'wr', 0x6, 1,   4,  0          ),
    req( 'wr', 0x7, 0x200c, 4, 0x14141414 ), resp( 'wr', 0x7, 1,   4,  0          ),

    req( 'rd', 0x8, 0x3000, 4, 0          ), resp( 'rd', 0x8, 0,   4,  0xabcd3000 ), # conflicts

    req( 'rd', 0x9, 0x1000, 4, 0          ), resp( 'rd', 0x9, 0,   4,  0x01010101 ),
    req( 'rd', 0xa, 0x1004, 4, 0          ), resp( 'rd', 0xa, 1,   4,  0x02020202 ),
    req( 'rd', 0xb, 0x1008, 4, 0          ), resp( 'rd', 0xb, 1,   4,  0x03030303 ),
    req( 'rd', 0xc, 0x100c, 4, 0          ), resp( 'rd', 0xc, 1,   4,  0x04040404 ),
  ]

# Write one word from each cacheline, then evict (uses data_16KB)

def evict_multi_cacheline():
  return [
    #    type  opq  addr   len data                type  opq  test len data
    req( 'wr', 0x0, 0x1000, 4, 0x10101010 ), resp( 'wr', 0x0, 0,   4,  0          ),
    req( 'wr', 0x1, 0x1010, 4, 0x11111111 ), resp( 'wr', 0x1, 0,   4,  0          ),
    req( 'wr', 0x2, 0x1020, 4, 0x12121212 ), resp( 'wr', 0x2, 0,   4,  0          ),
    req( 'wr', 0x3, 0x1030, 4, 0x13131313 ), resp( 'wr', 0x3, 0,   4,  0          ),
    req( 'wr', 0x4, 0x1040, 4, 0x14141414 ), resp( 'wr', 0x4, 0,   4,  0          ),
    req( 'wr', 0x5, 0x1050, 4, 0x15151515 ), resp( 'wr', 0x5, 0,   4,  0          ),
    req( 'wr', 0x6, 0x1060, 4, 0x16161616 ), resp( 'wr', 0x6, 0,   4,  0          ),
    req( 'wr', 0x7, 0x1070, 4, 0x17171717 ), resp( 'wr', 0x7, 0,   4,  0          ),
    req( 'wr', 0x8, 0x1080, 4, 0x18181818 ), resp( 'wr', 0x8, 0,   4,  0          ),
    req( 'wr', 0x9, 0x1090, 4, 0x19191919 ), resp( 'wr', 0x9, 0,   4,  0          ),
    req( 'wr', 0xa, 0x10a0, 4, 0x1a1a1a1a ), resp( 'wr', 0xa, 0,   4,  0          ),
    req( 'wr', 0xb, 0x10b0, 4, 0x1b1b1b1b ), resp( 'wr', 0xb, 0,   4,  0          ),
    req( 'wr', 0xc, 0x10c0, 4, 0x1c1c1c1c ), resp( 'wr', 0xc, 0,   4,  0          ),
    req( 'wr', 0xd, 0x10d0, 4, 0x1d1d1d1d ), resp( 'wr', 0xd, 0,   4,  0          ),
    req( 'wr', 0xe, 0x10e0, 4, 0x1e1e1e1e ), resp( 'wr', 0xe, 0,   4,  0          ),
    req( 'wr', 0xf, 0x10f0, 4, 0x1f1f1f1f ), resp( 'wr', 0xf, 0,   4,  0          ),

    req( 'rd', 0x0, 0x1000, 4, 0          ), resp( 'rd', 0x0, 1,   4,  0x10101010 ),
    req( 'rd', 0x1, 0x1010, 4, 0          ), resp( 'rd', 0x1, 1,   4,  0x11111111 ),
    req( 'rd', 0x2, 0x1020, 4, 0          ), resp( 'rd', 0x2, 1,   4,  0x12121212 ),
    req( 'rd', 0x3, 0x1030, 4, 0          ), resp( 'rd', 0x3, 1,   4,  0x13131313 ),
    req( 'rd', 0x4, 0x1040, 4, 0          ), resp( 'rd', 0x4, 1,   4,  0x14141414 ),
    req( 'rd', 0x5, 0x1050, 4, 0          ), resp( 'rd', 0x5, 1,   4,  0x15151515 ),
    req( 'rd', 0x6, 0x1060, 4, 0          ), resp( 'rd', 0x6, 1,   4,  0x16161616 ),
    req( 'rd', 0x7, 0x1070, 4, 0          ), resp( 'rd', 0x7, 1,   4,  0x17171717 ),
    req( 'rd', 0x8, 0x1080, 4, 0          ), resp( 'rd', 0x8, 1,   4,  0x18181818 ),
    req( 'rd', 0x9, 0x1090, 4, 0          ), resp( 'rd', 0x9, 1,   4,  0x19191919 ),
    req( 'rd', 0xa, 0x10a0, 4, 0          ), resp( 'rd', 0xa, 1,   4,  0x1a1a1a1a ),
    req( 'rd', 0xb, 0x10b0, 4, 0          ), resp( 'rd', 0xb, 1,   4,  0x1b1b1b1b ),
    req( 'rd', 0xc, 0x10c0, 4, 0          ), resp( 'rd', 0xc, 1,   4,  0x1c1c1c1c ),
    req( 'rd', 0xd, 0x10d0, 4, 0          ), resp( 'rd', 0xd, 1,   4,  0x1d1d1d1d ),
    req( 'rd', 0xe, 0x10e0, 4, 0          ), resp( 'rd', 0xe, 1,   4,  0x1e1e1e1e ),
    req( 'rd', 0xf, 0x10f0, 4, 0          ), resp( 'rd', 0xf, 1,   4,  0x1f1f1f1f ),

    req( 'wr', 0x0, 0x2000, 4, 0x20202020 ), resp( 'wr', 0x0, 0,   4,  0          ),
    req( 'wr', 0x1, 0x2010, 4, 0x21212121 ), resp( 'wr', 0x1, 0,   4,  0          ),
    req( 'wr', 0x2, 0x2020, 4, 0x22222222 ), resp( 'wr', 0x2, 0,   4,  0          ),
    req( 'wr', 0x3, 0x2030, 4, 0x23232323 ), resp( 'wr', 0x3, 0,   4,  0          ),
    req( 'wr', 0x4, 0x2040, 4, 0x24242424 ), resp( 'wr', 0x4, 0,   4,  0          ),
    req( 'wr', 0x5, 0x2050, 4, 0x25252525 ), resp( 'wr', 0x5, 0,   4,  0          ),
    req( 'wr', 0x6, 0x2060, 4, 0x26262626 ), resp( 'wr', 0x6, 0,   4,  0          ),
    req( 'wr', 0x7, 0x2070, 4, 0x27272727 ), resp( 'wr', 0x7, 0,   4,  0          ),
    req( 'wr', 0x8, 0x2080, 4, 0x28282828 ), resp( 'wr', 0x8, 0,   4,  0          ),
    req( 'wr', 0x9, 0x2090, 4, 0x29292929 ), resp( 'wr', 0x9, 0,   4,  0          ),
    req( 'wr', 0xa, 0x20a0, 4, 0x2a2a2a2a ), resp( 'wr', 0xa, 0,   4,  0          ),
    req( 'wr', 0xb, 0x20b0, 4, 0x2b2b2b2b ), resp( 'wr', 0xb, 0,   4,  0          ),
    req( 'wr', 0xc, 0x20c0, 4, 0x2c2c2c2c ), resp( 'wr', 0xc, 0,   4,  0          ),
    req( 'wr', 0xd, 0x20d0, 4, 0x2d2d2d2d ), resp( 'wr', 0xd, 0,   4,  0          ),
    req( 'wr', 0xe, 0x20e0, 4, 0x2e2e2e2e ), resp( 'wr', 0xe, 0,   4,  0          ),
    req( 'wr', 0xf, 0x20f0, 4, 0x2f2f2f2f ), resp( 'wr', 0xf, 0,   4,  0          ),

    req( 'rd', 0x0, 0x2000, 4, 0          ), resp( 'rd', 0x0, 1,   4,  0x20202020 ),
    req( 'rd', 0x1, 0x2010, 4, 0          ), resp( 'rd', 0x1, 1,   4,  0x21212121 ),
    req( 'rd', 0x2, 0x2020, 4, 0          ), resp( 'rd', 0x2, 1,   4,  0x22222222 ),
    req( 'rd', 0x3, 0x2030, 4, 0          ), resp( 'rd', 0x3, 1,   4,  0x23232323 ),
    req( 'rd', 0x4, 0x2040, 4, 0          ), resp( 'rd', 0x4, 1,   4,  0x24242424 ),
    req( 'rd', 0x5, 0x2050, 4, 0          ), resp( 'rd', 0x5, 1,   4,  0x25252525 ),
    req( 'rd', 0x6, 0x2060, 4, 0          ), resp( 'rd', 0x6, 1,   4,  0x26262626 ),
    req( 'rd', 0x7, 0x2070, 4, 0          ), resp( 'rd', 0x7, 1,   4,  0x27272727 ),
    req( 'rd', 0x8, 0x2080, 4, 0          ), resp( 'rd', 0x8, 1,   4,  0x28282828 ),
    req( 'rd', 0x9, 0x2090, 4, 0          ), resp( 'rd', 0x9, 1,   4,  0x29292929 ),
    req( 'rd', 0xa, 0x20a0, 4, 0          ), resp( 'rd', 0xa, 1,   4,  0x2a2a2a2a ),
    req( 'rd', 0xb, 0x20b0, 4, 0          ), resp( 'rd', 0xb, 1,   4,  0x2b2b2b2b ),
    req( 'rd', 0xc, 0x20c0, 4, 0          ), resp( 'rd', 0xc, 1,   4,  0x2c2c2c2c ),
    req( 'rd', 0xd, 0x20d0, 4, 0          ), resp( 'rd', 0xd, 1,   4,  0x2d2d2d2d ),
    req( 'rd', 0xe, 0x20e0, 4, 0          ), resp( 'rd', 0xe, 1,   4,  0x2e2e2e2e ),
    req( 'rd', 0xf, 0x20f0, 4, 0          ), resp( 'rd', 0xf, 1,   4,  0x2f2f2f2f ),

    req( 'rd', 0x0, 0x3000, 4, 0          ), resp( 'rd', 0x0, 0,   4,  0xabcd3000 ), # conflicts
    req( 'rd', 0x1, 0x3010, 4, 0          ), resp( 'rd', 0x1, 0,   4,  0xabcd3010 ), # conflicts
    req( 'rd', 0x2, 0x3020, 4, 0          ), resp( 'rd', 0x2, 0,   4,  0xabcd3020 ), # conflicts
    req( 'rd', 0x3, 0x3030, 4, 0          ), resp( 'rd', 0x3, 0,   4,  0xabcd3030 ), # conflicts
    req( 'rd', 0x4, 0x3040, 4, 0          ), resp( 'rd', 0x4, 0,   4,  0xabcd3040 ), # conflicts
    req( 'rd', 0x5, 0x3050, 4, 0          ), resp( 'rd', 0x5, 0,   4,  0xabcd3050 ), # conflicts
    req( 'rd', 0x6, 0x3060, 4, 0          ), resp( 'rd', 0x6, 0,   4,  0xabcd3060 ), # conflicts
    req( 'rd', 0x7, 0x3070, 4, 0          ), resp( 'rd', 0x7, 0,   4,  0xabcd3070 ), # conflicts
    req( 'rd', 0x8, 0x3080, 4, 0          ), resp( 'rd', 0x8, 0,   4,  0xabcd3080 ), # conflicts
    req( 'rd', 0x9, 0x3090, 4, 0          ), resp( 'rd', 0x9, 0,   4,  0xabcd3090 ), # conflicts
    req( 'rd', 0xa, 0x30a0, 4, 0          ), resp( 'rd', 0xa, 0,   4,  0xabcd30a0 ), # conflicts
    req( 'rd', 0xb, 0x30b0, 4, 0          ), resp( 'rd', 0xb, 0,   4,  0xabcd30b0 ), # conflicts
    req( 'rd', 0xc, 0x30c0, 4, 0          ), resp( 'rd', 0xc, 0,   4,  0xabcd30c0 ), # conflicts
    req( 'rd', 0xd, 0x30d0, 4, 0          ), resp( 'rd', 0xd, 0,   4,  0xabcd30d0 ), # conflicts
    req( 'rd', 0xe, 0x30e0, 4, 0          ), resp( 'rd', 0xe, 0,   4,  0xabcd30e0 ), # conflicts
    req( 'rd', 0xf, 0x30f0, 4, 0          ), resp( 'rd', 0xf, 0,   4,  0xabcd30f0 ), # conflicts

    req( 'rd', 0x0, 0x1000, 4, 0          ), resp( 'rd', 0x0, 0,   4,  0x10101010 ),
    req( 'rd', 0x1, 0x1010, 4, 0          ), resp( 'rd', 0x1, 0,   4,  0x11111111 ),
    req( 'rd', 0x2, 0x1020, 4, 0          ), resp( 'rd', 0x2, 0,   4,  0x12121212 ),
    req( 'rd', 0x3, 0x1030, 4, 0          ), resp( 'rd', 0x3, 0,   4,  0x13131313 ),
    req( 'rd', 0x4, 0x1040, 4, 0          ), resp( 'rd', 0x4, 0,   4,  0x14141414 ),
    req( 'rd', 0x5, 0x1050, 4, 0          ), resp( 'rd', 0x5, 0,   4,  0x15151515 ),
    req( 'rd', 0x6, 0x1060, 4, 0          ), resp( 'rd', 0x6, 0,   4,  0x16161616 ),
    req( 'rd', 0x7, 0x1070, 4, 0          ), resp( 'rd', 0x7, 0,   4,  0x17171717 ),
    req( 'rd', 0x8, 0x1080, 4, 0          ), resp( 'rd', 0x8, 0,   4,  0x18181818 ),
    req( 'rd', 0x9, 0x1090, 4, 0          ), resp( 'rd', 0x9, 0,   4,  0x19191919 ),
    req( 'rd', 0xa, 0x10a0, 4, 0          ), resp( 'rd', 0xa, 0,   4,  0x1a1a1a1a ),
    req( 'rd', 0xb, 0x10b0, 4, 0          ), resp( 'rd', 0xb, 0,   4,  0x1b1b1b1b ),
    req( 'rd', 0xc, 0x10c0, 4, 0          ), resp( 'rd', 0xc, 0,   4,  0x1c1c1c1c ),
    req( 'rd', 0xd, 0x10d0, 4, 0          ), resp( 'rd', 0xd, 0,   4,  0x1d1d1d1d ),
    req( 'rd', 0xe, 0x10e0, 4, 0          ), resp( 'rd', 0xe, 0,   4,  0x1e1e1e1e ),
    req( 'rd', 0xf, 0x10f0, 4, 0          ), resp( 'rd', 0xf, 0,   4,  0x1f1f1f1f ),
  ]

#-------------------------------------------------------------------------
# Check valid bit
#-------------------------------------------------------------------------
# This test makes sure the cache includes the valid bit in the tag check.
# Since the simulator sets the tags to zero be default, if the cache
# doesn't check the valid bit, then there will be a hit instead of a miss
# if you do a cache request with a tag of zero.

# 4B of data

def data_4B():
  return [
    # addr      data
    0x00000000, 0xdeadbeef,
  ]

def check_valid_bit():
  return [
    #    type  opq   addr      len  data               type  opq test len  data
    req( 'rd', 0x01, 0x00000000, 4, 0          ), resp('rd', 0x01, 0, 4, 0xdeadbeef ),
  ]

#-------------------------------------------------------------------------
# Test more evictions
#-------------------------------------------------------------------------

def evict_more():
  return [
    #    type  opq   addr      len  data               type  opq test len  data
    req( 'wr', 0x00, 0x00000000, 4, 0x0a0b0c0d ), resp('wr', 0x00, 0, 4, 0          ), # write word  0x00000000
    req( 'wr', 0x01, 0x00000004, 4, 0x0e0f0102 ), resp('wr', 0x01, 1, 4, 0          ), # write word  0x00000004
    req( 'rd', 0x02, 0x00000000, 4, 0          ), resp('rd', 0x02, 1, 4, 0x0a0b0c0d ), # read  word  0x00000000
    req( 'rd', 0x03, 0x00000004, 4, 0          ), resp('rd', 0x03, 1, 4, 0x0e0f0102 ), # read  word  0x00000004

    # try forcing some conflict misses to force evictions

    req( 'wr', 0x04, 0x00004000, 4, 0xcafecafe ), resp('wr', 0x04, 0, 4, 0x0        ), # write word  0x00004000
    req( 'wr', 0x05, 0x00004004, 4, 0xebabefac ), resp('wr', 0x05, 1, 4, 0x0        ), # write word  0x00004004
    req( 'rd', 0x06, 0x00004000, 4, 0          ), resp('rd', 0x06, 1, 4, 0xcafecafe ), # read  word  0x00004000
    req( 'rd', 0x07, 0x00004004, 4, 0          ), resp('rd', 0x07, 1, 4, 0xebabefac ), # read  word  0x00004004

    req( 'wr', 0x00, 0x00008000, 4, 0xaaaeeaed ), resp('wr', 0x00, 0, 4, 0x0        ), # write word  0x00008000
    req( 'wr', 0x01, 0x00008004, 4, 0x0e0f0102 ), resp('wr', 0x01, 1, 4, 0x0        ), # write word  0x00008004
    req( 'rd', 0x03, 0x00008004, 4, 0          ), resp('rd', 0x03, 1, 4, 0x0e0f0102 ), # read  word  0x00008004
    req( 'rd', 0x02, 0x00008000, 4, 0          ), resp('rd', 0x02, 1, 4, 0xaaaeeaed ), # read  word  0x00008000

    req( 'wr', 0x04, 0x0000c000, 4, 0xcacafefe ), resp('wr', 0x04, 0, 4, 0x0        ), # write word  0x0000c000
    req( 'wr', 0x05, 0x0000c004, 4, 0xbeefbeef ), resp('wr', 0x05, 1, 4, 0x0        ), # write word  0x0000c004
    req( 'rd', 0x06, 0x0000c000, 4, 0          ), resp('rd', 0x06, 1, 4, 0xcacafefe ), # read  word  0x0000c000
    req( 'rd', 0x07, 0x0000c004, 4, 0          ), resp('rd', 0x07, 1, 4, 0xbeefbeef ), # read  word  0x0000c004

    req( 'wr', 0xf5, 0x0000c004, 4, 0xdeadbeef ), resp('wr', 0xf5, 1, 4, 0x0        ), # write word  0x0000c004
    req( 'wr', 0xd5, 0x0000d004, 4, 0xbeefbeef ), resp('wr', 0xd5, 0, 4, 0x0        ), # write word  0x0000d004
    req( 'wr', 0xe5, 0x0000e004, 4, 0xbeefbeef ), resp('wr', 0xe5, 0, 4, 0x0        ), # write word  0x0000e004
    req( 'wr', 0xc5, 0x0000f004, 4, 0xbeefbeef ), resp('wr', 0xc5, 0, 4, 0x0        ), # write word  0x0000f004

    # now refill those same cache lines to make sure we wrote to the
    # memory earlier and make sure we can read from memory

    req( 'rd', 0x06, 0x00004000, 4, 0          ), resp('rd', 0x06, 0, 4, 0xcafecafe ), # read  word  0x00004000
    req( 'rd', 0x07, 0x00004004, 4, 0          ), resp('rd', 0x07, 1, 4, 0xebabefac ), # read  word  0x00004004
    req( 'rd', 0x02, 0x00000000, 4, 0          ), resp('rd', 0x02, 0, 4, 0x0a0b0c0d ), # read  word  0x00000000
    req( 'rd', 0x03, 0x00000004, 4, 0          ), resp('rd', 0x03, 1, 4, 0x0e0f0102 ), # read  word  0x00000004
    req( 'rd', 0x03, 0x00008004, 4, 0          ), resp('rd', 0x03, 0, 4, 0x0e0f0102 ), # read  word  0x00008004
    req( 'rd', 0x02, 0x00008000, 4, 0          ), resp('rd', 0x02, 1, 4, 0xaaaeeaed ), # read  word  0x00008000
    req( 'rd', 0x06, 0x0000c000, 4, 0          ), resp('rd', 0x06, 0, 4, 0xcacafefe ), # read  word  0x0000c000
    req( 'rd', 0x07, 0x0000c004, 4, 0          ), resp('rd', 0x07, 1, 4, 0xdeadbeef ), # read  word  0x0000c004
    req( 'rd', 0x07, 0x0000d004, 4, 0          ), resp('rd', 0x07, 0, 4, 0xbeefbeef ), # read  word  0x0000d004
    req( 'rd', 0x08, 0x0000e004, 4, 0          ), resp('rd', 0x08, 0, 4, 0xbeefbeef ), # read  word  0x0000e004
    req( 'rd', 0x09, 0x0000f004, 4, 0          ), resp('rd', 0x09, 0, 4, 0xbeefbeef ), # read  word  0x0000f004
  ]

#-------------------------------------------------------------------------
# Test Case for Streaming Patterns
#-------------------------------------------------------------------------

def read_stream():
  msgs = []
  for i in range(0,128,4):
    msgs.extend([
      req( 'rd', i+0, 0x00001000+4*(i+0), 4, 0 ), resp( 'rd', i+0, 0, 4, 0xabcd1000+4*(i+0) ),
      req( 'rd', i+1, 0x00001000+4*(i+1), 4, 0 ), resp( 'rd', i+1, 1, 4, 0xabcd1000+4*(i+1) ),
      req( 'rd', i+2, 0x00001000+4*(i+2), 4, 0 ), resp( 'rd', i+2, 1, 4, 0xabcd1000+4*(i+2) ),
      req( 'rd', i+3, 0x00001000+4*(i+3), 4, 0 ), resp( 'rd', i+3, 1, 4, 0xabcd1000+4*(i+3) ),
    ])

  return msgs

def write_stream():
  msgs = []
  for i in range(0,128,4):
    msgs.extend([
      req( 'wr', i+0, 0x00001000+4*(i+0), 4, 0xcafe1000+4*(i+0) ), resp( 'wr', i+0, 0, 4, 0 ),
      req( 'wr', i+1, 0x00001000+4*(i+1), 4, 0xcafe1000+4*(i+1) ), resp( 'wr', i+1, 1, 4, 0 ),
      req( 'wr', i+2, 0x00001000+4*(i+2), 4, 0xcafe1000+4*(i+2) ), resp( 'wr', i+2, 1, 4, 0 ),
      req( 'wr', i+3, 0x00001000+4*(i+3), 4, 0xcafe1000+4*(i+3) ), resp( 'wr', i+3, 1, 4, 0 ),
    ])
  for i in range(0,128,4):
    msgs.extend([
      req( 'rd', i+0, 0x00001000+4*(i+0), 4, 0 ), resp( 'rd', i+0, 1, 4, 0xcafe1000+4*(i+0) ),
      req( 'rd', i+1, 0x00001000+4*(i+1), 4, 0 ), resp( 'rd', i+1, 1, 4, 0xcafe1000+4*(i+1) ),
      req( 'rd', i+2, 0x00001000+4*(i+2), 4, 0 ), resp( 'rd', i+2, 1, 4, 0xcafe1000+4*(i+2) ),
      req( 'rd', i+3, 0x00001000+4*(i+3), 4, 0 ), resp( 'rd', i+3, 1, 4, 0xcafe1000+4*(i+3) ),
    ])

  return msgs

#-------------------------------------------------------------------------
# Generic tests
#-------------------------------------------------------------------------

test_case_table_generic = mk_test_case_table([
  (                                    "msg_func                    mem_data_func stall lat src sink"),

  [ "write_init_word",                  write_init_word,            None,         0.0,  0,  0,  0    ],
  [ "write_init_multi_word",            write_init_multi_word,      None,         0.0,  0,  0,  0    ],
  [ "write_init_cacheline",             write_init_cacheline,       None,         0.0,  0,  0,  0    ],
  [ "write_init_multi_cacheline",       write_init_multi_cacheline, None,         0.0,  0,  0,  0    ],
  [ "write_init_multi_word_sink_delay", write_init_multi_word,      None,         0.0,  0,  0,  10   ],
  [ "write_init_multi_word_src_delay",  write_init_multi_word,      None,         0.0,  0,  10, 0    ],

  [ "read_hit_word",                    read_hit_word,              None,         0.0,  0,  0,  0    ],
  [ "read_hit_multi_word",              read_hit_multi_word,        None,         0.0,  0,  0,  0    ],
  [ "read_hit_cacheline",               read_hit_cacheline,         None,         0.0,  0,  0,  0    ],
  [ "read_hit_multi_cacheline",         read_hit_multi_cacheline,   None,         0.0,  0,  0,  0    ],
  [ "read_hit_multi_word_sink_delay",   read_hit_multi_word,        None,         0.0,  0,  0,  10   ],
  [ "read_hit_multi_word_src_delay",    read_hit_multi_word,        None,         0.0,  0,  10, 0    ],

  [ "write_hit_word",                   write_hit_word,             None,         0.0,  0,  0,  0    ],
  [ "write_hit_multi_word",             write_hit_multi_word,       None,         0.0,  0,  0,  0    ],
  [ "write_hit_cacheline",              write_hit_cacheline,        None,         0.0,  0,  0,  0    ],
  [ "write_hit_multi_cacheline",        write_hit_multi_cacheline,  None,         0.0,  0,  0,  0    ],
  [ "write_hit_multi_word_sink_delay",  write_hit_multi_word,       None,         0.0,  0,  0,  10   ],
  [ "write_hit_multi_word_src_delay",   write_hit_multi_word,       None,         0.0,  0,  10, 0    ],

  [ "read_miss_word",                   read_miss_word,             data_64B,     0.0,  0,  0,  0    ],
  [ "read_miss_multi_word",             read_miss_multi_word,       data_64B,     0.0,  0,  0,  0    ],
  [ "read_miss_cacheline",              read_miss_cacheline,        data_64B,     0.0,  0,  0,  0    ],
  [ "read_miss_multi_cacheline",        read_miss_multi_cacheline,  data_16KB,    0.0,  0,  0,  0    ],
  [ "read_miss_multi_word_sink_delay",  read_miss_multi_word,       data_64B,     0.9,  3,  0,  10   ],
  [ "read_miss_multi_word_src_delay",   read_miss_multi_word,       data_64B,     0.9,  3,  10, 0    ],

  [ "write_miss_word",                  write_miss_word,            data_64B,     0.0,  0,  0,  0    ],
  [ "write_miss_multi_word",            write_miss_multi_word,      data_64B,     0.0,  0,  0,  0    ],
  [ "write_miss_cacheline",             write_miss_cacheline,       data_64B,     0.0,  0,  0,  0    ],
  [ "write_miss_multi_cacheline",       write_miss_multi_cacheline, data_16KB,    0.0,  0,  0,  0    ],
  [ "write_miss_multi_word_sink_delay", write_miss_multi_word,      data_64B,     0.9,  3,  0,  10   ],
  [ "write_miss_multi_word_src_delay",  write_miss_multi_word,      data_64B,     0.9,  3,  10, 0    ],

  [ "evict_word",                       evict_word,                 data_16KB,    0.0,  0,  0,  0    ],
  [ "evict_multi_word",                 evict_multi_word,           data_16KB,    0.0,  0,  0,  0    ],
  [ "evict_cacheline",                  evict_cacheline,            data_16KB,    0.0,  0,  0,  0    ],
  [ "evict_multi_cacheline",            evict_multi_cacheline,      data_16KB,    0.0,  0,  0,  0    ],
  [ "evict_multi_word_sink_delay",      evict_multi_word,           data_16KB,    0.9,  3,  0,  10   ],
  [ "evict_multi_word_src_delay",       evict_multi_word,           data_16KB,    0.9,  3,  10, 0    ],

  [ "check_valid_bit",                  check_valid_bit,            data_4B,      0.0,  0,  0,  0    ],
  [ "evict_more",                       evict_more,                 None,         0.0,  0,  0,  0    ],
  [ "read_stream",                      read_stream,                data_16KB,    0.0,  0,  0,  0    ],
  [ "write_stream",                     write_stream,               None,         0.0,  0,  0,  0    ],
  [ "read_stream_mem_delay",            read_stream,                data_16KB,    0.9,  3,  0,  0    ],
  [ "write_stream_mem_delay",           write_stream,               None,         0.9,  3,  0,  0    ],

])

@pytest.mark.parametrize( **test_case_table_generic )
def test_generic( test_params ):
  run_test( CacheFL(), test_params, cmp_fun=cmp_wo_test_field )

#-------------------------------------------------------------------------
# Test Case with Random Addresses and Data
#-------------------------------------------------------------------------

# Notice how the we pass cmp_wo_test_field to our run_test helper
# function. This means that these random test cases will _not_ check the
# test bit (i.e., will _not_ check hit/miss).

def random_reads():

  vmem = data_random()[1::2]
  msgs = []

  for i in range(100):
    idx = randint(0,255)

    if randint(0,1):

      correct_data = vmem[idx]
      msgs.extend([
        req( 'rd', i, 0x00001000+4*idx, 4, 0 ), resp( 'rd', i, 0, 4, correct_data ),
      ])

  return msgs

def random_hits():

  vmem = data_random()[1::2]
  msgs = []

  # First fill the cache with read misses

  for i in range(0,64):
    correct_data = vmem[i]
    msgs.extend([
      req( 'rd', i, 0x00001000+4*i, 4, 0 ), resp( 'rd', i, 0, 4, correct_data ),
    ])

  # Now all remaining accesses should be hits

  for i in range(100):
    idx = randint(0,63)

    if randint(0,1):

      correct_data = vmem[idx]
      msgs.extend([
        req( 'rd', i, 0x00001000+4*idx, 4, 0 ), resp( 'rd', i, 0, 4, correct_data ),
      ])

    else:

      new_data = randint(0,0xffffffff)
      vmem[idx] = new_data
      msgs.extend([
        req( 'wr', i, 0x00001000+4*idx, 4, new_data ), resp( 'wr', i, 0, 4, 0 ),
      ])

  # Read all data again to make sure every write was correct

  for i in range(0,64):
    correct_data = vmem[i]
    msgs.extend([
      req( 'rd', i, 0x00001000+4*i, 4, 0 ), resp( 'rd', i, 0, 4, correct_data ),
    ])

  return msgs

def random_misses():

  vmem = data_random()[1::2]
  msgs = []

  for i in range(100):
    idx = randint(0,255)

    if randint(0,1):

      correct_data = vmem[idx]
      msgs.extend([
        req( 'rd', i, 0x00001000+4*idx, 4, 0 ), resp( 'rd', i, 0, 4, correct_data ),
      ])

    else:

      new_data = randint(0,0xffffffff)
      vmem[idx] = new_data
      msgs.extend([
        req( 'wr', i, 0x00001000+4*idx, 4, new_data ), resp( 'wr', i, 0, 4, 0 ),
      ])

  # Read all data again to make sure every write was correct

  for i in range(0,64):
    correct_data = vmem[i]
    msgs.extend([
      req( 'rd', i, 0x00001000+4*i, 4, 0 ), resp( 'rd', i, 0, 4, correct_data ),
    ])

  return msgs

test_case_table_random = mk_test_case_table([
  (                        "msg_func       mem_data_func stall lat src sink"),
  [ "random_reads",         random_reads,  data_random,  0,    0,  0,  0    ],
  [ "random_hits",          random_hits,   data_random,  0,    0,  0,  0    ],
  [ "random_misses",        random_misses, data_random,  0,    0,  0,  0    ],
  [ "random_hits_delays",   random_hits,   data_random,  0.9,  3,  10, 10   ],
  [ "random_misses_delays", random_misses, data_random,  0.9,  3,  10, 10   ],
])

@pytest.mark.parametrize( **test_case_table_random )
def test_random( test_params ):
  run_test( CacheFL(), test_params, cmp_fun=cmp_wo_test_field )

#-------------------------------------------------------------------------
# Test Cases for Set Associative
#-------------------------------------------------------------------------

# This test is just for the set associative cache. We have two lines that
# cause a conflict miss in a direct mapped cache, which does not occur in
# the set associative cache. (uses data_512B)

def sassoc_no_conflict():
  return [
    #    type  opq  addr       len data       type  opq  test len data
    req( 'rd', 0x0, 0x00001000, 4, 0 ), resp( 'rd', 0x0, 0,   4,  0xabcd1000 ),
    req( 'rd', 0x1, 0x00001100, 4, 0 ), resp( 'rd', 0x1, 0,   4,  0xabcd1100 ),
    req( 'rd', 0x2, 0x00001000, 4, 0 ), resp( 'rd', 0x2, 1,   4,  0xabcd1000 ),
    req( 'rd', 0x3, 0x00001100, 4, 0 ), resp( 'rd', 0x3, 1,   4,  0xabcd1100 ),
  ]

# Test cases designed for two-way set-associative cache

def sassoc_long():
  return [
    #    type  opq   addr      len  data               type  opq test len  data
    # Write to cacheline 0 way 0
    req( 'wr', 0x00, 0x00000000, 4, 0xffffff00), resp( 'wr', 0x00, 0, 4, 0          ),
    req( 'wr', 0x01, 0x00000004, 4, 0xffffff01), resp( 'wr', 0x01, 1, 4, 0          ),
    req( 'wr', 0x02, 0x00000008, 4, 0xffffff02), resp( 'wr', 0x02, 1, 4, 0          ),
    req( 'wr', 0x03, 0x0000000c, 4, 0xffffff03), resp( 'wr', 0x03, 1, 4, 0          ), # LRU:1
    # Write to cacheline 0 way 1
    req( 'wr', 0x04, 0x00001000, 4, 0xffffff04), resp( 'wr', 0x04, 0, 4, 0          ),
    req( 'wr', 0x05, 0x00001004, 4, 0xffffff05), resp( 'wr', 0x05, 1, 4, 0          ),
    req( 'wr', 0x06, 0x00001008, 4, 0xffffff06), resp( 'wr', 0x06, 1, 4, 0          ),
    req( 'wr', 0x07, 0x0000100c, 4, 0xffffff07), resp( 'wr', 0x07, 1, 4, 0          ), # LRU:0
    # Evict way 0
    req( 'rd', 0x08, 0x00002000, 4, 0         ), resp( 'rd', 0x08, 0, 4, 0x00facade ), # LRU:1
    # Read again from same cacheline to see if cache hit properly
    req( 'rd', 0x09, 0x00002004, 4, 0         ), resp( 'rd', 0x09, 1, 4, 0x05ca1ded ), # LRU:1
    # Read from cacheline 0 way 1 to see if cache hits properly,
    req( 'rd', 0x0a, 0x00001004, 4, 0         ), resp( 'rd', 0x0a, 1, 4, 0xffffff05 ), # LRU:0
    # Write to cacheline 0 way 1 to see if cache hits properly
    req( 'wr', 0x0b, 0x0000100c, 4, 0xffffff09), resp( 'wr', 0x0b, 1, 4, 0          ), # LRU:0
    # Read that back
    req( 'rd', 0x0c, 0x0000100c, 4, 0         ), resp( 'rd', 0x0c, 1, 4, 0xffffff09 ), # LRU:0
    # Evict way 0 again
    req( 'rd', 0x0d, 0x00000000, 4, 0         ), resp( 'rd', 0x0d, 0, 4, 0xffffff00 ), # LRU:1
    # Testing cacheline 7 now
    # Write to cacheline 7 way 0
    req( 'wr', 0x10, 0x00000070, 4, 0xffffff00), resp( 'wr', 0x10, 0, 4, 0          ),
    req( 'wr', 0x11, 0x00000074, 4, 0xffffff01), resp( 'wr', 0x11, 1, 4, 0          ),
    req( 'wr', 0x12, 0x00000078, 4, 0xffffff02), resp( 'wr', 0x12, 1, 4, 0          ),
    req( 'wr', 0x13, 0x0000007c, 4, 0xffffff03), resp( 'wr', 0x13, 1, 4, 0          ), # LRU:1
    # Write to cacheline 7 way 1
    req( 'wr', 0x14, 0x00001070, 4, 0xffffff04), resp( 'wr', 0x14, 0, 4, 0          ),
    req( 'wr', 0x15, 0x00001074, 4, 0xffffff05), resp( 'wr', 0x15, 1, 4, 0          ),
    req( 'wr', 0x16, 0x00001078, 4, 0xffffff06), resp( 'wr', 0x16, 1, 4, 0          ),
    req( 'wr', 0x17, 0x0000107c, 4, 0xffffff07), resp( 'wr', 0x17, 1, 4, 0          ), # LRU:0
    # Evict way 0
    req( 'rd', 0x18, 0x00002070, 4, 0         ), resp( 'rd', 0x18, 0, 4, 0x70facade ), # LRU:1
    # Read again from same cacheline to see if cache hits properly
    req( 'rd', 0x19, 0x00002074, 4, 0         ), resp( 'rd', 0x19, 1, 4, 0x75ca1ded ), # LRU:1
    # Read from cacheline 7 way 1 to see if cache hits properly
    req( 'rd', 0x1a, 0x00001074, 4, 0         ), resp( 'rd', 0x1a, 1, 4, 0xffffff05 ), # LRU:0
    # Write to cacheline 7 way 1 to see if cache hits properly
    req( 'wr', 0x1b, 0x0000107c, 4, 0xffffff09), resp( 'wr', 0x1b, 1, 4, 0          ), # LRU:0
    # Read that back
    req( 'rd', 0x1c, 0x0000107c, 4, 0         ), resp( 'rd', 0x1c, 1, 4, 0xffffff09 ), # LRU:0
    # Evict way 0 again
    req( 'rd', 0x1d, 0x00000070, 4, 0         ), resp( 'rd', 0x1d, 0, 4, 0xffffff00 ), # LRU:1
  ]

def sassoc_long_mem():
  return [
    # addr      # data (in int)
    0x00002000, 0x00facade,
    0x00002004, 0x05ca1ded,
    0x00002070, 0x70facade,
    0x00002074, 0x75ca1ded,
  ]

test_case_table_sassoc = mk_test_case_table([
  (                       "msg_func            mem_data_func    stall lat src sink"),
  [ "sassoc_no_conflict",  sassoc_no_conflict, data_16KB,       0.0,  0,  0,  0    ],
  [ "sassoc_long",         sassoc_long,        sassoc_long_mem, 0.0,  0,  0,  0    ],
])

@pytest.mark.parametrize( **test_case_table_sassoc )
def test_sassoc( test_params ):
  run_test( CacheFL(), test_params, cmp_fun=cmp_wo_test_field )

