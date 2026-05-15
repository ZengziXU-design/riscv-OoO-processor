#========================================================================
# ubmark-vmuladd2-unopt: vector multiply-add kernel with two MUL RAW chains
#========================================================================
# Branch-less variant of a vector multiply-add kernel for evaluating an
# out-of-order processor that does not yet support branches/jumps.
#
# Equivalent to:
#
#   void vmuladd2( int *dest, int *src0, int *src1, int size ) {
#     for ( int i = 0; i < size; i++ ) {
#       int a  = src0[i];
#       int b  = src1[i];
#
#       int p0 = a * b;
#       int q0 = p0 + 7;
#
#       int p1 = a * 3;
#       int q1 = p1 + b;
#
#       int s  = a + b;
#       int d  = a - b;
#
#       dest[i] = q0 + q1 + s + d;
#     }
#   }
#
# Simplified:
#
#   dest[i] = src0[i] * src1[i] + 5 * src0[i] + src1[i] + 7;
#
# with the loop FULLY unrolled.
#
# The key pattern in each unrolled iteration is:
#
#   mul   x8,  x6,  x7      # p0 = a*b
#   add   x9,  x8,  x21     # q0 = p0+7, RAW on first mul
#
#   mul   x10, x6,  x20     # p1 = a*3
#   add   x11, x10, x7      # q1 = p1+b, RAW on second mul
#
#   add   x12, x6,  x7      # s = a+b, independent
#   sub   x15, x6,  x7      # d = a-b, independent
#
# This is OoO-friendly because the dependent consumers can wait in the
# issue queue, while younger independent instructions continue to issue.
# It is less friendly to a simple in-order dual-issue superscalar machine
# because the first dependent add can create head-of-line blocking.
#========================================================================

import struct

from pymtl3 import *
from pymtl3.stdlib.proc import SparseMemoryImage

from proj3.test.tinyrv2_encoding_test import mk_section
from proj3.tinyrv2_encoding           import assemble

# ----------------------------------------------------------------------
# Data
# ----------------------------------------------------------------------

c_vmuladd2_src0_ptr = 0x2000
c_vmuladd2_src1_ptr = 0x3000
c_vmuladd2_dest_ptr = 0x4000

# Number of integer elements to process.
# Increase this if you want a longer eval.
c_vmuladd2_size     = 100

# Keep values small to avoid signed 32-bit overflow.
# These are generated locally so this benchmark does not need a separate
# proc_ubmark_vmuladd2_data.py file.

src0 = [ (i % 23) + 1          for i in range(c_vmuladd2_size) ]
src1 = [ ((3*i + 5) % 29) + 1 for i in range(c_vmuladd2_size) ]

# Equivalent result:
#
#   p0 = src0[i] * src1[i]
#   q0 = p0 + 7
#
#   p1 = src0[i] * 3
#   q1 = p1 + src1[i]
#
#   s  = src0[i] + src1[i]
#   d  = src0[i] - src1[i]
#
#   ref = q0 + q1 + s + d
#
# Simplified:
#
#   ref = src0[i] * src1[i] + 5 * src0[i] + src1[i] + 7

ref = [
  src0[i] * src1[i] + 5 * src0[i] + src1[i] + 7
  for i in range(c_vmuladd2_size)
]

#========================================================================
# ubmark_vmuladd2_unopt
#========================================================================

class ubmark_vmuladd2_unopt:

  # verification function, argument is a bytearray from TestMemory instance

  @staticmethod
  def verify( memory ):

    for i in range(c_vmuladd2_size):
      x = struct.unpack(
        'i',
        memory[
          c_vmuladd2_dest_ptr + i * 4 :
          c_vmuladd2_dest_ptr + (i+1) * 4
        ]
      )[0]

      if x != ref[i]:
        print(
          " [ failed ] dest[{i}]: {x} != ref[{i}]: {ref} ".format(
            i=i, x=x, ref=ref[i]
          )
        )
        return False

    print( " [ passed ] vmuladd2-unopt" )
    return True

  @staticmethod
  def gen_mem_image():

    # ----------------------------------------------------------------
    # Prologue: load base pointers and constants
    # ----------------------------------------------------------------
    # x2  = src0 base
    # x3  = src1 base
    # x4  = dest base
    #
    # x20 = 3
    # x21 = 7
    # ----------------------------------------------------------------

    text = """
    csrr  x2,  mngr2proc < 0x2000   # src0 base
    csrr  x3,  mngr2proc < 0x3000   # src1 base
    csrr  x4,  mngr2proc < 0x4000   # dest base

    csrr  x20, mngr2proc < 3        # constant 3
    csrr  x21, mngr2proc < 7        # constant 7
"""

    # ----------------------------------------------------------------
    # Per-element block, fully unrolled.
    # ----------------------------------------------------------------
    #
    # Per element:
    #
    #   a  = src0[i]
    #   b  = src1[i]
    #
    #   p0 = a * b
    #   q0 = p0 + 7
    #
    #   p1 = a * 3
    #   q1 = p1 + b
    #
    #   s  = a + b
    #   d  = a - b
    #
    #   r  = q0 + q1 + s + d
    #   dest[i] = r
    #
    # Register usage in each unrolled block:
    #
    #   x6  = a
    #   x7  = b
    #   x8  = p0
    #   x9  = q0
    #   x10 = p1
    #   x11 = q1
    #   x12 = s
    #   x13 = q0 + q1
    #   x14 = r
    #   x15 = d
    #
    # The instruction order intentionally places dependent consumers right
    # after long-latency multiplications. This creates head-of-line blocking
    # for in-order issue, while an OoO issue queue can keep the consumers
    # waiting and issue younger independent work.
    # ----------------------------------------------------------------

    for i in range(c_vmuladd2_size):
      off = i * 4

      text += f"""
    # ---- element {i} ----
    lw    x6,  {off}(x2)          # a = src0[i]
    lw    x7,  {off}(x3)          # b = src1[i]

    mul   x8,  x6,  x7            # p0 = a * b
    add   x9,  x8,  x21           # q0 = p0 + 7, RAW on first mul

    mul   x10, x6,  x20           # p1 = a * 3
    add   x11, x10, x7            # q1 = p1 + b, RAW on second mul

    add   x12, x6,  x7            # s  = a + b
    sub   x15, x6,  x7            # d  = a - b, independent work

    add   x13, x9,  x11           # q0 + q1
    add   x14, x13, x12           # q0 + q1 + s
    add   x14, x14, x15           # r = q0 + q1 + s + d

    sw    x14, {off}(x4)          # dest[i] = r
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

    src0_section = mk_section( ".data", c_vmuladd2_src0_ptr, src0 )
    src1_section = mk_section( ".data", c_vmuladd2_src1_ptr, src1 )

    mem_image.add_section( src0_section )
    mem_image.add_section( src1_section )

    return mem_image