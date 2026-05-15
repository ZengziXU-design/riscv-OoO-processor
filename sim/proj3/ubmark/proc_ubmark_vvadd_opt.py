#========================================================================
# ubmark-vvadd-opt: vector-vector addition kernel (UNROLLED, no branch)
#========================================================================
# Branch-less variant of vvadd-opt for evaluating an out-of-order
# processor that does not yet support branches/jumps.
#
# Original kernel: 4-way unrolled per loop iteration, ~21 instructions
# per iteration including the backward branch and pointer bumps.
#
# In the branch-less variant we remove the backward branch and also the
# pointer-bump addis: every block uses a hard-coded offset so the address
# generator can run fully in parallel.
#
# Each block processes 4 elements (4 loads from src0, 4 loads from src1,
# 4 adds, 4 stores), and the whole kernel is just a sequence of these
# blocks. Raise c_vvadd_size in multiples of 4 (or copy more blocks).
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

# Initial size for the unrolled benchmark. Must be a multiple of 4
# because the unrolled body processes 4 elements at a time.
c_vvadd_size     = 100; # <= 100  && c_vvadd_size % 4 == 0

class ubmark_vvadd_opt:

  # verification function, argument is a bytearray from TestMemory instance

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
      print( " [ passed ] vvadd-opt" )
      return True

  @staticmethod
  def gen_mem_image():

    assert c_vvadd_size % 4 == 0, "vvadd-opt size must be a multiple of 4"

    # ----------------------------------------------------------------
    # Prologue: load base pointers
    # ----------------------------------------------------------------

    text = """
    csrr  x2, mngr2proc < 0x2000   # src0 base
    csrr  x3, mngr2proc < 0x3000   # src1 base
    csrr  x4, mngr2proc < 0x4000   # dest base
"""

    # ----------------------------------------------------------------
    # 4-way unrolled blocks, fully unrolled (no backward branch).
    # Each block uses hard-coded byte offsets keyed off the block index.
    # ----------------------------------------------------------------

    num_blocks = c_vvadd_size // 4
    for blk in range(num_blocks):
      base_off = blk * 16   # 4 elements * 4 bytes
      o0 = base_off
      o1 = base_off + 4
      o2 = base_off + 8
      o3 = base_off + 12
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