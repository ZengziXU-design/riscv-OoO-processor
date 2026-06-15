#=========================================================================
# ProcIssueQueue unit tests
#=========================================================================

from pymtl3 import *
from pymtl3.stdlib.test_utils import run_test_vector_sim
from proj3.ProcIssueQueue import ProcIssueQueue

CHANNELS = ( 'alu0', 'alu1', 'mul', 'mem' )

TEST_FMT = (
  'input_val_lane0 input_val_lane1 '
  'input_inst_lane0 input_rob_tag_lane0 input_is_csr_lane0 input_is_mem_lane0 input_is_mul_lane0 '
  'input_rs1_addr_lane0 input_rs1_valid_lane0 input_rs2_addr_lane0 input_rs2_valid_lane0 '
  'input_rd_addr_lane0 input_rd_valid_lane0 '
  'input_inst_lane1 input_rob_tag_lane1 input_is_csr_lane1 input_is_mem_lane1 input_is_mul_lane1 '
  'input_rs1_addr_lane1 input_rs1_valid_lane1 input_rs2_addr_lane1 input_rs2_valid_lane1 '
  'input_rd_addr_lane1 input_rd_valid_lane1 '
  'alu0_dispatch_rdy alu1_dispatch_rdy mul_dispatch_rdy mem_dispatch_rdy '
  'rf_wen_alu0 rf_waddr_alu0 rf_wen_alu1 rf_waddr_alu1 '
  'rf_wen_mul rf_waddr_mul rf_wen_mem rf_waddr_mem '
  'input_rdy* '
  'alu0_dispatch_val* alu0_dispatch_inst* alu0_dispatch_rob_tag* '
  'alu0_dispatch_rs1_addr* alu0_dispatch_rs2_addr* alu0_dispatch_rd_addr* alu0_dispatch_rd_valid* '
  'alu1_dispatch_val* alu1_dispatch_inst* alu1_dispatch_rob_tag* '
  'alu1_dispatch_rs1_addr* alu1_dispatch_rs2_addr* alu1_dispatch_rd_addr* alu1_dispatch_rd_valid* '
  'mul_dispatch_val* mul_dispatch_inst* mul_dispatch_rob_tag* '
  'mul_dispatch_rs1_addr* mul_dispatch_rs2_addr* mul_dispatch_rd_addr* mul_dispatch_rd_valid* '
  'mem_dispatch_val* mem_dispatch_inst* mem_dispatch_rob_tag* '
  'mem_dispatch_rs1_addr* mem_dispatch_rs2_addr* mem_dispatch_rd_addr* mem_dispatch_rd_valid*'
)

def tv( v0, v1, **k ):
  lane0 = [
    k.get('inst0', 0), k.get('tag0', 0), k.get('csr0', 0),
    k.get('mem0', 0), k.get('mul0', 0),
    k.get('rs10', 0), k.get('rs1v0', 0),
    k.get('rs20', 0), k.get('rs2v0', 0),
    k.get('rd0', 0), k.get('rdv0', 0),
  ]
  lane1 = [
    k.get('inst1', 0), k.get('tag1', 0), k.get('csr1', 0),
    k.get('mem1', 0), k.get('mul1', 0),
    k.get('rs11', 0), k.get('rs1v1', 0),
    k.get('rs21', 0), k.get('rs2v1', 0),
    k.get('rd1', 0), k.get('rdv1', 0),
  ]
  ready = [
    k.get('alu0_rdy', 1), k.get('alu1_rdy', 1),
    k.get('mul_rdy', 1), k.get('mem_rdy', 1),
  ]
  wakeup = [
    k.get('wen_alu0', 0), k.get('waddr_alu0', 0),
    k.get('wen_alu1', 0), k.get('waddr_alu1', 0),
    k.get('wen_mul', 0),  k.get('waddr_mul', 0),
    k.get('wen_mem', 0),  k.get('waddr_mem', 0),
  ]

  expected = [ k.get('input_rdy', '?') ]
  for channel in CHANNELS:
    expected.extend([
      k.get(f'{channel}_val', '?'),
      k.get(f'{channel}_inst', '?'),
      k.get(f'{channel}_tag', '?'),
      k.get(f'{channel}_rs1', '?'),
      k.get(f'{channel}_rs2', '?'),
      k.get(f'{channel}_rd', '?'),
      k.get(f'{channel}_rdv', '?'),
    ])

  return [ v0, v1 ] + lane0 + lane1 + ready + wakeup + expected

def no_dispatch( **k ):
  return dict( alu0_val=0, alu1_val=0, mul_val=0, mem_val=0, **k )

#-------------------------------------------------------------------------
# Two independent ALU instructions dispatch together
#-------------------------------------------------------------------------

