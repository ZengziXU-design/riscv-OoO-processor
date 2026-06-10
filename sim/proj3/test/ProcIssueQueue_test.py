#=========================================================================
# ProcIssueQueue unit tests
#=========================================================================

from pymtl3 import *
from pymtl3.stdlib.test_utils import run_test_vector_sim
from proj3.ProcIssueQueue import ProcIssueQueue

TEST_FMT = (
  'input_val_lane0 input_val_lane1 '
  'input_inst_lane0 input_rob_tag_lane0 input_is_csr_lane0 input_is_mem_lane0 '
  'input_rs1_addr_lane0 input_rs1_valid_lane0 input_rs2_addr_lane0 input_rs2_valid_lane0 '
  'input_rd_addr_lane0 input_rd_valid_lane0 '
  'input_inst_lane1 input_rob_tag_lane1 input_is_csr_lane1 input_is_mem_lane1 '
  'input_rs1_addr_lane1 input_rs1_valid_lane1 input_rs2_addr_lane1 input_rs2_valid_lane1 '
  'input_rd_addr_lane1 input_rd_valid_lane1 '
  'dispatch_rdy mem_issue_rdy '
  'rf_wen0 rf_waddr0 rf_wen1 rf_waddr1 rf_wen2 rf_waddr2 '
  'input_rdy* dispatch_val* dispatch_inst* dispatch_rob_tag* '
  'dispatch_rs1_addr* dispatch_rs2_addr* dispatch_rd_addr* dispatch_rd_valid*'
)

def tv(
  v0, v1,
  inst0=0, tag0=0, csr0=0, mem0=0, rs10=0, rs1v0=0, rs20=0, rs2v0=0, rd0=0, rdv0=0,
  inst1=0, tag1=0, csr1=0, mem1=0, rs11=0, rs1v1=0, rs21=0, rs2v1=0, rd1=0, rdv1=0,
  dispatch_rdy=1, mem_issue_rdy=1,
  rf_wen0=0, rf_waddr0=0, rf_wen1=0, rf_waddr1=0, rf_wen2=0, rf_waddr2=0,
  input_rdy='?', dispatch_val='?', dispatch_inst='?', dispatch_rob_tag='?',
  dispatch_rs1_addr='?', dispatch_rs2_addr='?', dispatch_rd_addr='?', dispatch_rd_valid='?'
):
  return [
    v0, v1,
    inst0, tag0, csr0, mem0, rs10, rs1v0, rs20, rs2v0, rd0, rdv0,
    inst1, tag1, csr1, mem1, rs11, rs1v1, rs21, rs2v1, rd1, rdv1,
    dispatch_rdy, mem_issue_rdy,
    rf_wen0, rf_waddr0, rf_wen1, rf_waddr1, rf_wen2, rf_waddr2,
    input_rdy, dispatch_val, dispatch_inst, dispatch_rob_tag,
    dispatch_rs1_addr, dispatch_rs2_addr, dispatch_rd_addr, dispatch_rd_valid
  ]

#-------------------------------------------------------------------------
# Test 1: dual enqueue, single dispatch
#-------------------------------------------------------------------------

def test_dual_enqueue_single_dispatch( cmdline_opts ):
  dut = ProcIssueQueue()

  run_test_vector_sim( dut, [
    TEST_FMT,

    tv( 1, 1,
      inst0=0x0000000A, tag0=1, rd0=5, rdv0=1,
      inst1=0x0000000B, tag1=2, rd1=6, rdv1=1,
      input_rdy=1, dispatch_val=0 ),

    tv( 0, 0,
      input_rdy=1, dispatch_val=1, dispatch_inst=0x0000000A, dispatch_rob_tag=1,
      dispatch_rs1_addr=0, dispatch_rs2_addr=0, dispatch_rd_addr=5, dispatch_rd_valid=1 ),

    tv( 0, 0,
      input_rdy=1, dispatch_val=1, dispatch_inst=0x0000000B, dispatch_rob_tag=2,
      dispatch_rs1_addr=0, dispatch_rs2_addr=0, dispatch_rd_addr=6, dispatch_rd_valid=1 ),

    tv( 0, 0, input_rdy=1, dispatch_val=0 ),
  ], cmdline_opts )

#-------------------------------------------------------------------------
# Test 2: RAW dependency within the two enqueued instructions
#-------------------------------------------------------------------------

