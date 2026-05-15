#=========================================================================
# MemUnit unit tests
#=========================================================================
# Tests for the single-M-stage MemUnit. Key invariants exercised here:
#
#   * LW end-to-end: addr=base+imm, type=READ, ostream_rf_wen=1,
#     ostream_data forwarded from dmem response.
#   * SW end-to-end: type=WRITE, dmem_reqstream_msg_data=sw_data,
#     ostream_rf_wen=0 (no PRF writeback for store).
#   * dmem_reqstream_rdy=0 prevents istream from firing
#     (mem_issue_rdy/istream_rdy both go 0).
#   * busy_M=1 prevents a second mem inst from issuing
#     (the "single in-flight" property).
#   * Back-to-back: when req_fire and resp_fire happen in the same cycle,
#     the OLD instruction completes on ostream while the NEW instruction
#     becomes the new outstanding mem op (busy_M stays 1, but rd_paddr_M
#     and rob_idx_M update).

from pymtl3 import *
from pymtl3.stdlib.test_utils import run_test_vector_sim
from proj3.ProcMemunit import MemUnit

# Mem message type encoding (matches vc/mem-msgs.v)
READ  = 0
WRITE = 1

TEST_FMT = (
  # ----- Inputs (11) -----
  'istream_val istream_is_sw '
  'istream_base istream_imm istream_rd_paddr istream_rob_idx istream_sw_data '
  'dmem_reqstream_rdy '
  'dmem_respstream_val dmem_respstream_msg_data '
  'ostream_rdy '
  # ----- Outputs (12) -----
  'istream_rdy* mem_issue_rdy* '
  'dmem_reqstream_val* dmem_reqstream_msg_addr* dmem_reqstream_msg_data* dmem_reqstream_msg_type* '
  'dmem_respstream_rdy* '
  'ostream_val* ostream_rf_wen* ostream_data* ostream_rd_paddr* ostream_rob_idx*'
)

#-------------------------------------------------------------------------
# Test 1: LW end-to-end
#-------------------------------------------------------------------------
# A single lw is issued, the dmem response arrives, and the response data
# propagates to ostream with rf_wen=1.
def test_lw_basic( cmdline_opts ):
  dut = MemUnit()

  run_test_vector_sim( dut, [
    (TEST_FMT),
    # Cycle 1: issue lw  base=0x100  imm=0x4  rd_paddr=5  rob=1
    # -> dmem req fires this cycle (addr=0x104, type=READ, data=0)
    [ 1, 0,  0x100, 0x4, 5, 1, 0,    1,    0, 0,           1,
      1, 1,  1, 0x104, 0, READ,  0,  0, 0, '?', '?', '?' ],

    # Cycle 2: in flight, waiting for dmem response.
    # busy_M=1 -> mem_issue_rdy=0; dmem_respstream_rdy=1 (ready to take it).
    [ 0, 0,  0, 0, 0, 0, 0,          1,    0, 0,           1,
      0, 0,  0, '?', '?', '?',       1,    0, 0, '?', '?', '?' ],

    # Cycle 3: dmem response arrives -> ostream fires this same cycle.
    # ostream_data=resp_data, rd_paddr=5, rob_idx=1, rf_wen=1.
    # resp_fire=1 -> can_accept=1 -> mem_issue_rdy=1 again.
    [ 0, 0,  0, 0, 0, 0, 0,          1,    1, 0xCAFEBABE,  1,
      1, 1,  0, '?', '?', '?',       1,    1, 1, 0xCAFEBABE, 5, 1 ],

    # Cycle 4: idle. busy_M=0. nothing on ostream. dmem_resp_rdy back to 0.
    [ 0, 0,  0, 0, 0, 0, 0,          1,    0, 0,           1,
      1, 1,  0, '?', '?', '?',       0,    0, 0, '?', '?', '?' ],
  ], cmdline_opts )


