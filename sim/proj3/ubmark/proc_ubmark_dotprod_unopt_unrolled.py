#========================================================================
# ubmark-dotprod-unopt-unrolled: vector-vector multiply kernel
#========================================================================
# Branch-less Python-generated variant for evaluating an out-of-order
# processor that does not yet support branches/jumps.
#
# Equivalent to:
#
#   void dotprod( int *dest, int *src0, int *src1, int size ) {
#     for ( int i = 0; i < size; i++ )
#       dest[i] = src0[i] * src1[i];
#   }
#
# The loop is FULLY unrolled in Python. The generated TinyRV2 assembly has
# no branch/jump instructions. Verification is done in Python using the
# memory image after simulation, not by an in-program branch-based checker.
#========================================================================

import struct

from pymtl3 import *
from pymtl3.stdlib.proc import SparseMemoryImage

from proj3.test.tinyrv2_encoding_test import mk_section
from proj3.tinyrv2_encoding           import assemble

# ----------------------------------------------------------------------
# Data
# ----------------------------------------------------------------------

c_dotprod_src0_ptr = 0x2000
c_dotprod_src1_ptr = 0x3000
c_dotprod_dest_ptr = 0x4000

# Number of integer elements to process.
c_dotprod_size     = 100

# These match the data in dotprod_unopt_unrolled.S, although the assembly
# file comments/name describe a vector-vector multiply benchmark rather than
# a scalar dot-product accumulator.

src0 = [ (i % 23) + 1 for i in range(c_dotprod_size) ]
src1 = [ ((5*i + 7) % 31) + 1 for i in range(c_dotprod_size) ]

ref = [ src0[i] * src1[i] for i in range(c_dotprod_size) ]

#========================================================================
# ubmark_dotprod_unopt_unrolled
#========================================================================

class ubmark_dotprod_unopt_unrolled:

  # verification function, argument is a bytearray from TestMemory instance

  @staticmethod
  def verify( memory ):

    for i in range(c_dotprod_size):
      x = struct.unpack(
        'i',
        memory[
          c_dotprod_dest_ptr + i * 4 :
          c_dotprod_dest_ptr + (i+1) * 4
        ]
      )[0]

      if x != ref[i]:
        print(
          " [ failed ] dest[{i}]: {x} != ref[{i}]: {ref} ".format(
            i=i, x=x, ref=ref[i]
          )
        )
        return False

    print( " [ passed ] dotprod-unopt-unrolled" )
    return True

  @staticmethod
  def gen_mem_image():

    # ----------------------------------------------------------------
    # Prologue: load base pointers
    # ----------------------------------------------------------------
    # x2 = src0 base
    # x3 = src1 base
    # x4 = dest base
    # ----------------------------------------------------------------

    text = """
    csrr  x2, mngr2proc < 0x2000   # src0 base
    csrr  x3, mngr2proc < 0x3000   # src1 base
    csrr  x4, mngr2proc < 0x4000   # dest base
"""

    # ----------------------------------------------------------------
    # Per-element block, fully unrolled.
    # ----------------------------------------------------------------
    # Same instruction order as the provided .S file:
    #   lw    x6, 0(x2)
    #   addi  x2, x2, 4
    #   lw    x7, 0(x3)
    #   addi  x3, x3, 4
    #   mul   x8, x6, x7
    #   sw    x8, 0(x4)
    #   addi  x4, x4, 4
    # ----------------------------------------------------------------

    for i in range(c_dotprod_size):
      text += f"""
    # ---- element {i} ----
    lw    x6,  0(x2)             # a = *src0_ptr
    addi  x2,  x2, 4             # src0_ptr++
    lw    x7,  0(x3)             # b = *src1_ptr
    addi  x3,  x3, 4             # src1_ptr++
    mul   x8,  x6, x7            # p = a * b
    sw    x8,  0(x4)             # *dest_ptr = p
    addi  x4,  x4, 4             # dest_ptr++
"""

    # ----------------------------------------------------------------
    # Epilogue
    # ----------------------------------------------------------------
    # No branch-based stop loop. proc-sim can verify through Python.
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

    src0_section = mk_section( ".data", c_dotprod_src0_ptr, src0 )
    src1_section = mk_section( ".data", c_dotprod_src1_ptr, src1 )
    dest_section = mk_section( ".data", c_dotprod_dest_ptr, [0] * c_dotprod_size )

    mem_image.add_section( src0_section )
    mem_image.add_section( src1_section )
    mem_image.add_section( dest_section )

    return mem_image


# Backward-compatible alias for the benchmark name used in the assembly comments.
ubmark_vvmul_unopt_unrolled = ubmark_dotprod_unopt_unrolled
