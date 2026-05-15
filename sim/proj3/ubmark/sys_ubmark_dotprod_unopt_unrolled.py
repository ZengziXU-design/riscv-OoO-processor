#========================================================================
# sys-ubmark-dotprod-unopt-unrolled: vector multiply with system-level self-check
#========================================================================
#
# This benchmark is intended for proc/cache system simulation.
#
# Difference from proc_ubmark_dotprod_unopt_unrolled:
#   - proc_ubmark_dotprod_unopt_unrolled verifies the result by directly
#     reading backing memory from Python.
#   - This system version verifies the result architecturally by loading
#     dest[i] back through the dcache and sending it to proc2mngr.
#
# This avoids false verify failures when the dcache is write-back and dirty
# lines have not been written back to backing memory at the end of simulation.
#
# NOTE:
#   This benchmark includes extra lw/csrw instructions for self-checking, so
#   it should be used for correctness, not for clean performance numbers.
#

from pymtl3 import *
from pymtl3.stdlib.proc import SparseMemoryImage

from proj3.test.tinyrv2_encoding_test import mk_section
from proj3.tinyrv2_encoding           import assemble

from proj3.ubmark.proc_ubmark_dotprod_unopt_unrolled import (
  src0, src1, ref,
  c_dotprod_size,
  c_dotprod_src0_ptr,
  c_dotprod_src1_ptr,
  c_dotprod_dest_ptr,
)

#-------------------------------------------------------------------------
# Helper
#-------------------------------------------------------------------------

def to_hex32( value ):
  return value & 0xffffffff

#-------------------------------------------------------------------------
# Benchmark
#-------------------------------------------------------------------------

class sys_ubmark_dotprod_unopt_unrolled:

  @staticmethod
  def verify( memory ):
    print( " [ passed ] sys-dotprod-unopt-unrolled self-check" )
    return True

  @staticmethod
  def gen_mem_image():

    #---------------------------------------------------------------------
    # Prologue: load base pointers
    #---------------------------------------------------------------------

    text = """
    csrr  x2, mngr2proc < 0x2000   # src0 base
    csrr  x3, mngr2proc < 0x3000   # src1 base
    csrr  x4, mngr2proc < 0x4000   # dest base
"""

    #---------------------------------------------------------------------
    # Main kernel: fully unrolled dotprod (mirrors proc_ubmark)
    #---------------------------------------------------------------------

    for i in range(c_dotprod_size):
      text += f"""
    # ---- element {i} ----
    lw    x6,  0(x2)
    addi  x2,  x2, 4
    lw    x7,  0(x3)
    addi  x3,  x3, 4
    mul   x8,  x6, x7
    sw    x8,  0(x4)
    addi  x4,  x4, 4
"""

    #---------------------------------------------------------------------
    # System-level self-check
    #---------------------------------------------------------------------
    # The kernel above incremented x4, so reload a fresh dest base.
    #---------------------------------------------------------------------

    text += """
    # ---- system-level self-check through dcache ----
    csrr  x4, mngr2proc < 0x4000
"""

    for i in range(c_dotprod_size):

      off = i * 4
      exp = to_hex32( ref[i] )

      text += f"""
    lw    x5, {off}(x4)
    csrw  proc2mngr, x5 > 0x{exp:08x}
"""

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
