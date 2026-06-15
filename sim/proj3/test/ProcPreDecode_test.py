#=========================================================================
# ProcPreDecode unit tests
#=========================================================================
# PreDecode emits lightweight instruction-class flags consumed by IQ/Ctrl:
#   is_csr -> CSRR / CSRW    (opcode 7'b1110011)
#   is_mem -> LW / SW         (opcode 7'b0000011 or 7'b0100011)
#   is_mul -> MUL             (RV32M encoding)

from pymtl3 import *
from pymtl3.stdlib.test_utils import run_test_vector_sim

from proj3.ProcPreDecode import ProcPreDecode

TEST_FMT = (
  'inst '
  'rs1_addr* rs2_addr* rd_addr* '
  'rs1_valid* rs2_valid* rd_valid* '
  'is_csr* is_mem*'
)

#-------------------------------------------------------------------------
# test R-Type (e.g., ADD, SUB, MUL)
#-------------------------------------------------------------------------
# Expect: rs1_valid=1, rs2_valid=1, rd_valid=1, is_csr=0, is_mem=0
def test_predecode_rtype( cmdline_opts ):
  dut = ProcPreDecode()

  run_test_vector_sim( dut, [
    (TEST_FMT),
    # ADD x1, x2, x3 -> 0x003100b3 (rs1=2, rs2=3, rd=1)
    [ 0b0000000_00011_00010_000_00001_0110011, 2, 3, 1,  1, 1, 1,  0, 0 ],
    # SUB x4, x5, x6 -> 0x40628233 (rs1=5, rs2=6, rd=4)
    [ 0b0100000_00110_00101_000_00100_0110011, 5, 6, 4,  1, 1, 1,  0, 0 ],
  ], cmdline_opts )

#-------------------------------------------------------------------------
# test I-Type (e.g., ADDI, LW)
#-------------------------------------------------------------------------
# ADDI: rs1_valid=1, rs2_valid=0, rd_valid=1, is_csr=0, is_mem=0
# LW  : rs1_valid=1, rs2_valid=0, rd_valid=1, is_csr=0, is_mem=1
def test_predecode_itype( cmdline_opts ):
  dut = ProcPreDecode()

  run_test_vector_sim( dut, [
    (TEST_FMT),
    # ADDI x7, x8, 15 -> 0x00f40393 (rs1=8, rd=7)
    [ 0b000000001111_01000_000_00111_0010011,  8, 15, 7,  1, 0, 1,  0, 0 ],
    # LW x9, 4(x10) -> 0x00452483 (rs1=10, rd=9)
    [ 0b000000000100_01010_010_01001_0000011,  10, 4, 9,  1, 0, 1,  0, 1 ],
  ], cmdline_opts )

#-------------------------------------------------------------------------
# test S-Type & B-Type (e.g., SW, BEQ)
#-------------------------------------------------------------------------
# SW : rs1_valid=1, rs2_valid=1, rd_valid=0, is_csr=0, is_mem=1
# BEQ: rs1_valid=1, rs2_valid=1, rd_valid=0, is_csr=0, is_mem=0
def test_predecode_stype_btype( cmdline_opts ):
  dut = ProcPreDecode()

  run_test_vector_sim( dut, [
    (TEST_FMT),
    # SW x11, 8(x12) -> 0x00b62423 (rs1=12, rs2=11)
    [ 0b0000000_01011_01100_010_01000_0100011, 12, 11, 8,  1, 1, 0,  0, 1 ],
    # BEQ x13, x14, label -> 0x00e68063 (rs1=13, rs2=14)
    [ 0b0000000_01110_01101_000_00000_1100011, 13, 14, 0,  1, 1, 0,  0, 0 ],
  ], cmdline_opts )

#-------------------------------------------------------------------------
# test U-Type & J-Type (e.g., LUI, JAL)
#-------------------------------------------------------------------------
# Expect: rs1_valid=0, rs2_valid=0, rd_valid=1, is_csr=0, is_mem=0
def test_predecode_utype_jtype( cmdline_opts ):
  dut = ProcPreDecode()

  run_test_vector_sim( dut, [
    (TEST_FMT),
    # LUI x15, 0x1000
    [ 0b00000001000000000000_01111_0110111,    '?', '?', 15,  0, 0, 1,  0, 0 ],
    # JAL x16, label
    [ 0b00000000000000000000_10000_1101111,    '?', '?', 16,  0, 0, 1,  0, 0 ],
  ], cmdline_opts )

