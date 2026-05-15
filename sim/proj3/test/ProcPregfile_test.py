#=========================================================================
# ProcPregfile unit tests
#=========================================================================
# Updated for the mem-pipe revision: PRF now exposes a third write port
# (wr_en2 / wr_addr2 / wr_data2) for lw-response writeback from MemUnit.
# Same-cycle read-bypass priority is port 0 (ALU) > port 1 (MUL) > port 2 (LW).

from pymtl3 import *
from pymtl3.stdlib.test_utils import run_test_vector_sim
from proj3.ProcPregfile import ProcPregfile

# Unified column format
TEST_FMT = (
  'rd_addr0 rd_addr1 '
  'wr_en0 wr_addr0 wr_data0 '
  'wr_en1 wr_addr1 wr_data1 '
  'wr_en2 wr_addr2 wr_data2 '
  'rd_data0* rd_data1*'
)

#-------------------------------------------------------------------------
# Test 1: Basic Read/Write (ports 0 and 1 only)
#-------------------------------------------------------------------------
def test_basic_rw( cmdline_opts ):
  dut = ProcPregfile()

  run_test_vector_sim( dut, [
    (TEST_FMT),
    # Cycle 1: Write p5 via port 0, write p6 via port 1. Read p0 (always 0).
    [  0,  0,   1,   5, 0x11111111,   1,   6, 0x22222222,   0,   0, 0x00000000,          0,          0 ],

    # Cycle 2: Read p5 via port 0, read p6 via port 1. No writes.
    [  5,  6,   0,   0, 0x00000000,   0,   0, 0x00000000,   0,   0, 0x00000000, 0x11111111, 0x22222222 ],

    # Cycle 3: Swap ports - read p6 via port 0, read p5 via port 1.
    [  6,  5,   0,   0, 0x00000000,   0,   0, 0x00000000,   0,   0, 0x00000000, 0x22222222, 0x11111111 ],
  ], cmdline_opts )


#-------------------------------------------------------------------------
# Test 2: Same-Cycle Bypass Forwarding (ports 0 and 1)
#-------------------------------------------------------------------------
def test_bypass_forwarding( cmdline_opts ):
  dut = ProcPregfile()

  run_test_vector_sim( dut, [
    (TEST_FMT),
    # Cycle 1: Same-cycle write+read of p10 via port 0.
    [ 10,  0,   1,  10, 0xAAAAAAAA,   0,   0, 0x00000000,   0,   0, 0x00000000, 0xAAAAAAAA,          0 ],

    # Cycle 2: Same-cycle write+read of p20 via port 1.
    [  0, 20,   0,   0, 0x00000000,   1,  20, 0xBBBBBBBB,   0,   0, 0x00000000,          0, 0xBBBBBBBB ],

    # Cycle 3: Cross-port bypass.
    # Write p30 via port 0 -> read via port 1; write p40 via port 1 -> read via port 0.
    [ 40, 30,   1,  30, 0xCCCCCCCC,   1,  40, 0xDDDDDDDD,   0,   0, 0x00000000, 0xDDDDDDDD, 0xCCCCCCCC ],
  ], cmdline_opts )


#-------------------------------------------------------------------------
# Test 3: The Zero Register (p0) Hardwire Check
#-------------------------------------------------------------------------
# All three write ports must be masked from corrupting p0, both in the
# stored register file and in the same-cycle bypass mux.
def test_p0_protection( cmdline_opts ):
  dut = ProcPregfile()

  run_test_vector_sim( dut, [
    (TEST_FMT),
    # Cycle 1: Aggressively try to overwrite p0 from ALL THREE write ports.
    # Same-cycle reads of p0 must still return 0 (bypass is masked).
    [  0,  0,   1,   0, 0xDEADBEEF,   1,   0, 0xBADF00D0,   1,   0, 0xCAFEBABE,          0,          0 ],

    # Cycle 2: Stop writing. p0 must still be 0 (no state corruption).
    [  0,  0,   0,   0, 0x00000000,   0,   0, 0x00000000,   0,   0, 0x00000000,          0,          0 ],

    # Cycle 3: Try writing p0 ONLY via port 2 (the new path). Read must be 0.
    [  0,  0,   0,   0, 0x00000000,   0,   0, 0x00000000,   1,   0, 0xFFFFFFFF,          0,          0 ],

    # Cycle 4: Verify p0 is still 0 after the port-2-only assault.
    [  0,  0,   0,   0, 0x00000000,   0,   0, 0x00000000,   0,   0, 0x00000000,          0,          0 ],
  ], cmdline_opts )


