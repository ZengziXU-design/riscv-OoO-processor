#========================================================================
# sys-ubmark-cmult: complex multiply kernel with system-level self-check
#========================================================================
#
# This benchmark is intended for proc/cache system simulation.
#
# Difference from proc_ubmark_cmult:
#   - proc_ubmark_cmult verifies the result by directly reading backing
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

from proj3.ubmark.proc_ubmark_cmult_data import src0, src1, ref

#-------------------------------------------------------------------------
# Data addresses
#-------------------------------------------------------------------------

c_cmplx_mult_src0_ptr = 0x2000
c_cmplx_mult_src1_ptr = 0x3000
c_cmplx_mult_dest_ptr = 0x4000

# Number of INTS to process. Must be even.
# Real/imag pairs, so 200 ints = 100 complex numbers.

c_cmplx_mult_size = 200

#-------------------------------------------------------------------------
# Helper
#-------------------------------------------------------------------------

def to_hex32( value ):
  return value & 0xffffffff

#-------------------------------------------------------------------------
# Benchmark
#-------------------------------------------------------------------------

class sys_ubmark_cmult:

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
    print( " [ passed ] sys-cmult self-check" )
    return True

  #-----------------------------------------------------------------------
  # generate memory image
  #-----------------------------------------------------------------------

  @staticmethod
  def gen_mem_image():

    assert c_cmplx_mult_size % 2 == 0, "cmult size must be even"

    #---------------------------------------------------------------------
    # Prologue: load base pointers
    #---------------------------------------------------------------------

    text = """
    csrr  x2, mngr2proc < 0x2000   # src0 base
    csrr  x3, mngr2proc < 0x3000   # src1 base
    csrr  x4, mngr2proc < 0x4000   # dest base
"""

    #---------------------------------------------------------------------
    # Main kernel: fully unrolled complex multiply
    #---------------------------------------------------------------------
    #
    # For each complex pair:
    #
    #   dest_real = src0_real * src1_real - src0_imag * src1_imag
    #   dest_imag = src0_imag * src1_real + src0_real * src1_imag
    #
    # Each complex number uses two ints:
    #   real at offset base_off
    #   imag at offset base_off + 4
    #---------------------------------------------------------------------

    num_blocks = c_cmplx_mult_size // 2

    for blk in range(num_blocks):

      base_off = blk * 8
      ore      = base_off
      oim      = base_off + 4

      text += f"""
    # ---- block {blk} ----
    lw    x6,  {ore}(x2)         # src0_real
    lw    x7,  {oim}(x2)         # src0_imag
    lw    x8,  {ore}(x3)         # src1_real
    lw    x9,  {oim}(x3)         # src1_imag

    mul   x10, x6, x8            # src0_real * src1_real
    mul   x11, x7, x9            # src0_imag * src1_imag
    mul   x12, x7, x8            # src0_imag * src1_real
    mul   x13, x6, x9            # src0_real * src1_imag

    sub   x14, x10, x11          # dest_real
    add   x15, x12, x13          # dest_imag

    sw    x14, {ore}(x4)         # dest[2k]
    sw    x15, {oim}(x4)         # dest[2k+1]
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

    for i in range(c_cmplx_mult_size):

      off = i * 4
      exp = to_hex32( ref[i] )

      text += f"""
    lw    x5, {off}(x4)
    csrw  proc2mngr, x5 > 0x{exp:08x}
"""

    # Final marker. This is optional, but useful to confirm the program
    # reached the end.

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

    src0_section = mk_section( ".data", c_cmplx_mult_src0_ptr, src0 )
    src1_section = mk_section( ".data", c_cmplx_mult_src1_ptr, src1 )

    mem_image.add_section( src0_section )
    mem_image.add_section( src1_section )

    return mem_image