#-------------------------------------------------------------------------
# Test 2: SW end-to-end (negative immediate, rf_wen=0 on writeback)
#-------------------------------------------------------------------------
# Verifies the WRITE path: dmem_reqstream_msg_data carries sw_data,
# msg_type=WRITE, and ostream_rf_wen stays 0 even when dmem acks.
# Also exercises addr = base + imm with imm = -8 (0xFFFFFFF8).
def test_sw_basic( cmdline_opts ):
  dut = MemUnit()

  run_test_vector_sim( dut, [
    (TEST_FMT),
    # Cycle 1: issue sw  base=0x200  imm=-8 (0xFFFFFFF8)  rob=2  data=0xDEADBEEF
    # -> addr = 0x200 + 0xFFFFFFF8 = 0x1F8 (mod 2^32), type=WRITE
    # rd_paddr=0 because sw has no rd (rename should have masked it).
    [ 1, 1,  0x200, 0xFFFFFFF8, 0, 2, 0xDEADBEEF,  1,  0, 0,  1,
      1, 1,  1, 0x1F8, 0xDEADBEEF, WRITE,  0,  0, 0, '?', '?', '?' ],

    # Cycle 2: dmem ack arrives. ostream fires WITH rf_wen=0 (key for sw).
    # ostream_data forced to 0 (the is_sw_M ? 0 : ... mux). rd_paddr=0, rob=2.
    [ 0, 0,  0, 0, 0, 0, 0,          1,    1, 0,            1,
      1, 1,  0, '?', '?', '?',       1,    1, 0, 0, 0, 2 ],

    # Cycle 3: idle.
    [ 0, 0,  0, 0, 0, 0, 0,          1,    0, 0,            1,
      1, 1,  0, '?', '?', '?',       0,    0, 0, '?', '?', '?' ],
  ], cmdline_opts )


#-------------------------------------------------------------------------
# Test 3: dmem_reqstream_rdy=0 -> issue is blocked
#-------------------------------------------------------------------------
# When dmem can't accept a new request, the MemUnit must NOT accept the
# instruction from IQ either (mem_issue_rdy and istream_rdy both go 0).
# This is the key invariant from the M-stage code comment - because there
# is no internal request buffer, MemUnit accepting an inst that dmem
# can't take would lose the instruction.
def test_dmem_req_backpressure( cmdline_opts ):
  dut = MemUnit()

  run_test_vector_sim( dut, [
    (TEST_FMT),
    # Cycle 1: try to issue lw, but dmem_reqstream_rdy=0 -> blocked.
    # mem_issue_rdy=0, istream_rdy=0. dmem_reqstream_val IS asserted (the
    # request is presented), but req_fire never happens -> no state change.
    [ 1, 0,  0x100, 0x4, 5, 1, 0,    0,    0, 0,           1,
      0, 0,  1, 0x104, 0, READ,      0,    0, 0, '?', '?', '?' ],

    # Cycle 2: still blocked. Confirms persistent blocking.
    [ 1, 0,  0x100, 0x4, 5, 1, 0,    0,    0, 0,           1,
      0, 0,  1, 0x104, 0, READ,      0,    0, 0, '?', '?', '?' ],

    # Cycle 3: dmem_reqstream_rdy goes to 1 -> request fires THIS cycle.
    # End of cycle 3: busy_M=1.
    [ 1, 0,  0x100, 0x4, 5, 1, 0,    1,    0, 0,           1,
      1, 1,  1, 0x104, 0, READ,      0,    0, 0, '?', '?', '?' ],

    # Cycle 4: dmem responds in same cycle we'd otherwise wait.
    [ 0, 0,  0, 0, 0, 0, 0,          1,    1, 0xAA000001,  1,
      1, 1,  0, '?', '?', '?',       1,    1, 1, 0xAA000001, 5, 1 ],
  ], cmdline_opts )