def test_dual_enqueue_raw_wakeup( cmdline_opts ):
  dut = ProcIssueQueue()

  run_test_vector_sim( dut, [
    TEST_FMT,

    # lane1 depends on lane0's physical destination p10.
    tv( 1, 1,
      inst0=0x0000000A, tag0=1, rd0=10, rdv0=1,
      inst1=0x0000000B, tag1=2, rs11=10, rs1v1=1, rd1=11, rdv1=1,
      input_rdy=1, dispatch_val=0 ),

    # Producer can issue, consumer remains blocked by scoreboard[p10].
    tv( 0, 0,
      input_rdy=1, dispatch_val=1, dispatch_inst=0x0000000A, dispatch_rob_tag=1,
      dispatch_rs1_addr=0, dispatch_rs2_addr=0, dispatch_rd_addr=10, dispatch_rd_valid=1 ),

    tv( 0, 0, input_rdy=1, dispatch_val=0 ),

    # Same-cycle writeback wakeup lets the consumer issue.
    tv( 0, 0, rf_wen0=1, rf_waddr0=10,
      input_rdy=1, dispatch_val=1, dispatch_inst=0x0000000B, dispatch_rob_tag=2,
      dispatch_rs1_addr=10, dispatch_rs2_addr=0, dispatch_rd_addr=11, dispatch_rd_valid=1 ),
  ], cmdline_opts )

#-------------------------------------------------------------------------
# Test 3: memory ordering for two memory instructions
#-------------------------------------------------------------------------

def test_mem_mem_in_order( cmdline_opts ):
  dut = ProcIssueQueue()

  run_test_vector_sim( dut, [
    TEST_FMT,

    tv( 1, 1,
      inst0=0x10000001, tag0=1, mem0=1, rs10=2, rs1v0=1, rd0=5, rdv0=1,
      inst1=0x10000002, tag1=2, mem1=1, rs11=3, rs1v1=1, rd1=6, rdv1=1,
      input_rdy=1, dispatch_val=0 ),

    # The older memory instruction issues first.
    tv( 0, 0,
      input_rdy=1, dispatch_val=1, dispatch_inst=0x10000001, dispatch_rob_tag=1,
      dispatch_rs1_addr=2, dispatch_rs2_addr=0, dispatch_rd_addr=5, dispatch_rd_valid=1 ),

    # The younger memory instruction waits while MemUnit is busy.
    tv( 0, 0, mem_issue_rdy=0, input_rdy=1, dispatch_val=0 ),

    tv( 0, 0,
      input_rdy=1, dispatch_val=1, dispatch_inst=0x10000002, dispatch_rob_tag=2,
      dispatch_rs1_addr=3, dispatch_rs2_addr=0, dispatch_rd_addr=6, dispatch_rd_valid=1 ),
  ], cmdline_opts )

#-------------------------------------------------------------------------
# Test 4: younger ALU can pass a stalled older memory instruction
#-------------------------------------------------------------------------

def test_alu_passes_stalled_mem( cmdline_opts ):
  dut = ProcIssueQueue()

  run_test_vector_sim( dut, [
    TEST_FMT,

    tv( 1, 1, mem_issue_rdy=0,
      inst0=0x10000001, tag0=1, mem0=1, rs10=2, rs1v0=1, rd0=5, rdv0=1,
      inst1=0xA0000002, tag1=2, rs11=20, rs1v1=1, rd1=7, rdv1=1,
      input_rdy=1, dispatch_val=0 ),

    # MEM is blocked by MemUnit, but younger ALU is ready.
    tv( 0, 0, mem_issue_rdy=0,
      input_rdy=1, dispatch_val=1, dispatch_inst=0xA0000002, dispatch_rob_tag=2,
      dispatch_rs1_addr=20, dispatch_rs2_addr=0, dispatch_rd_addr=7, dispatch_rd_valid=1 ),

    tv( 0, 0,
      input_rdy=1, dispatch_val=1, dispatch_inst=0x10000001, dispatch_rob_tag=1,
      dispatch_rs1_addr=2, dispatch_rs2_addr=0, dispatch_rd_addr=5, dispatch_rd_valid=1 ),
  ], cmdline_opts )

#-------------------------------------------------------------------------
# Test 5: rf_wen2 wakeup path still works
#-------------------------------------------------------------------------

