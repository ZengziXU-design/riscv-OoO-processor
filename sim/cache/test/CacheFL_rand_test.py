#=========================================================================
# CacheFL_rand_test.py
#=========================================================================
# This set of "enhanced" random tests uses a cache model that properly
# tracks hits and misses, and should completely accurately model eviction
# behavior. The model is split up into a hit/miss tracker, and a
# transaction generator, so that the hit/miss tracker can be reused in an
# FL model.

# NOTE: I am not sure if the enhanced random testing model works for
# banking ... I don't think it does. I think it assumes the bank index
# value is always the same for any given cache instance (which is what
# will happen in practice), but the random address generation logic
# doesn't enforce this. -cbatten
#
#  Author : Ian Thompson, Megan Leszczynski (ported by cbatten)
#  Date   : 2016
#

import pytest

from random import seed, randint, getrandbits, random
from math   import log

from pymtl3 import *
from pymtl3.stdlib.mem        import MemMsgType
from pymtl3.stdlib.test_utils import mk_test_case_table

from cache.test.harness      import req, resp, run_test
from cache.test.CacheFL_test import cmp_wo_test_field
from cache.CacheFL           import CacheFL

seed(0xa4e28cc2)

RAND_LEN = 100 # Number of transactions per random test
ADDR_LEN = 20  # How many bits are allowed in a random address

#-------------------------------------------------------------------------
# HitMissTracker
#-------------------------------------------------------------------------

class HitMissTracker:

  def __init__(self, size, nways, linesize):

    # Compute various sizes
    self.nways = nways
    self.linesize = linesize
    self.nlines = int(size / linesize)
    self.nsets = int(self.nlines / self.nways)

    # hard coding to 1, since not sure this works for nbanks == 4
    self.nbanks = 1

    # Compute how the address is sliced

    self.offset_start = 0
    self.offset_end = self.offset_start + int(log(linesize, 2))
    self.bank_start = self.offset_end
    if self.nbanks > 0:
      self.bank_end = self.bank_start + int(log(self.nbanks, 2))
    else:
      self.bank_end = self.bank_start
    self.idx_start = self.bank_end
    self.idx_end = self.idx_start + int(log(self.nsets, 2))
    self.tag_start = self.idx_end
    self.tag_end = 32

    # Initialize the tag and valid array
    # Both arrays are of the form line[idx][way]
    # Note that line[idx] is a one-element array for
    # a direct-mapped cache

    self.line = []
    self.valid = []
    for n in range(self.nlines):
      self.line.insert(n, [Bits32(0) for x in range(nways)])
      self.valid.insert(n, [False for x in range(nways)])

    # Initialize the lru array
    # Implemented as an array for each set index
    # lru[idx][0] is the most recently used
    # lru[idx][-1] is the least recently used

    self.lru = []
    for n in range(self.nsets):
      self.lru.insert(n, [x for x in range(nways)])

  # Generate the components of an address
  # Ignores the bank bits, since they don't affect the behavior
  # (and may not even exist)

  def split_address(self, addr):
    addr = Bits32(addr)
    offset = addr[self.offset_start:self.offset_end]
    idx = addr[self.idx_start:self.idx_end]
    tag = addr[self.tag_start:self.tag_end]
    return (tag, idx, offset)

  # Update the LRU status, given that a hit just occurred

  def lru_hit(self, idx, way):
    self.lru[idx].remove(way)
    self.lru[idx].insert(0, way)

  # Get the least recently used way for an index
  # The LRU is always the last element in the list

  def lru_get(self, idx):
    return self.lru[idx][-1]

  # Perform a tag check, and update lru if a hit occurs

  def tag_check(self, tag, idx):
    for way in range(self.nways):
      if self.valid[idx][way] and self.line[idx][way] == tag:
        # Whenever tag check hits, update the set's lru array
        self.lru_hit(idx, way)
        return True
    return False

  # Update the tag array due to a value getting fetched from memory

  def refill(self, tag, idx):
    victim = self.lru_get(idx)
    self.line[idx][victim] = tag
    self.valid[idx][victim] = True
    self.lru_hit(idx, victim)

  # Simulate accessing an address. Returns True if a hit occurred,
  # False on miss

  def access_address(self, addr):
    (tag, idx, offset) = self.split_address(addr)
    hit = self.tag_check(tag, idx)
    if not hit:
      self.refill(tag, idx)

    return hit

#-------------------------------------------------------------------------
# ModelCache
#-------------------------------------------------------------------------