#-------------------------------------------------------------------------
# Test 4: busy_M=1 blocks a second mem inst until response completes
#-------------------------------------------------------------------------
# The "single in-flight" property: while one mem inst is waiting for its
# response, a second mem inst presented to istream must NOT fire. Once
# the response completes, mem_issue_rdy returns to 1 and new issues work.
def test_busy_blocks_new_issue( cmdline_opts ):
  dut = MemUnit()

  run_test_vector_sim( dut, [
    (TEST_FMT),
    # Cycle 1: issue lw1 (rob=1). End: busy_M=1.
    [ 1, 0,  0x100, 0x4, 5, 1, 0,    1,    0, 0,           1,
      1, 1,  1, 0x104, 0, READ,      0,    0, 0, '?', '?', '?' ],

    # Cycle 2: try to issue lw2 (rob=2, base=0x300, imm=0x10) WHILE busy_M=1.
    # can_accept=0 -> mem_issue_rdy=0, istream_rdy=0, dmem_reqstream_val=0.
    # The request is NOT presented to dmem. busy_M stays 1.
    [ 1, 0,  0x300, 0x10, 10, 2, 0,  1,    0, 0,           1,
      0, 0,  0, '?', '?', '?',       1,    0, 0, '?', '?', '?' ],

    # Cycle 3: stop trying lw2. Still busy_M=1, no response yet -> blocked.
    [ 0, 0,  0, 0, 0, 0, 0,          1,    0, 0,           1,
      0, 0,  0, '?', '?', '?',       1,    0, 0, '?', '?', '?' ],

    # Cycle 4: lw1 response arrives. ostream fires for lw1.
    # End of cycle 4: busy_M=0.
    [ 0, 0,  0, 0, 0, 0, 0,          1,    1, 0x11111111,  1,
      1, 1,  0, '?', '?', '?',       1,    1, 1, 0x11111111, 5, 1 ],

    # Cycle 5: idle, MemUnit free again.
    [ 0, 0,  0, 0, 0, 0, 0,          1,    0, 0,           1,
      1, 1,  0, '?', '?', '?',       0,    0, 0, '?', '?', '?' ],
  ], cmdline_opts )


#-------------------------------------------------------------------------
# Test 5: Back-to-back issue (req_fire && resp_fire same cycle)
#-------------------------------------------------------------------------
# The most subtle case in this design. When the old response arrives in the
# SAME cycle as a new request fires:
#   - ostream produces the OLD instruction's writeback (rd_paddr_M, rob_idx_M
#     are still the old values combinationally because we read state).
#   - At the clock edge, req_fire wins over resp_fire in the always_ff,
#     so busy_M stays 1 and the metadata is overwritten with the NEW inst's.
def test_back_to_back( cmdline_opts ):
  dut = MemUnit()

  run_test_vector_sim( dut, [
    (TEST_FMT),
    # Cycle 1: issue lw1 (rob=1, rd=5). End: busy_M=1, rob_idx_M=1, rd_paddr_M=5.
    [ 1, 0,  0x100, 0x4, 5, 1, 0,    1,    0, 0,           1,
      1, 1,  1, 0x104, 0, READ,      0,    0, 0, '?', '?', '?' ],

    # Cycle 2: in flight, no response yet.
    [ 0, 0,  0, 0, 0, 0, 0,          1,    0, 0,           1,
      0, 0,  0, '?', '?', '?',       1,    0, 0, '?', '?', '?' ],

    # Cycle 3: BACK-TO-BACK.
    #   * dmem responds for lw1 (data=0xAAAAAAAA) -> resp_fire=1.
    #   * Simultaneously, lw2 issues (rob=2, rd=10, addr=0x208) -> req_fire=1.
    #   * resp_fire makes can_accept=1 even though busy_M=1.
    # Outputs reflect lw1 on ostream (using old rd_paddr_M=5, rob_idx_M=1)
    # and lw2 on dmem_reqstream (addr=0x208).
    # End: busy_M stays 1, but rd_paddr_M<=10, rob_idx_M<=2 (new inst).
    [ 1, 0,  0x200, 0x8, 10, 2, 0,   1,    1, 0xAAAAAAAA,  1,
      1, 1,  1, 0x208, 0, READ,      1,    1, 1, 0xAAAAAAAA, 5, 1 ],

    # Cycle 4: lw2 in flight, waiting for its response.
    [ 0, 0,  0, 0, 0, 0, 0,          1,    0, 0,           1,
      0, 0,  0, '?', '?', '?',       1,    0, 0, '?', '?', '?' ],

    # Cycle 5: lw2 response arrives -> ostream fires for lw2.
    [ 0, 0,  0, 0, 0, 0, 0,          1,    1, 0xBBBBBBBB,  1,
      1, 1,  0, '?', '?', '?',       1,    1, 1, 0xBBBBBBBB, 10, 2 ],
  ], cmdline_opts )