#-------------------------------------------------------------------------
# Test 4: Write Port 2 - basic write then read
#-------------------------------------------------------------------------
# A lw response writes via port 2 and the value must be readable from
# either read port on subsequent cycles.
def test_port2_basic( cmdline_opts ):
  dut = ProcPregfile()

  run_test_vector_sim( dut, [
    (TEST_FMT),
    # Cycle 1: Write p7 via port 2, read p0 (don't care about written data yet).
    [  0,  0,   0,   0, 0x00000000,   0,   0, 0x00000000,   1,   7, 0x12345678,          0,          0 ],

    # Cycle 2: Read p7 from BOTH read ports.
    [  7,  7,   0,   0, 0x00000000,   0,   0, 0x00000000,   0,   0, 0x00000000, 0x12345678, 0x12345678 ],

    # Cycle 3: Write p8 via port 2 with a different value, simultaneously read p7.
    [  7,  0,   0,   0, 0x00000000,   0,   0, 0x00000000,   1,   8, 0xABCDEF01, 0x12345678,          0 ],

    # Cycle 4: Read both p7 and p8 - both writes from port 2 must persist.
    [  7,  8,   0,   0, 0x00000000,   0,   0, 0x00000000,   0,   0, 0x00000000, 0x12345678, 0xABCDEF01 ],
  ], cmdline_opts )


#-------------------------------------------------------------------------
# Test 5: Write Port 2 - same-cycle bypass forwarding
#-------------------------------------------------------------------------
# A consumer reading the lw destination on the same cycle the lw writes back
# must observe the response data through the bypass mux.
def test_port2_bypass( cmdline_opts ):
  dut = ProcPregfile()

  run_test_vector_sim( dut, [
    (TEST_FMT),
    # Cycle 1: Same-cycle write p15 via port 2 and read p15 via port 0.
    [ 15,  0,   0,   0, 0x00000000,   0,   0, 0x00000000,   1,  15, 0x55555555, 0x55555555,          0 ],

    # Cycle 2: Same-cycle write p25 via port 2 and read p25 via port 1.
    [  0, 25,   0,   0, 0x00000000,   0,   0, 0x00000000,   1,  25, 0x66666666,          0, 0x66666666 ],

    # Cycle 3: Same-cycle write p35 via port 2 and read it from BOTH ports.
    [ 35, 35,   0,   0, 0x00000000,   0,   0, 0x00000000,   1,  35, 0x77777777, 0x77777777, 0x77777777 ],
  ], cmdline_opts )


#-------------------------------------------------------------------------
# Test 6: All Three Write Ports Active in Same Cycle
#-------------------------------------------------------------------------
# Realistic case: ALU/MUL/LW all complete on the same cycle, each writing a
# distinct paddr (Rename + scoreboard guarantee distinctness in real hw).
# All three writes must persist independently.
def test_three_port_write( cmdline_opts ):
  dut = ProcPregfile()

  run_test_vector_sim( dut, [
    (TEST_FMT),
    # Cycle 1: Triple write to p1 (port 0), p2 (port 1), p3 (port 2).
    [  0,  0,   1,   1, 0x0A0A0A0A,   1,   2, 0x0B0B0B0B,   1,   3, 0x0C0C0C0C,          0,          0 ],

    # Cycle 2: Read p1 via port 0, p2 via port 1.
    [  1,  2,   0,   0, 0x00000000,   0,   0, 0x00000000,   0,   0, 0x00000000, 0x0A0A0A0A, 0x0B0B0B0B ],

    # Cycle 3: Read p3 via port 0, p1 via port 1.
    [  3,  1,   0,   0, 0x00000000,   0,   0, 0x00000000,   0,   0, 0x00000000, 0x0C0C0C0C, 0x0A0A0A0A ],

    # Cycle 4: Triple write again to p1/p2/p3 with new values, simultaneously
    # read p2 via port 0 and p3 via port 1 - bypass must show the NEW values.
    [  2,  3,   1,   1, 0xE1E1E1E1,   1,   2, 0xE2E2E2E2,   1,   3, 0xE3E3E3E3, 0xE2E2E2E2, 0xE3E3E3E3 ],

    # Cycle 5: Read back p1 - must hold the latest value from cycle 4.
    [  1,  0,   0,   0, 0x00000000,   0,   0, 0x00000000,   0,   0, 0x00000000, 0xE1E1E1E1,          0 ],
  ], cmdline_opts )