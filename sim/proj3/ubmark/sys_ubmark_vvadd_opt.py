#========================================================================
# sys-ubmark-vvadd-opt: vector-vector addition kernel with self-check
#========================================================================
#
# This benchmark is intended for proc/cache system simulation.
#
# Difference from proc_ubmark_vvadd_opt:
#   - proc_ubmark_vvadd_opt verifies the result by directly reading backing
#     memory from Python.
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

# Initial size for the unrolled benchmark. Must be a multiple of 4.

c_vvadd_size = 100

#-------------------------------------------------------------------------
# Helper
#-------------------------------------------------------------------------

def to_hex32( value ):
  return value & 0xffffffff

#-------------------------------------------------------------------------
# Benchmark
#-------------------------------------------------------------------------

class sys_ubmark_vvadd_opt:

  #-----------------------------------------------------------------------
  # verification function
  #-----------------------------------------------------------------------
  # For this system-level benchmark, correctness is checked by the
  # proc2mngr stream generated in the assembly below. If the processor
  # produces a wrong value, the StreamSinkFL in the harness should fail
  # before this verify() function is reached.
  #
  # We intentionally do not read backing memory here, because a write-back
  # dcache may still contain dirty dest data that has not been written back.

  @staticmethod
  def verify( memory ):
    print( " [ passed ] sys-vvadd-opt self-check" )
    return True

  #-----------------------------------------------------------------------
  # generate memory image
  #-----------------------------------------------------------------------

  @staticmethod
  def gen_mem_image():

    assert c_vvadd_size % 4 == 0, "vvadd-opt size must be a multiple of 4"

    #---------------------------------------------------------------------
    # Prologue: load base pointers
    #---------------------------------------------------------------------

    text = """
    csrr  x2, mngr2proc < 0x2000   # src0 base
    csrr  x3, mngr2proc < 0x3000   # src1 base
    csrr  x4, mngr2proc < 0x4000   # dest base
"""

    #---------------------------------------------------------------------
    # Main kernel: 4-way unrolled vvadd
    #---------------------------------------------------------------------
    #
    # Each block processes 4 elements:
    #
    #   dest[i+0] = src0[i+0] + src1[i+0]
    #   dest[i+1] = src0[i+1] + src1[i+1]
    #   dest[i+2] = src0[i+2] + src1[i+2]
    #   dest[i+3] = src0[i+3] + src1[i+3]
    #
    # Hard-coded offsets remove pointer bumps and branches.
    #---------------------------------------------------------------------

    num_blocks = c_vvadd_size // 4

    for blk in range(num_blocks):

      base_off = blk * 16   # 4 elements * 4 bytes
      o0       = base_off
      o1       = base_off + 4
      o2       = base_off + 8
      o3       = base_off + 12

      text += f"""
    # ---- block {blk} (elements {blk*4}..{blk*4+3}) ----
    lw    x6,  {o0}(x2)
    lw    x7,  {o1}(x2)
    lw    x8,  {o2}(x2)
    lw    x9,  {o3}(x2)

    lw    x10, {o0}(x3)
    lw    x11, {o1}(x3)
    lw    x12, {o2}(x3)
    lw    x13, {o3}(x3)

    add   x6,  x6,  x10
    add   x7,  x7,  x11
    add   x8,  x8,  x12
    add   x9,  x9,  x13

    sw    x6,  {o0}(x4)
    sw    x7,  {o1}(x4)
    sw    x8,  {o2}(x4)
    sw    x9,  {o3}(x4)
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