def test_dual_alu_dispatch( cmdline_opts ):
  dut = ProcIssueQueue()

  run_test_vector_sim( dut, [
    TEST_FMT,
    tv( 1, 1,
      inst0=0xA0, tag0=1, rs10=2, rs1v0=1, rd0=10, rdv0=1,
      inst1=0xA1, tag1=2, rs11=3, rs1v1=1, rd1=11, rdv1=1,
      input_rdy=1, **no_dispatch() ),
    tv( 0, 0, input_rdy=1,
      alu0_val=1, alu0_inst=0xA0, alu0_tag=1, alu0_rs1=2, alu0_rs2=0, alu0_rd=10, alu0_rdv=1,
      alu1_val=1, alu1_inst=0xA1, alu1_tag=2, alu1_rs1=3, alu1_rs2=0, alu1_rd=11, alu1_rdv=1,
      mul_val=0, mem_val=0 ),
    tv( 0, 0, input_rdy=1, **no_dispatch() ),
  ], cmdline_opts )

#-------------------------------------------------------------------------
# RAW dependency prevents same-cycle dual issue
#-------------------------------------------------------------------------

def test_raw_dependency_and_wakeup( cmdline_opts ):
  dut = ProcIssueQueue()

  run_test_vector_sim( dut, [
    TEST_FMT,
    tv( 1, 1,
      inst0=0xB0, tag0=1, rd0=10, rdv0=1,
      inst1=0xB1, tag1=2, rs11=10, rs1v1=1, rd1=11, rdv1=1,
      input_rdy=1, **no_dispatch() ),
    tv( 0, 0, input_rdy=1,
      alu0_val=1, alu0_inst=0xB0, alu0_tag=1, alu0_rd=10, alu0_rdv=1,
      alu1_val=0, mul_val=0, mem_val=0 ),
    tv( 0, 0, input_rdy=1, **no_dispatch() ),
    tv( 0, 0, wen_alu0=1, waddr_alu0=10, input_rdy=1,
      alu0_val=1, alu0_inst=0xB1, alu0_tag=2, alu0_rs1=10,
      alu0_rd=11, alu0_rdv=1, alu1_val=0, mul_val=0, mem_val=0 ),
  ], cmdline_opts )

#-------------------------------------------------------------------------
# Mixed ALU and MUL dispatch
#-------------------------------------------------------------------------

def test_alu_mul_dispatch( cmdline_opts ):
  dut = ProcIssueQueue()

  run_test_vector_sim( dut, [
    TEST_FMT,
    tv( 1, 1,
      inst0=0xC0, tag0=3, mul0=1, rs10=4, rs1v0=1, rs20=5, rs2v0=1, rd0=12, rdv0=1,
      inst1=0xC1, tag1=4, rs11=6, rs1v1=1, rd1=13, rdv1=1,
      input_rdy=1, **no_dispatch() ),
    tv( 0, 0, input_rdy=1,
      alu0_val=1, alu0_inst=0xC1, alu0_tag=4, alu0_rs1=6, alu0_rd=13, alu0_rdv=1,
      alu1_val=0,
      mul_val=1, mul_inst=0xC0, mul_tag=3, mul_rs1=4, mul_rs2=5, mul_rd=12, mul_rdv=1,
      mem_val=0 ),
  ], cmdline_opts )

#-------------------------------------------------------------------------
# Only the oldest MEM is eligible; an ALU may issue beside it
#-------------------------------------------------------------------------

def test_mem_order_with_parallel_alu( cmdline_opts ):
  dut = ProcIssueQueue()

  run_test_vector_sim( dut, [
    TEST_FMT,
    tv( 1, 1, alu0_rdy=0, alu1_rdy=0, mul_rdy=0, mem_rdy=0,
      inst0=0xD0, tag0=1, mem0=1, rs10=2, rs1v0=1, rd0=20, rdv0=1,
      inst1=0xD1, tag1=2, mem1=1, rs11=3, rs1v1=1, rd1=21, rdv1=1,
      input_rdy=1, **no_dispatch() ),
    tv( 1, 0, alu0_rdy=0, alu1_rdy=0, mul_rdy=0, mem_rdy=0,
      inst0=0xD2, tag0=3, rs10=4, rs1v0=1, rd0=22, rdv0=1,
      input_rdy=1, alu0_val=0, alu1_val=0, mul_val=0,
      mem_val=1, mem_inst=0xD0, mem_tag=1, mem_rs1=2, mem_rd=20, mem_rdv=1 ),
    tv( 0, 0, input_rdy=1,
      alu0_val=1, alu0_inst=0xD2, alu0_tag=3, alu0_rs1=4, alu0_rd=22, alu0_rdv=1,
      alu1_val=0, mul_val=0,
      mem_val=1, mem_inst=0xD0, mem_tag=1, mem_rs1=2, mem_rd=20, mem_rdv=1 ),
    tv( 0, 0, input_rdy=1, alu0_val=0, alu1_val=0, mul_val=0,
      mem_val=1, mem_inst=0xD1, mem_tag=2, mem_rs1=3, mem_rd=21, mem_rdv=1 ),
  ], cmdline_opts )

