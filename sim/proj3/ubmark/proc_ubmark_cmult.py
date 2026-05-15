#========================================================================
# ubmark-cmult: complex multiply kernel (UNROLLED, no branch)
#========================================================================
# Branch-less variant of cmult for evaluating an out-of-order processor
# that does not yet support branches/jumps.
#
# Equivalent to:
#   void cmplx_mult( int *dest, int *src0, int *src1, int size ) {
#     for ( int i = 0; i < size; i += 2 ) {
#       int s0r = src0[i]; int s0i = src0[i+1];
#       int s1r = src1[i]; int s1i = src1[i+1];
#       dest[i]   = s0r*s1r - s0i*s1i;
#       dest[i+1] = s0r*s1i + s0i*s1r;
#     }
#   }
# with the loop FULLY unrolled.
#
# Original kernel (per 2-element block): 4 loads + 4 muls + 1 sub + 1 add
# + 2 stores + 4 pointer/loop adds + 1 branch ~= 17 insts.
# Branch-less unrolled block drops the pointer bumps and the branch:
# 4 lw + 4 mul + 1 sub + 1 add + 2 sw = 12 insts per complex element pair.
#
# Each block uses hard-coded offsets keyed off the block index, so blocks
# are independent and all four MULs in a block can dispatch in program
# order without waiting for a backward branch.
#
# c_cmult_size counts INTS (= 2 * number of complex elements). Must be
# even. Initial value is small for stage-1 evaluation; increase by adding
# more blocks.
#
# Author : Christopher Batten (original) / unrolled for OoO eval
# Date   : September 21, 2022
#

import struct

from pymtl3 import *
from pymtl3.stdlib.proc import SparseMemoryImage

from proj3.test.tinyrv2_encoding_test import mk_section
from proj3.tinyrv2_encoding           import assemble

from proj3.ubmark.proc_ubmark_cmult_data import src0, src1, ref

# pointers for the input and output arrays
c_cmplx_mult_src0_ptr = 0x2000
c_cmplx_mult_src1_ptr = 0x3000
c_cmplx_mult_dest_ptr = 0x4000

# Number of INTS to process. Must be even (real, imag pairs).
c_cmplx_mult_size     = 200 # <= 200

class ubmark_cmult:

  # verification function, argument is a bytearray from TestMemory instance

  @staticmethod
  def verify( memory ):

    is_pass      = True
    first_failed = -1

    for i in range(c_cmplx_mult_size):
      x = struct.unpack('i', memory[c_cmplx_mult_dest_ptr + i * 4 : c_cmplx_mult_dest_ptr + (i+1) * 4] )[0]
      if not ( x == ref[i] ):
        is_pass     = False
        first_faild = i
        print( " [ failed ] dest[{i}]: {x} != ref[{i}]: {ref} ".format( i=i, x=x, ref=ref[i] ) )
        return False

    if is_pass:
      print( " [ passed ] cmult" )
      return True

  @staticmethod
  def gen_mem_image():

    assert c_cmplx_mult_size % 2 == 0, "cmult size must be even (real,imag pairs)"

    # ----------------------------------------------------------------
    # Prologue: load base pointers
    # ----------------------------------------------------------------

    text = """
    csrr  x2, mngr2proc < 0x2000   # src0 base
    csrr  x3, mngr2proc < 0x3000   # src1 base
    csrr  x4, mngr2proc < 0x4000   # dest base
"""

    # ----------------------------------------------------------------
    # Per complex-pair block, fully unrolled.
    # Each block produces dest[2k], dest[2k+1] from src0[2k..2k+1] and
    # src1[2k..2k+1]. Hard-coded offsets eliminate pointer bumps.
    # ----------------------------------------------------------------

    num_blocks = c_cmplx_mult_size // 2
    for blk in range(num_blocks):
      base_off = blk * 8         # bytes for 2 ints
      ore = base_off              # offset of real part
      oim = base_off + 4          # offset of imag part
      text += f"""
    # ---- block {blk} (complex element {blk}) ----
    lw    x6,  {ore}(x2)         # src0_real
    lw    x7,  {oim}(x2)         # src0_imag
    lw    x8,  {ore}(x3)         # src1_real
    lw    x9,  {oim}(x3)         # src1_imag
    mul   x10, x6, x8            # real * real
    mul   x11, x7, x9            # imag * imag
    mul   x12, x7, x8            # imag * real
    mul   x13, x6, x9            # real * imag
    sub   x14, x10, x11          # dest_real
    add   x15, x12, x13          # dest_imag
    sw    x14, {ore}(x4)         # dest[2k]
    sw    x15, {oim}(x4)         # dest[2k+1]
"""

    # ----------------------------------------------------------------
    # Epilogue
    # ----------------------------------------------------------------

    text += """
    csrw  proc2mngr, x0 > 0
    nop
    nop
    nop
    nop
    nop
    nop
"""

    mem_image = assemble( text )

    src0_section = mk_section( ".data", c_cmplx_mult_src0_ptr, src0 )
    src1_section = mk_section( ".data", c_cmplx_mult_src1_ptr, src1 )

    mem_image.add_section( src0_section )
    mem_image.add_section( src1_section )

    return mem_image