class ModelCache:
  def __init__(self, size, nways, linesize, mem=None):

    # The hit/miss tracker
    self.tracker = HitMissTracker(size, nways, linesize)

    self.mem = {}

    # Unpack any initial values of memory into a dict (has easier lookup)
    #
    # zip is used here to convert the mem array into an array of
    # (addr, value) pairs (which it really should be in the first
    # place)
    if mem:
      for addr, value in zip(mem[::2], mem[1::2]):
        self.mem[addr] = Bits32(value)

    # The transactions list contains the requests and responses for
    # the stream of read/write calls on this model
    self.transactions = []

  def check_hit(self, addr):
    # Tracker returns boolean, need to convert to 1 or 0 to use
    # in the "test" field of the response
    if self.tracker.access_address(addr):
      return 1
    else:
      return 0

  def read(self, addr):
    hit = self.check_hit(addr)

    if addr.int() in self.mem:
      value = self.mem[addr.int()]
    else:
      value = Bits32(0)

    opaque = randint(0,255)
    self.transactions.append(req('rd', opaque, addr, 4, 0))
    self.transactions.append(resp('rd', opaque, hit, 4, zext(value,128)))

  def write(self, addr, value):
    value = Bits32(value)
    hit = self.check_hit(addr)

    self.mem[addr.int()] = value

    opaque = randint(0,255)
    self.transactions.append(req('wr', opaque, addr, 4, zext(value,128)))
    self.transactions.append(resp('wr', opaque, hit, 4, 0))

  def get_transactions(self):
    return self.transactions

#-------------------------------------------------------------------------
# Random memory initialization
#-------------------------------------------------------------------------
# This double list comprehension looks really icky, but TA's prior
# comments seem to suggest that it was written this way for efficiency,
# whatever that meant at the time. The first for is the outer loop,
# generating the addresses of 1K worth of memory. The second for takes a
# tuple of (address, value), and turns it into two separate array
# elements, so that it can be loaded into a test memory. ModelCache will
# undo the effects of the second for when it reads the array in

def rand_mem():
  seed(0x00c0ffee)
  return [val for n in range(8192) for val in (n*4, randint(0x00000000, 0xffffffff))]

#-------------------------------------------------------------------------
# Test: Write random data to random low addresses
#-------------------------------------------------------------------------

def rand_write_lowaddr( nways ):
  seed(0xdeadbeef)
  model = ModelCache( 8192, nways, 16, rand_mem() )
  for i in range(RAND_LEN):
    addr = randint(0x00000000, 0x00000400)
    addr = addr & Bits32(0xfffffffc) # Align the address
    value = getrandbits(32)
    model.write(addr, value)
  return model.get_transactions()

#-------------------------------------------------------------------------
# Test: Read random data from random low addresses
#-------------------------------------------------------------------------

def rand_read_lowaddr( nways ):
  seed(0xd00dd00d)
  model = ModelCache( 8192, nways, 16, rand_mem() )
  for i in range(RAND_LEN):
    addr = randint(0x00000000, 0x00000400)
    addr = addr & Bits32(0xfffffffc) # Align the address
    model.read(addr)
  return model.get_transactions()

#-------------------------------------------------------------------------
# Test: Randomly read or write random data from random low addresses
#-------------------------------------------------------------------------

def rand_rw_lowaddr( nways ):
  seed(0xbaadf00d)
  model = ModelCache( 8192, nways, 16, rand_mem() )
  for i in range(RAND_LEN):
    addr = randint(0x00000000, 0x00000400)
    addr = addr & Bits32(0xfffffffc) # Align the address
    if randint(0,1):
      # Write something
      value = getrandbits(32)
      model.write(addr, value)
    else:
      # Read something
      model.read(addr)
  return model.get_transactions()

#-------------------------------------------------------------------------
# Test: Randomly read or write random data from random low addresses
#-------------------------------------------------------------------------
# Replaces with an operation on a small pool of addresses 60% of the time

REPEAT_LEN = 10
REPEAT_CHANCE = 0.6

def rand_rw_repeat( nways ):
  seed(0x12345678)
  model = ModelCache( 8192, nways, 16, rand_mem() )
  rep = [getrandbits(ADDR_LEN) for x in range(REPEAT_LEN)]
  for i in range(RAND_LEN):

    if random() < REPEAT_CHANCE:
      addr = rep[randint(0,REPEAT_LEN-1)]
    else:
      addr = getrandbits(ADDR_LEN)
    addr = addr & Bits32(0xfffffffc) # Align the address

    if randint(0,1):
      # Write something
      value = getrandbits(32)
      model.write(addr, value)
    else:
      # Read something
      model.read(addr)

  return model.get_transactions()

#-------------------------------------------------------------------------
# Test: Read/write random data to each address sequentially
#-------------------------------------------------------------------------

def rand_rw_stride( nways ):
  seed(0xaaaaaaaa)
  model = ModelCache( 8192, nways, 16, rand_mem() )
  for i in range(RAND_LEN):

    addr = i * 4
    addr = addr & Bits32(0xfffffffc) # Align the address

    if randint(0,1):
      # Write something
      value = getrandbits(32)
      model.write(addr, value)
    else:
      # Read something
      model.read(addr)

  return model.get_transactions()

