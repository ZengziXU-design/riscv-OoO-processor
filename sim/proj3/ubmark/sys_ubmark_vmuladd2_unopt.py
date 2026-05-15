#========================================================================
# sys-ubmark-vmuladd2-unopt: vector multiply-add with system-level self-check
#========================================================================
#
# This benchmark is intended for proc/cache system simulation.
#
# Difference from proc_ubmark_vmuladd2_unopt:
#   - proc_ubmark_vmuladd2_unopt verifies the result by directly reading
#     backing memory from Python.
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

from proj3.ubmark.proc_ubmark_vmuladd2_unopt import (
  src0, src1, ref,
  c_vmuladd2_size,
  c_vmuladd2_src0_ptr,
  c_vmuladd2_src1_ptr,
  c_vmuladd2_dest_ptr,
)

#-------------------------------------------------------------------------
# Helper
#-------------------------------------------------------------------------

def to_hex32( value ):
  return value & 0xffffffff

#-------------------------------------------------------------------------
# Benchmark
#-------------------------------------------------------------------------

class sys_ubmark_vmuladd2_unopt:

  @staticmethod
  def verify( memory ):
    print( " [ passed ] sys-vmuladd2-unopt self-check" )
    return True

  @staticmethod
  def gen_mem_image():

    #---------------------------------------------------------------------
    # Prologue: load base pointers and constants
    #---------------------------------------------------------------------

    text = """
    csrr  x2,  mngr2proc < 0x2000   # src0 base
    csrr  x3,  mngr2proc < 0x3000   # src1 base
    csrr  x4,  mngr2proc < 0x4000   # dest base

    csrr  x20, mngr2proc < 3        # constant 3
    csrr  x21, mngr2proc < 7        # constant 7
"""

    #---------------------------------------------------------------------
    # Main kernel: fully unrolled vmuladd2 (mirrors proc_ubmark_vmuladd2_unopt)
    #---------------------------------------------------------------------

    for i in range(c_vmuladd2_size):
      off = i * 4

      text += f"""
    # ---- element {i} ----
    lw    x6,  {off}(x2)
    lw    x7,  {off}(x3)

    mul   x8,  x6,  x7
    add   x9,  x8,  x21

    mul   x10, x6,  x20
    add   x11, x10, x7

    add   x12, x6,  x7
    sub   x15, x6,  x7

    add   x13, x9,  x11
    add   x14, x13, x12
    add   x14, x14, x15

    sw    x14, {off}(x4)
"""

    #---------------------------------------------------------------------
    # System-level self-check
    #---------------------------------------------------------------------
    # Reload dest base into a fresh register, then load every dest[i] back
    # through the dcache and send it to proc2mngr.
    #---------------------------------------------------------------------

    text += """
    # ---- system-level self-check through dcache ----
    csrr  x4, mngr2proc < 0x4000
"""

    for i in range(c_vmuladd2_size):

      off = i * 4
      exp = to_hex32( ref[i] )

      text += f"""
    lw    x5, {off}(x4)
    csrw  proc2mngr, x5 > 0x{exp:08x}
"""

    # Final marker.

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
