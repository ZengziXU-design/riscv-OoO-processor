#=========================================================================
# ProcPregfile unit tests
#=========================================================================

from pymtl3 import *
from pymtl3.stdlib.test_utils import run_test_vector_sim
from proj3.ProcPregfile import ProcPregfile

# 4R4W PRF:
#   read ports  : issue0_rs1, issue0_rs2, issue1_rs1, issue1_rs2
#   write ports : alu0, alu1, mul, mem

TEST_FMT = (
  'rd_addr_issue0_rs1 rd_addr_issue0_rs2 '
  'rd_addr_issue1_rs1 rd_addr_issue1_rs2 '
  'wr_en_alu0 wr_addr_alu0 wr_data_alu0 '
  'wr_en_alu1 wr_addr_alu1 wr_data_alu1 '
  'wr_en_mul wr_addr_mul wr_data_mul '
  'wr_en_mem wr_addr_mem wr_data_mem '
  'rd_data_issue0_rs1* rd_data_issue0_rs2* '
  'rd_data_issue1_rs1* rd_data_issue1_rs2*'
)

#-------------------------------------------------------------------------
# Basic read/write through all four write ports and all four read ports
#-------------------------------------------------------------------------

def test_basic_rw( cmdline_opts ):
  dut = ProcPregfile()

  run_test_vector_sim( dut, [
    (TEST_FMT),

    # Cycle 1: Write p1/p2/p3/p4 from ALU0/ALU1/MUL/MEM.
    [  0,  0,  0,  0,
       1,  1, 0x11111111,
       1,  2, 0x22222222,
       1,  3, 0x33333333,
       1,  4, 0x44444444,
       0, 0, 0, 0 ],

    # Cycle 2: Read all four written registers at once.
    [  1,  2,  3,  4,
       0,  0, 0x00000000,
       0,  0, 0x00000000,
       0,  0, 0x00000000,
       0,  0, 0x00000000,
       0x11111111, 0x22222222, 0x33333333, 0x44444444 ],

    # Cycle 3: Same values should be visible from different read ports.
    [  4,  3,  2,  1,
       0,  0, 0x00000000,
       0,  0, 0x00000000,
       0,  0, 0x00000000,
       0,  0, 0x00000000,
       0x44444444, 0x33333333, 0x22222222, 0x11111111 ],
  ], cmdline_opts )

#-------------------------------------------------------------------------
# Same-cycle bypass forwarding from all four write ports
#-------------------------------------------------------------------------

def test_bypass_forwarding( cmdline_opts ):
  dut = ProcPregfile()

  run_test_vector_sim( dut, [
    (TEST_FMT),

    # Cycle 1: Every read port consumes a value written in the same cycle.
    [ 10, 11, 12, 13,
       1, 10, 0xAAAAAAAA,
       1, 11, 0xBBBBBBBB,
       1, 12, 0xCCCCCCCC,
       1, 13, 0xDDDDDDDD,
       0xAAAAAAAA, 0xBBBBBBBB, 0xCCCCCCCC, 0xDDDDDDDD ],

    # Cycle 2: Cross the producing functional unit and consuming read port.
    [ 23, 22, 21, 20,
       1, 20, 0x20202020,
       1, 21, 0x21212121,
       1, 22, 0x22222222,
       1, 23, 0x23232323,
       0x23232323, 0x22222222, 0x21212121, 0x20202020 ],
  ], cmdline_opts )

#-------------------------------------------------------------------------
# p0 protection
#-------------------------------------------------------------------------

def test_p0_protection( cmdline_opts ):
  dut = ProcPregfile()

  run_test_vector_sim( dut, [
    (TEST_FMT),

    # Cycle 1: Try to overwrite p0 from every write port.
    [  0,  0,  0,  0,
       1,  0, 0xDEADBEEF,
       1,  0, 0xBADF00D0,
       1,  0, 0xCAFEBABE,
       1,  0, 0xFFFFFFFF,
       0, 0, 0, 0 ],

    # Cycle 2: p0 should still be hardwired to zero.
    [  0,  0,  0,  0,
       0,  0, 0x00000000,
       0,  0, 0x00000000,
       0,  0, 0x00000000,
       0,  0, 0x00000000,
       0, 0, 0, 0 ],
  ], cmdline_opts )

#-------------------------------------------------------------------------
# Same-address bypass/write priority
#-------------------------------------------------------------------------

def test_bypass_priority( cmdline_opts ):
  dut = ProcPregfile()

  run_test_vector_sim( dut, [
    (TEST_FMT),

    # ALU0 has highest same-cycle bypass priority, then ALU1, MUL, MEM.
    [ 30, 30, 30, 30,
       1, 30, 0xA0A0A0A0,
       1, 30, 0xA1A1A1A1,
       1, 30, 0xB0B0B0B0,
       1, 30, 0xC0C0C0C0,
       0xA0A0A0A0, 0xA0A0A0A0, 0xA0A0A0A0, 0xA0A0A0A0 ],

    # The stored value follows the same priority for this defensive case.
    [ 30, 30, 30, 30,
       0,  0, 0x00000000,
       0,  0, 0x00000000,
       0,  0, 0x00000000,
       0,  0, 0x00000000,
       0xA0A0A0A0, 0xA0A0A0A0, 0xA0A0A0A0, 0xA0A0A0A0 ],
  ], cmdline_opts )