#-------------------------------------------------------------------------
# Test: Read/write random data to every 3rd address
#-------------------------------------------------------------------------

STRIDE_LEN = 3

def rand_rw_vstride( nways ):
  seed(0xbbbbbbbb)
  model = ModelCache( 8192, nways, 16, rand_mem() )
  for i in range(RAND_LEN):
    addr = i * 4 * STRIDE_LEN
    addr = addr & Bits32(0xfffffffc) # Align the address

    if randint(0,1):
      # Write something
      value = getrandbits(32)
      model.write(addr, value)
    else:
      # Read something
      model.read(addr)

  return model.get_transactions()

#-------------------------------------------------------------------------
# Test: Read/write random data to every address in sequence
#-------------------------------------------------------------------------
# Replaces an operation with a query to a preselected address 60% of the
# time

def rand_rw_rstride( nways ):
  seed(0xcccccccc)
  model = ModelCache( 8192, nways, 16, rand_mem() )
  rep = [getrandbits(ADDR_LEN) for x in range(REPEAT_LEN)]
  for i in range(RAND_LEN):
    if random() < REPEAT_CHANCE:
      addr = rep[randint(0,REPEAT_LEN-1)]
    else:
      addr = i * 4

    addr = addr & Bits32(0xfffffffc) # Align the address

    if randint(0,1):
      # Write something
      value = getrandbits(32)
      model.write(addr, value)
    else:
      # Read something
      model.read(addr)

  return model.get_transactions()

#-------------------------------------------------------------------------
# Test: Read/write random data to random addresses
#-------------------------------------------------------------------------
# Replaces an operation with a query to a previous address 60% of the
# time

HIST_LEN = 20
HIST_CHANCE = 0.6

def rand_rw_hist( nways ):
  seed(0xbaadf00d)
  model = ModelCache( 8192, nways, 16, rand_mem() )
  hist = [getrandbits(ADDR_LEN) for x in range(HIST_LEN)]
  for i in range(RAND_LEN):
    if random() < HIST_CHANCE:
      addr = hist[randint(0,HIST_LEN-1)]
    else:
      addr = getrandbits(ADDR_LEN)

    addr = addr & Bits32(0xfffffffc) # Align the address

    # Update the address history
    hist.pop()
    hist.insert(0, addr)

    if randint(0,1):
      # Write something
      value = getrandbits(32)
      model.write(addr, value)
    else:
      # Read something
      model.read(addr)

  return model.get_transactions()

#-------------------------------------------------------------------------
# Direct Mapped Test Case Table
#-------------------------------------------------------------------------

def dmap_rand_write_lowaddr(): return rand_write_lowaddr( 1 )
def dmap_rand_read_lowaddr():  return rand_read_lowaddr( 1 )
def dmap_rand_rw_lowaddr():    return rand_rw_lowaddr( 1 )
def dmap_rand_rw_repeat():     return rand_rw_repeat( 1 )
def dmap_rand_rw_stride():     return rand_rw_stride( 1 )
def dmap_rand_rw_vstride():    return rand_rw_vstride( 1 )
def dmap_rand_rw_rstride():    return rand_rw_rstride( 1 )
def dmap_rand_rw_hist():       return rand_rw_hist( 1 )

test_case_table_dmap_rand = mk_test_case_table([
  (                                  "msg_func            mem_data_func  stall lat src sink"),

  [ "dmap_rand_write_lowaddr",        dmap_rand_write_lowaddr, rand_mem, 0.0,  0,  0,  0    ],
  [ "dmap_rand_read_lowaddr",         dmap_rand_read_lowaddr,  rand_mem, 0.0,  0,  0,  0    ],
  [ "dmap_rand_rw_lowaddr",           dmap_rand_rw_lowaddr,    rand_mem, 0.0,  0,  0,  0    ],
  [ "dmap_rand_rw_repeat",            dmap_rand_rw_repeat,     rand_mem, 0.0,  0,  0,  0    ],
  [ "dmap_rand_rw_stride",            dmap_rand_rw_stride,     rand_mem, 0.0,  0,  0,  0    ],
  [ "dmap_rand_rw_vstride",           dmap_rand_rw_vstride,    rand_mem, 0.0,  0,  0,  0    ],
  [ "dmap_rand_rw_rstride",           dmap_rand_rw_rstride,    rand_mem, 0.0,  0,  0,  0    ],
  [ "dmap_rand_rw_hist",              dmap_rand_rw_hist,       rand_mem, 0.0,  0,  0,  0    ],

  [ "dmap_rand_write_lowaddr_delays", dmap_rand_write_lowaddr, rand_mem, 0.5,  3,  10, 10   ],
  [ "dmap_rand_read_lowaddr_delays",  dmap_rand_read_lowaddr,  rand_mem, 0.5,  3,  10, 10   ],
  [ "dmap_rand_rw_lowaddr_delays",    dmap_rand_rw_lowaddr,    rand_mem, 0.5,  3,  10, 10   ],
  [ "dmap_rand_rw_repeat_delays",     dmap_rand_rw_repeat,     rand_mem, 0.5,  3,  10, 10   ],
  [ "dmap_rand_rw_stride_delays",     dmap_rand_rw_stride,     rand_mem, 0.5,  3,  10, 10   ],
  [ "dmap_rand_rw_vstride_delays",    dmap_rand_rw_vstride,    rand_mem, 0.5,  3,  10, 10   ],
  [ "dmap_rand_rw_rstride_delays",    dmap_rand_rw_rstride,    rand_mem, 0.5,  3,  10, 10   ],
  [ "dmap_rand_rw_hist_delays",       dmap_rand_rw_hist,       rand_mem, 0.5,  3,  10, 10   ],

])