#-------------------------------------------------------------------------
# CSR remains head-only and exclusive
#-------------------------------------------------------------------------

def test_csr_barrier( cmdline_opts ):
  dut = ProcIssueQueue()

  run_test_vector_sim( dut, [
    TEST_FMT,
    tv( 1, 1,
      inst0=0xE0, tag0=1, csr0=1,
      inst1=0xE1, tag1=2, rd1=9, rdv1=1,
      input_rdy=1, **no_dispatch() ),
    tv( 0, 0, input_rdy=1,
      alu0_val=1, alu0_inst=0xE0, alu0_tag=1, alu0_rd=0, alu0_rdv=0,
      alu1_val=0, mul_val=0, mem_val=0 ),
    tv( 0, 0, input_rdy=1,
      alu0_val=1, alu0_inst=0xE1, alu0_tag=2, alu0_rd=9, alu0_rdv=1,
      alu1_val=0, mul_val=0, mem_val=0 ),
  ], cmdline_opts )

#-------------------------------------------------------------------------
# Each channel removes its entry only when its own ready is asserted
#-------------------------------------------------------------------------

def test_independent_channel_ready( cmdline_opts ):
  dut = ProcIssueQueue()

  run_test_vector_sim( dut, [
    TEST_FMT,
    tv( 1, 1,
      inst0=0xF0, tag0=1, rd0=30, rdv0=1,
      inst1=0xF1, tag1=2, rd1=31, rdv1=1,
      input_rdy=1, **no_dispatch() ),
    tv( 0, 0, alu0_rdy=0, alu1_rdy=1, input_rdy=1,
      alu0_val=1, alu0_inst=0xF0, alu0_tag=1,
      alu1_val=1, alu1_inst=0xF1, alu1_tag=2,
      mul_val=0, mem_val=0 ),
    tv( 0, 0, input_rdy=1,
      alu0_val=1, alu0_inst=0xF0, alu0_tag=1,
      alu1_val=0, mul_val=0, mem_val=0 ),
  ], cmdline_opts )

#-------------------------------------------------------------------------
# All four writeback feedback ports wake consumers
#-------------------------------------------------------------------------

def run_wakeup_test( cmdline_opts, wen, waddr ):
  dut = ProcIssueQueue()
  wakeup = { wen: 1, waddr: 15 }

  run_test_vector_sim( dut, [
    TEST_FMT,
    tv( 1, 1,
      inst0=0x110, tag0=1, rd0=15, rdv0=1,
      inst1=0x111, tag1=2, rs11=15, rs1v1=1, rd1=16, rdv1=1,
      input_rdy=1, **no_dispatch() ),
    tv( 0, 0, input_rdy=1,
      alu0_val=1, alu0_inst=0x110, alu0_tag=1,
      alu1_val=0, mul_val=0, mem_val=0 ),
    tv( 0, 0, input_rdy=1, **no_dispatch() ),
    tv( 0, 0, input_rdy=1, **wakeup,
      alu0_val=1, alu0_inst=0x111, alu0_tag=2, alu0_rs1=15,
      alu0_rd=16, alu0_rdv=1, alu1_val=0, mul_val=0, mem_val=0 ),
  ], cmdline_opts )

def test_wakeup_alu0( cmdline_opts ):
  run_wakeup_test( cmdline_opts, 'wen_alu0', 'waddr_alu0' )

def test_wakeup_alu1( cmdline_opts ):
  run_wakeup_test( cmdline_opts, 'wen_alu1', 'waddr_alu1' )

def test_wakeup_mul( cmdline_opts ):
  run_wakeup_test( cmdline_opts, 'wen_mul', 'waddr_mul' )

def test_wakeup_mem( cmdline_opts ):
  run_wakeup_test( cmdline_opts, 'wen_mem', 'waddr_mem' )

#-------------------------------------------------------------------------
# Two simultaneous issues free enough capacity for two new inputs
#-------------------------------------------------------------------------

def test_dual_issue_capacity( cmdline_opts ):
  dut = ProcIssueQueue()
  vectors = [ TEST_FMT ]

  for pair in range( 4 ):
    base = 2 * pair
    vectors.append( tv( 1, 1, alu0_rdy=0, alu1_rdy=0,
      inst0=0x200 + base, tag0=base, rd0=10 + base, rdv0=1,
      inst1=0x201 + base, tag1=base + 1, rd1=11 + base, rdv1=1,
      input_rdy=1,
      alu0_val=0 if pair == 0 else 1,
      alu1_val=0 if pair == 0 else 1,
      mul_val=0, mem_val=0 ) )

  vectors.append( tv( 1, 1,
    inst0=0x300, tag0=8, rd0=40, rdv0=1,
    inst1=0x301, tag1=9, rd1=41, rdv1=1,
    input_rdy=1, alu0_val=1, alu1_val=1, mul_val=0, mem_val=0 ) )

  run_test_vector_sim( dut, vectors, cmdline_opts )
