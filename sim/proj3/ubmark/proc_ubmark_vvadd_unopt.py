#========================================================================
# ubmark-vvadd-unopt: vector-vector addition kernel (UNROLLED, no branch)
#========================================================================
# Branch-less variant of vvadd-unopt for evaluating an out-of-order
# processor that does not yet support branches/jumps.
#
# Equivalent to:
#   void vvadd( int *dest, int *src0, int *src1, int size ) {
#     for ( int i = 0; i < size; i++ )
#       *dest++ = *src0++ + *src1++;
#   }
# with the loop FULLY unrolled.
#
# Original kernel: 1 element per iteration, ~9 instructions.
# Unrolled by N copies => N elements, ~9*N instructions in the kernel
# body, no branch, no jal. Increase N below by appending more copies
# of the per-element block (or by raising c_vvadd_size and adding the
# corresponding lw/add/sw triples).
#
# Author : Christopher Batten (original) / unrolled for OoO eval
# Date   : September 21, 2022
#

import struct

from pymtl3 import *
from pymtl3.stdlib.proc import SparseMemoryImage

from proj3.test.tinyrv2_encoding_test import mk_section
from proj3.tinyrv2_encoding           import assemble

from proj3.ubmark.proc_ubmark_vvadd_data import src0, src1, ref

c_vvadd_src0_ptr = 0x2000;
c_vvadd_src1_ptr = 0x3000;
c_vvadd_dest_ptr = 0x4000;

# Initial size for the unrolled benchmark. Keep small to start; raise by
# duplicating per-element blocks in gen_mem_image() below.
c_vvadd_size     = 100; # <= 100

class ubmark_vvadd_unopt:

  # verification function, argument is a bytearray

  @staticmethod
  def verify( memory ):

    is_pass      = True
    first_failed = -1

    for i in range(c_vvadd_size):
      x = struct.unpack('i', memory[c_vvadd_dest_ptr + i * 4 : c_vvadd_dest_ptr + (i+1) * 4] )[0]
      if not ( x == ref[i] ):
        is_pass     = False
        first_faild = i
        print( " [ failed ] dest[{i}]: {x} != ref[{i}]: {ref} ".format( i=i, x=x, ref=ref[i] ) )
        return False

    if is_pass:
      print( " [ passed ] vvadd-unopt" )
      return True

  @staticmethod
  def gen_mem_image():

    # ----------------------------------------------------------------
    # Prologue: load base pointers
    # ----------------------------------------------------------------

    text = """
    csrr  x2, mngr2proc < 0x2000   # src0 base
    csrr  x3, mngr2proc < 0x3000   # src1 base
    csrr  x4, mngr2proc < 0x4000   # dest base
"""

    # ----------------------------------------------------------------
    # Per-element block, fully unrolled.
    # Each block is independent of the others (different offsets,
    # different temporary regs), maximizing OoO opportunity.
    # ----------------------------------------------------------------
    # We rotate through a small pool of temporary registers so that
    # successive iterations do not serialize on the same architectural
    # register (renaming will give them different physical regs anyway,
    # but this also keeps the disassembly readable).

    tmp_pool = [6, 7, 8, 9, 10, 11, 12, 13]
    for i in range(c_vvadd_size):
      off  = i * 4
      ta   = tmp_pool[ (2*i)     % len(tmp_pool) ]
      tb   = tmp_pool[ (2*i + 1) % len(tmp_pool) ]
      text += f"""
    lw    x{ta}, {off}(x2)
    lw    x{tb}, {off}(x3)
    add   x{ta}, x{ta}, x{tb}
    sw    x{ta}, {off}(x4)
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

    src0_section = mk_section( ".data", c_vvadd_src0_ptr, src0 )
    src1_section = mk_section( ".data", c_vvadd_src1_ptr, src1 )

    mem_image.add_section( src0_section )
    mem_image.add_section( src1_section )

    return mem_image