@pytest.mark.parametrize( **test_case_table_dmap_rand )
def test_dmap_rand( test_params ):
  run_test( CacheFL(), test_params, cmp_fun=cmp_wo_test_field )

#-------------------------------------------------------------------------
# Set Associative Test Case Table
#-------------------------------------------------------------------------

def sassoc_rand_write_lowaddr(): return rand_write_lowaddr( 2 )
def sassoc_rand_read_lowaddr():  return rand_read_lowaddr( 2 )
def sassoc_rand_rw_lowaddr():    return rand_rw_lowaddr( 2 )
def sassoc_rand_rw_repeat():     return rand_rw_repeat( 2 )
def sassoc_rand_rw_stride():     return rand_rw_stride( 2 )
def sassoc_rand_rw_vstride():    return rand_rw_vstride( 2 )
def sassoc_rand_rw_rstride():    return rand_rw_rstride( 2 )
def sassoc_rand_rw_hist():       return rand_rw_hist( 2 )

test_case_table_sassoc_rand = mk_test_case_table([
  (                                  "msg_func            mem_data_func  stall lat src sink"),

  [ "sassoc_rand_write_lowaddr",        sassoc_rand_write_lowaddr, rand_mem, 0.0,  0,  0,  0    ],
  [ "sassoc_rand_read_lowaddr",         sassoc_rand_read_lowaddr,  rand_mem, 0.0,  0,  0,  0    ],
  [ "sassoc_rand_rw_lowaddr",           sassoc_rand_rw_lowaddr,    rand_mem, 0.0,  0,  0,  0    ],
  [ "sassoc_rand_rw_repeat",            sassoc_rand_rw_repeat,     rand_mem, 0.0,  0,  0,  0    ],
  [ "sassoc_rand_rw_stride",            sassoc_rand_rw_stride,     rand_mem, 0.0,  0,  0,  0    ],
  [ "sassoc_rand_rw_vstride",           sassoc_rand_rw_vstride,    rand_mem, 0.0,  0,  0,  0    ],
  [ "sassoc_rand_rw_rstride",           sassoc_rand_rw_rstride,    rand_mem, 0.0,  0,  0,  0    ],
  [ "sassoc_rand_rw_hist",              sassoc_rand_rw_hist,       rand_mem, 0.0,  0,  0,  0    ],

  [ "sassoc_rand_write_lowaddr_delays", sassoc_rand_write_lowaddr, rand_mem, 0.5,  3,  10, 10   ],
  [ "sassoc_rand_read_lowaddr_delays",  sassoc_rand_read_lowaddr,  rand_mem, 0.5,  3,  10, 10   ],
  [ "sassoc_rand_rw_lowaddr_delays",    sassoc_rand_rw_lowaddr,    rand_mem, 0.5,  3,  10, 10   ],
  [ "sassoc_rand_rw_repeat_delays",     sassoc_rand_rw_repeat,     rand_mem, 0.5,  3,  10, 10   ],
  [ "sassoc_rand_rw_stride_delays",     sassoc_rand_rw_stride,     rand_mem, 0.5,  3,  10, 10   ],
  [ "sassoc_rand_rw_vstride_delays",    sassoc_rand_rw_vstride,    rand_mem, 0.5,  3,  10, 10   ],
  [ "sassoc_rand_rw_rstride_delays",    sassoc_rand_rw_rstride,    rand_mem, 0.5,  3,  10, 10   ],
  [ "sassoc_rand_rw_hist_delays",       sassoc_rand_rw_hist,       rand_mem, 0.5,  3,  10, 10   ],

])

@pytest.mark.parametrize( **test_case_table_sassoc_rand )
def test_sassoc_rand( test_params ):
  run_test( CacheFL(), test_params, cmp_fun=cmp_wo_test_field )