#-------------------------------------------------------------------------
# test CSR Instructions (CSRR / CSRW)
#-------------------------------------------------------------------------
# Both should set is_csr=1, is_mem=0.
def test_predecode_csr( cmdline_opts ):
  dut = ProcPreDecode()

  run_test_vector_sim( dut, [
    (TEST_FMT),
    # CSRR x17, mngr2proc -> 0xfc0028f3
    # rs1=0, rs2=0(unused), rd=17, rs1_valid=0, rs2_valid=0, rd_valid=1
    [ 0b111111000000_00000_010_10001_1110011,  0, 0, 17,  0, 0, 1,  1, 0 ],
    # CSRW proc2mngr, x18 -> 0x7c091073
    # rs1=18, rs2=0(unused), rd=0, rs1_valid=1, rs2_valid=0, rd_valid=0
    [ 0b011111000000_10010_001_00000_1110011,  18, 0, 0,   1, 0, 0,  1, 0 ],
  ], cmdline_opts )

#-------------------------------------------------------------------------
# test Memory Instruction Classification  (NEW)
#-------------------------------------------------------------------------
# Focus test for the new is_mem flag. Covers:
#   * Multiple LW / SW variants with different rd / rs1 / rs2 / immediates
#   * is_mem must be derived from opcode alone (independent of immediate
#     value, so negative offsets and zero offsets both classify the same)
#   * is_csr stays 0 for every memory instruction
#   * Verifies the rs1/rs2/rd valid bits stay correct alongside is_mem
def test_predecode_mem( cmdline_opts ):
  dut = ProcPreDecode()

  run_test_vector_sim( dut, [
    (TEST_FMT),
    # LW x1, 0(x2)            (zero offset)
    [ 0b000000000000_00010_010_00001_0000011,  2,  0, 1,  1, 0, 1,  0, 1 ],
    # LW x20, 0x7FF(x3)       (max positive 12-bit immediate)
    [ 0b011111111111_00011_010_10100_0000011,  3,  31, 20, 1, 0, 1,  0, 1 ],
    # LW x5, -4(x6)           (negative offset; imm=0xFFC)
    [ 0b111111111100_00110_010_00101_0000011,  6,  28, 5,  1, 0, 1,  0, 1 ],
    # SW x7, 0(x8)            (zero offset)
    [ 0b0000000_00111_01000_010_00000_0100011, 8,  7,  0,  1, 1, 0,  0, 1 ],
    # SW x9, -8(x10)          (negative offset)
    [ 0b1111111_01001_01010_010_11000_0100011, 10, 9,  24, 1, 1, 0,  0, 1 ],
  ], cmdline_opts )

#-------------------------------------------------------------------------
# test Mutual Exclusion: is_csr vs is_mem  (NEW)
#-------------------------------------------------------------------------
# Sanity: is_csr and is_mem are derived from disjoint opcode buckets,
# so no instruction should ever set both.  Walking through one example
# of every major class is enough to lock that property in.
def test_predecode_class_exclusive( cmdline_opts ):
  dut = ProcPreDecode()

  run_test_vector_sim( dut, [
    (TEST_FMT),
    # ADD  - neither
    [ 0b0000000_00011_00010_000_00001_0110011, 2, 3, 1,  1, 1, 1,  0, 0 ],
    # ADDI - neither
    [ 0b000000000001_00010_000_00001_0010011,  2, 1, 1,  1, 0, 1,  0, 0 ],
    # LW   - is_mem only
    [ 0b000000000000_00010_010_00001_0000011,  2, 0, 1,  1, 0, 1,  0, 1 ],
    # SW   - is_mem only
    [ 0b0000000_00001_00010_010_00000_0100011, 2, 1, 0,  1, 1, 0,  0, 1 ],
    # CSRR - is_csr only
    [ 0b111111000000_00000_010_00001_1110011,  0, 0, 1,  0, 0, 1,  1, 0 ],
    # CSRW - is_csr only
    [ 0b011111000000_00010_001_00000_1110011,  2, 0, 0,  1, 0, 0,  1, 0 ],
    # BEQ  - neither
    [ 0b0000000_00010_00001_000_00000_1100011, 1, 2, 0,  1, 1, 0,  0, 0 ],
    # LUI  - neither
    [ 0b00000001000000000000_00001_0110111,    '?', '?', 1,  0, 0, 1,  0, 0 ],
  ], cmdline_opts )

#-------------------------------------------------------------------------
# test MUL classification
#-------------------------------------------------------------------------

def test_predecode_mul( cmdline_opts ):
  dut = ProcPreDecode()

  run_test_vector_sim( dut, [
    'inst is_mul*',
    [ 0b0000001_00011_00010_000_00001_0110011, 1 ], # MUL
    [ 0b0000000_00011_00010_000_00001_0110011, 0 ], # ADD
    [ 0b0100000_00011_00010_000_00001_0110011, 0 ], # SUB
  ], cmdline_opts )
