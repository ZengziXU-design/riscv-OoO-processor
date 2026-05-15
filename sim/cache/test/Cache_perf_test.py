#=========================================================================
# Cache_perf_test.py
#=========================================================================
# These tests will ensure that there are no unnecessary bubbles in cache
# performance. As there is the potential for optimizations to be made,
# there is only a maximum latency bound.
#
# There are 9 additional cycles needed for testing overhead. 3 cycles
# are for setting up the simulation, 5 cycles are for the remaining
# cycles in the simulation, and 1 cycle is for ending the simulation.
# All these extra cycles are removed when checking the number of cycles
# taken by each test.
#
#  1r                   > (I   [   ... ]) > [ ]                  >.                        [  ] >
#  2r                   > (I   [   ... ]) > [ ]                  >.                        [  ] >
#  3:                   > (I   [   ... ]) > [ ]                  >.                        [  ] >
#  4: rd:00:00001000:0: > (I   [   ... ]) > [ ]                  >.                        [  ] >
#  5: .                 > (TC m[   ... ]) > [ ]                  >.                        [  ] >
#  6: .                 > (RR  [   ... ]) > [ ]rd:00:00001000:0: >.                        [  ] >
#  7: .                 > (RW  [   ... ]) > [ ]                  >rd:00:0:0:00...00000c0ffe[ *] >
#  8: .                 > (RU  [   ... ]) > [ ]                  >.                        [  ] >
#  9: .                 > (RD  [10 ... ]) > [ ]                  >.                        [  ] >
# 10: .                 > (W   [10 ... ]) > [ ]                  >.                        [  ] > rd:00:0:0:000c0ffe
# 11:                   > (I   [10 ... ]) > [ ]                  >.                        [  ] >
# 12:                   > (I   [10 ... ]) > [ ]                  >.                        [  ] >
# 13:                   > (I   [10 ... ]) > [ ]                  >.                        [  ] >
# 14:                   > (I   [10 ... ]) > [ ]                  >.                        [  ] >
# 15:                   > (I   [10 ... ]) > [ ]                  >.                        [  ] >

import pytest

from pymtl3 import *
from pymtl3.stdlib.test_utils import run_sim

from cache.test.harness import TestHarness, req, resp
from cache.Cache        import Cache

#-------------------------------------------------------------------------
# Setup
#-------------------------------------------------------------------------

def run_perf_test( cmdline_opts, prog, mem, min_latency, max_latency ):

  # Instantiate model
  model = TestHarness( Cache() )

  imsgs = prog[::2]
  omsgs = prog[1::2]

  model.set_param( "top.src.construct",  msgs=imsgs )
  model.set_param( "top.sink.construct", msgs=omsgs )

  model.elaborate()

  if( mem!= [] ):
    model.load( mem[::2], mem[1::2] )

  run_sim( model, cmdline_opts, duts=['cache'] )

  # see comment above to explain the - 9 adjusment
  latency = model.sim_cycle_count() - 9

  print("min target latency = ",min_latency)
  print("max target latency = ",max_latency)
  print("    actual latency = ",latency)

  assert min_latency <= latency and latency <= max_latency

#-------------------------------------------------------------------------
# Read Hit
#-------------------------------------------------------------------------

def test_perf0( cmdline_opts ):
  prog = [
    req( 'in', 0x0, 0x1000, 0, 0xdeadbeef ), resp( 'in', 0x0, 0,   0,  0          ), # 3 cycles I->TC->IN
    req( 'rd', 0x0, 0x1000, 0, 0          ), resp( 'rd', 0x0, 1,   0,  0xdeadbeef ), # 1 cycle TC
    req( 'rd', 0x0, 0x1000, 0, 0          ), resp( 'rd', 0x0, 1,   0,  0xdeadbeef ), # 1 cycle TC
    req( 'rd', 0x0, 0x1000, 0, 0          ), resp( 'rd', 0x0, 1,   0,  0xdeadbeef ), # 1 cycle TC
  ]

  mem = []

  run_perf_test( cmdline_opts, prog, mem, 6, 6 )

#-------------------------------------------------------------------------
# Write Hit
#-------------------------------------------------------------------------
# The write hit has a single-cycle latency (the response is returned in
# TC) but a two-cycle occupancy (the request still needs to go through
# the TC and WDA states).

def test_perf1( cmdline_opts ):
  prog = [
    req( 'in', 0x0, 0x1000, 0, 0xdeadbeef ), resp( 'in', 0x0, 0,   0,  0          ), # 3 cycles I->TC->IN
    req( 'wr', 0x0, 0x1000, 0, 0xcafecafe ), resp( 'wr', 0x0, 1,   0,  0          ), # 1 cycle  TC->WDA
  ]

  mem = []

  run_perf_test( cmdline_opts, prog, mem, 4, 4 )

#-------------------------------------------------------------------------
# Refill
#-------------------------------------------------------------------------

def test_perf2( cmdline_opts ):
  prog = [
    req( 'rd', 0x0, 0x1000, 0, 0          ), resp( 'rd', 0x0, 0,   0,  0x000c0ffe ), # 8 cycles I->TC->RRQ->RWT->RUP->RD0->RD1->MWT
  ]

  mem = [
    0x00001000, 0x000c0ffe
  ]

  run_perf_test( cmdline_opts, prog, mem, 8, 8 )

#-------------------------------------------------------------------------
# Eviction
#-------------------------------------------------------------------------

def test_perf3( cmdline_opts ):
  prog = [
    req( 'wr', 0x0, 0x1000, 0, 0xdeadbeef ), resp( 'wr', 0x0, 0,   0,  0          ), #  7 cycles I->TC->RRQ->RWT->RUP->MWD->MWT
    req( 'wr', 0x0, 0x2000, 0, 0xcafecafe ), resp( 'wr', 0x0, 0,   0,  0          ), #  7 cycles I->TC->RRQ->RWT->RUP->MWD->MWT
    req( 'rd', 0x0, 0x3000, 0, 0          ), resp( 'rd', 0x0, 0,   0,  0xabcd1200 ), # 12 cycles I->TC->EP0->EP1->ERQ->EWT->RRQ->RWT->RUP->RD0->RD1->MWT
  ]

  mem = [
    0x00003000, 0xabcd1200
  ]

  run_perf_test( cmdline_opts, prog, mem, 26, 26 )