def test_wb2_wakeup( cmdline_opts ):
  dut = ProcIssueQueue()

  run_test_vector_sim( dut, [
    TEST_FMT,

    tv( 1, 1,
      inst0=0xAAAA0001, tag0=1, rd0=15, rdv0=1,
      inst1=0xCCCC0002, tag1=2, rs11=15, rs1v1=1, rd1=20, rdv1=1,
      input_rdy=1, dispatch_val=0 ),

    tv( 0, 0,
      input_rdy=1, dispatch_val=1, dispatch_inst=0xAAAA0001, dispatch_rob_tag=1,
      dispatch_rs1_addr=0, dispatch_rs2_addr=0, dispatch_rd_addr=15, dispatch_rd_valid=1 ),

    tv( 0, 0, input_rdy=1, dispatch_val=0 ),

    tv( 0, 0, rf_wen2=1, rf_waddr2=15,
      input_rdy=1, dispatch_val=1, dispatch_inst=0xCCCC0002, dispatch_rob_tag=2,
      dispatch_rs1_addr=15, dispatch_rs2_addr=0, dispatch_rd_addr=20, dispatch_rd_valid=1 ),
  ], cmdline_opts )

#-------------------------------------------------------------------------
# Test 6: capacity ready for 8-entry IQ with two input lanes
#-------------------------------------------------------------------------

def test_dual_enqueue_capacity( cmdline_opts ):
  dut = ProcIssueQueue()

  run_test_vector_sim( dut, [
    TEST_FMT,

    # Fill all eight entries while downstream is stalled.
    tv( 1, 1, dispatch_rdy=0,
      inst0=0x10, tag0=0, rd0=10, rdv0=1,
      inst1=0x11, tag1=1, rd1=11, rdv1=1,
      input_rdy=1, dispatch_val=0 ),
    tv( 1, 1, dispatch_rdy=0,
      inst0=0x12, tag0=2, rd0=12, rdv0=1,
      inst1=0x13, tag1=3, rd1=13, rdv1=1,
      input_rdy=1, dispatch_val=1, dispatch_inst=0x10, dispatch_rob_tag=0,
      dispatch_rs1_addr=0, dispatch_rs2_addr=0, dispatch_rd_addr=10, dispatch_rd_valid=1 ),
    tv( 1, 1, dispatch_rdy=0,
      inst0=0x14, tag0=4, rd0=14, rdv0=1,
      inst1=0x15, tag1=5, rd1=15, rdv1=1,
      input_rdy=1, dispatch_val=1, dispatch_inst=0x10, dispatch_rob_tag=0,
      dispatch_rs1_addr=0, dispatch_rs2_addr=0, dispatch_rd_addr=10, dispatch_rd_valid=1 ),
    tv( 1, 1, dispatch_rdy=0,
      inst0=0x16, tag0=6, rd0=16, rdv0=1,
      inst1=0x17, tag1=7, rd1=17, rdv1=1,
      input_rdy=1, dispatch_val=1, dispatch_inst=0x10, dispatch_rob_tag=0,
      dispatch_rs1_addr=0, dispatch_rs2_addr=0, dispatch_rd_addr=10, dispatch_rd_valid=1 ),

    # Full: two input lanes are not ready.
    tv( 1, 1, dispatch_rdy=0,
      inst0=0x18, tag0=0, rd0=18, rdv0=1,
      inst1=0x19, tag1=1, rd1=19, rdv1=1,
      input_rdy=0, dispatch_val=1, dispatch_inst=0x10, dispatch_rob_tag=0,
      dispatch_rs1_addr=0, dispatch_rs2_addr=0, dispatch_rd_addr=10, dispatch_rd_valid=1 ),

    # Even with one issue this cycle, only one slot is available, so two inputs are rejected.
    tv( 1, 1,
      inst0=0x18, tag0=0, rd0=18, rdv0=1,
      inst1=0x19, tag1=1, rd1=19, rdv1=1,
      input_rdy=0, dispatch_val=1, dispatch_inst=0x10, dispatch_rob_tag=0,
      dispatch_rs1_addr=0, dispatch_rs2_addr=0, dispatch_rd_addr=10, dispatch_rd_valid=1 ),

    # After the issue, exactly one free slot exists; a single-lane input is accepted.
    tv( 1, 0, dispatch_rdy=0,
      inst0=0x18, tag0=0, rd0=18, rdv0=1,
      input_rdy=1, dispatch_val=1, dispatch_inst=0x11, dispatch_rob_tag=1,
      dispatch_rs1_addr=0, dispatch_rs2_addr=0, dispatch_rd_addr=11, dispatch_rd_valid=1 ),
  ], cmdline_opts )
