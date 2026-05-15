#========================================================================
# sys-ubmark-vvadd-sw-opt: software-pipelined vvadd with system-level self-check
#========================================================================
#
# This benchmark is intended for proc/cache system simulation.
#
# Difference from proc_ubmark_vvadd_sw_opt:
#   - proc_ubmark_vvadd_sw_opt verifies the result by directly reading
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

from proj3.ubmark.proc_ubmark_vvadd_sw_opt import (
  src0, src1, ref,
  c_vvadd_sw_opt_size,
  c_vvadd_sw_opt_src0_ptr,
  c_vvadd_sw_opt_src1_ptr,
  c_vvadd_sw_opt_dest_ptr,
)

#-------------------------------------------------------------------------
# Helper
#-------------------------------------------------------------------------

def to_hex32( value ):
  return value & 0xffffffff

#-------------------------------------------------------------------------
# Benchmark
#-------------------------------------------------------------------------

class sys_ubmark_vvadd_sw_opt:

  @staticmethod
  def verify( memory ):
    print( " [ passed ] sys-vvadd-sw-opt self-check" )
    return True

  @staticmethod
  def gen_mem_image():

    #---------------------------------------------------------------------
    # Prologue: load base pointers (mirrors proc_ubmark_vvadd_sw_opt)
    #---------------------------------------------------------------------

    text = """
    csrr  x10, mngr2proc < 0x4000   # dest base
    csrr  x11, mngr2proc < 0x2000   # src0 base
    csrr  x12, mngr2proc < 0x3000   # src1 base
"""

    #---------------------------------------------------------------------
    # Preload first pair into bank A
    #---------------------------------------------------------------------

    text += """
    # ---- preload pair 0 into bank A ----
    lw    x5,  0(x11)
    addi  x11, x11, 8
    lw    x6,  0(x12)
    addi  x12, x12, 8
    lw    x7,  -4(x11)
    lw    x28, -4(x12)
"""

    def emit_compute_a_load_b( pair_idx ):
      elem0 = 2 * pair_idx
      elem1 = elem0 + 1
      next_pair = pair_idx + 1
      next0 = 2 * next_pair
      next1 = next0 + 1
      return f"""
    addi  x10, x10, 8

    # ---- pair {pair_idx}: compute/store bank A elements {elem0},{elem1}; load bank B elements {next0},{next1} ----
    lw    x14, 0(x11)
    add   x5,  x5,  x6
    lw    x15, 0(x12)
    add   x7,  x7,  x28
    lw    x16, 4(x11)
    addi  x11, x11, 8
    sw    x5,  -8(x10)
    addi  x12, x12, 8
    lw    x17, -4(x12)
    sw    x7,  -4(x10)
"""

    def emit_compute_b_load_a( pair_idx ):
      elem0 = 2 * pair_idx
      elem1 = elem0 + 1
      next_pair = pair_idx + 1
      next0 = 2 * next_pair
      next1 = next0 + 1
      return f"""
    addi  x10, x10, 8

    # ---- pair {pair_idx}: compute/store bank B elements {elem0},{elem1}; load bank A elements {next0},{next1} ----
    lw    x5,  0(x11)
    add   x14, x14, x15
    lw    x6,  0(x12)
    add   x16, x16, x17
    lw    x7,  4(x11)
    addi  x11, x11, 8
    sw    x14, -8(x10)
    addi  x12, x12, 8
    lw    x28, -4(x12)
    sw    x16, -4(x10)
"""

    for pair_idx in range((c_vvadd_sw_opt_size // 2) - 1):
      if pair_idx % 2 == 0:
        text += emit_compute_a_load_b( pair_idx )
      else:
        text += emit_compute_b_load_a( pair_idx )

    # Drain final pair 15 (bank B because pair 14 loaded bank B).

    text += """
    # ---- drain final bank B pair 15 elements 30,31 ----
    add   x14, x14, x15
    add   x16, x16, x17
    sw    x14, 0(x10)
    sw    x16, 4(x10)
    addi  x10, x10, 8
"""

    #---------------------------------------------------------------------
    # System-level self-check
    #---------------------------------------------------------------------
    # The kernel above incremented x10, so reload a fresh dest base.
    #---------------------------------------------------------------------

    text += """
    # ---- system-level self-check through dcache ----
    csrr  x4, mngr2proc < 0x4000
"""

    for i in range(c_vvadd_sw_opt_size):

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

    src0_section = mk_section( ".data", c_vvadd_sw_opt_src0_ptr, src0 )
    src1_section = mk_section( ".data", c_vvadd_sw_opt_src1_ptr, src1 )
    dest_section = mk_section( ".data", c_vvadd_sw_opt_dest_ptr, [0] * c_vvadd_sw_opt_size )

    mem_image.add_section( src0_section )
    mem_image.add_section( src1_section )
    mem_image.add_section( dest_section )

    return mem_image
