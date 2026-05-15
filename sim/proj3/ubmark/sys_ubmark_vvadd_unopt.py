#========================================================================
# sys-ubmark-vvadd-unopt: vector-vector addition kernel with self-check
#========================================================================
#
# This benchmark is intended for proc/cache system simulation.
#
# Difference from proc_ubmark_vvadd_unopt:
#   - proc_ubmark_vvadd_unopt verifies the result by directly reading
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

from proj3.ubmark.proc_ubmark_vvadd_data import src0, src1, ref

#-------------------------------------------------------------------------
# Data addresses
#-------------------------------------------------------------------------

c_vvadd_src0_ptr = 0x2000
c_vvadd_src1_ptr = 0x3000
c_vvadd_dest_ptr = 0x4000

# Number of ints to process.

c_vvadd_size = 100

#-------------------------------------------------------------------------
# Helper
#-------------------------------------------------------------------------

def to_hex32( value ):
  return value & 0xffffffff

#-------------------------------------------------------------------------
# Benchmark
#-------------------------------------------------------------------------

class sys_ubmark_vvadd_unopt:

  #-----------------------------------------------------------------------
  # verification function
  #-----------------------------------------------------------------------
  # Correctness is checked through proc2mngr in the generated assembly.
  # Do not read backing memory here, since dirty dcache lines may not have
  # been written back.

  @staticmethod
  def verify( memory ):
    print( " [ passed ] sys-vvadd-unopt self-check" )
    return True

  #-----------------------------------------------------------------------
  # generate memory image
  #-----------------------------------------------------------------------

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
    # Main kernel: fully unrolled vvadd
    #---------------------------------------------------------------------
    #
    # For each element:
    #
    #   dest[i] = src0[i] + src1[i]
    #
    # Each element uses hard-coded offsets and rotated temporary registers.
    #---------------------------------------------------------------------

    tmp_pool = [6, 7, 8, 9, 10, 11, 12, 13]

    for i in range(c_vvadd_size):

      off = i * 4
      ta  = tmp_pool[ (2*i)     % len(tmp_pool) ]
      tb  = tmp_pool[ (2*i + 1) % len(tmp_pool) ]

      text += f"""
    # ---- element {i} ----
    lw    x{ta}, {off}(x2)
    lw    x{tb}, {off}(x3)
    add   x{ta}, x{ta}, x{tb}
    sw    x{ta}, {off}(x4)
"""

    #---------------------------------------------------------------------
    # System-level self-check
    #---------------------------------------------------------------------
    #
    # Load every dest[i] back through the dcache and send it to proc2mngr.
    # This checks the architectural memory-system-visible result, instead
    # of checking backing memory directly from Python.
    #---------------------------------------------------------------------

    text += """
    # ---- system-level self-check through dcache ----
"""

    for i in range(c_vvadd_size):

      off = i * 4
      exp = to_hex32( ref[i] )

      text += f"""
    lw    x5, {off}(x4)
    csrw  proc2mngr, x5 > 0x{exp:08x}
"""

    # Final marker. Useful to confirm the program reached the end.

    text += """
    csrw  proc2mngr, x0 > 0
    nop
    nop
    nop
    nop
    nop
    nop
"""

    # Assemble program

    mem_image = assemble( text )

    # Add data sections

    src0_section = mk_section( ".data", c_vvadd_src0_ptr, src0 )
    src1_section = mk_section( ".data", c_vvadd_src1_ptr, src1 )

    mem_image.add_section( src0_section )
    mem_image.add_section( src1_section )

    return mem_image