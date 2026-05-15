#========================================================================
# sys-ubmark-chacha20-unrolled: ChaCha20 block kernel with system-level self-check
#========================================================================
#
# This benchmark is intended for proc/cache system simulation.
#
# Difference from proc_ubmark_chacha20_unrolled:
#   - proc_ubmark_chacha20_unrolled verifies the result by directly reading
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

from proj3.ubmark.proc_ubmark_chacha20_unrolled import (
  chacha20_src, chacha20_ref,
  c_chacha20_src_ptr,
  c_chacha20_dest_ptr,
  c_chacha20_nblocks,
  c_chacha20_nwords,
)

#-------------------------------------------------------------------------
# Helper
#-------------------------------------------------------------------------

def to_hex32( value ):
  return value & 0xffffffff

#-------------------------------------------------------------------------
# Benchmark
#-------------------------------------------------------------------------

class sys_ubmark_chacha20_unrolled:

  @staticmethod
  def verify( memory ):
    print( " [ passed ] sys-chacha20-unrolled self-check" )
    return True

  @staticmethod
  def gen_mem_image():

    #---------------------------------------------------------------------
    # Prologue: load fixed source/destination pointers (mirrors proc version)
    #---------------------------------------------------------------------

    text = """
    csrr  x11, mngr2proc < 0x8000   # chacha_src base
    csrr  x19, mngr2proc < 0x9000   # chacha_dest base
"""

    #---------------------------------------------------------------------
    # One ChaCha20 double-round body. Duplicated verbatim from
    # proc_ubmark_chacha20_unrolled.gen_mem_image() (inner_round is a local
    # there, not importable).
    #---------------------------------------------------------------------

    inner_round = """
    add   x30, x30, x10
    add   x31, x31, x12
    add   x9,  x6,  x9
    add   x8,  x17, x8
    xor   x13, x30, x13
    xor   x16, x31, x16
    xor   x14, x9,  x14
    xor   x15, x8,  x15
    srli  x23, x13, 0x10
    srli  x24, x15, 0x10
    srli  x25, x14, 0x10
    srli  x22, x16, 0x10
    slli  x13, x13, 0x10
    slli  x15, x15, 0x10
    slli  x14, x14, 0x10
    slli  x16, x16, 0x10
    add   x13, x13, x23
    add   x15, x15, x24
    add   x14, x14, x25
    add   x16, x16, x22
    add   x18, x13, x18
    add   x5,  x15, x5
    add   x7,  x14, x7
    add   x29, x16, x29
    xor   x10, x18, x10
    xor   x17, x5,  x17
    xor   x6,  x7,  x6
    xor   x12, x29, x12
    srli  x23, x10, 0x14
    srli  x24, x17, 0x14
    srli  x25, x6,  0x14
    srli  x22, x12, 0x14
    slli  x10, x10, 0x0c
    slli  x17, x17, 0x0c
    slli  x6,  x6,  0x0c
    slli  x12, x12, 0x0c
    add   x10, x10, x23
    add   x17, x17, x24
    add   x6,  x6,  x25
    add   x12, x12, x22
    add   x30, x30, x10
    add   x8,  x8,  x17
    add   x9,  x9,  x6
    add   x31, x31, x12
    xor   x13, x13, x30
    xor   x15, x15, x8
    xor   x14, x14, x9
    xor   x16, x16, x31
    srli  x23, x13, 0x18
    srli  x24, x14, 0x18
    srli  x25, x16, 0x18
    srli  x22, x15, 0x18
    slli  x13, x13, 0x08
    slli  x14, x14, 0x08
    slli  x16, x16, 0x08
    slli  x15, x15, 0x08
    add   x13, x13, x23
    add   x14, x14, x24
    add   x16, x16, x25
    add   x15, x15, x22
    add   x18, x18, x13
    add   x7,  x7,  x14
    add   x29, x29, x16
    add   x5,  x5,  x15
    xor   x10, x10, x18
    xor   x6,  x6,  x7
    xor   x12, x12, x29
    xor   x17, x17, x5
    srli  x23, x10, 0x19
    srli  x24, x12, 0x19
    srli  x25, x6,  0x19
    srli  x22, x17, 0x19
    slli  x10, x10, 0x07
    slli  x12, x12, 0x07
    slli  x6,  x6,  0x07
    slli  x17, x17, 0x07
    add   x10, x10, x23
    add   x12, x12, x24
    add   x6,  x6,  x25
    add   x17, x17, x22
    add   x8,  x10, x8
    add   x30, x30, x12
    add   x31, x31, x6
    add   x9,  x9,  x17
    xor   x14, x14, x8
    xor   x15, x15, x30
    xor   x13, x13, x31
    xor   x16, x16, x9
    srli  x23, x14, 0x10
    srli  x24, x15, 0x10
    srli  x25, x13, 0x10
    srli  x22, x16, 0x10
    slli  x14, x14, 0x10
    slli  x15, x15, 0x10
    slli  x13, x13, 0x10
    slli  x16, x16, 0x10
    add   x14, x14, x23
    add   x15, x15, x24
    add   x13, x13, x25
    add   x16, x16, x22
    add   x29, x29, x14
    add   x7,  x7,  x15
    add   x5,  x5,  x13
    add   x18, x18, x16
    xor   x10, x10, x29
    xor   x12, x12, x7
    xor   x6,  x6,  x5
    xor   x17, x17, x18
    srli  x23, x10, 0x14
    srli  x24, x12, 0x14
    srli  x25, x6,  0x14
    srli  x22, x17, 0x14
    slli  x10, x10, 0x0c
    slli  x12, x12, 0x0c
    slli  x6,  x6,  0x0c
    slli  x17, x17, 0x0c
    add   x10, x10, x23
    add   x12, x12, x24
    add   x6,  x6,  x25
    add   x17, x17, x22
    add   x8,  x8,  x10
    add   x30, x30, x12
    add   x31, x31, x6
    add   x9,  x9,  x17
    xor   x14, x14, x8
    xor   x15, x15, x30
    xor   x13, x13, x31
    xor   x16, x16, x9
    srli  x23, x14, 0x18
    srli  x24, x15, 0x18
    srli  x25, x13, 0x18
    srli  x22, x16, 0x18
    slli  x14, x14, 0x08
    slli  x15, x15, 0x08
    slli  x13, x13, 0x08
    slli  x16, x16, 0x08
    add   x14, x14, x23
    add   x15, x15, x24
    add   x13, x13, x25
    add   x16, x16, x22
    add   x29, x29, x14
    add   x7,  x7,  x15
    add   x5,  x5,  x13
    add   x18, x18, x16
    xor   x10, x10, x29
    xor   x12, x12, x7
    xor   x6,  x6,  x5
    xor   x17, x17, x18
    srli  x23, x10, 0x19
    srli  x24, x12, 0x19
    srli  x25, x6,  0x19
    srli  x22, x17, 0x19
    slli  x10, x10, 0x07
    slli  x12, x12, 0x07
    slli  x6,  x6,  0x07
    slli  x17, x17, 0x07
    addi  x28, x28, -1
    add   x10, x10, x23
    add   x12, x12, x24
    add   x6,  x6,  x25
    add   x17, x17, x22
"""

    #---------------------------------------------------------------------
    # Generate fully-unrolled blocks (mirrors proc version)
    #---------------------------------------------------------------------

    for blk in range(c_chacha20_nblocks):
      text += f"""
    # ---- chacha20 block {blk} ----
    lw    x20, 0(x11)
    lw    x31, 4(x11)
    lw    x9,  8(x11)
    lw    x8,  12(x11)
    lw    x10, 16(x11)
    lw    x12, 20(x11)
    lw    x6,  24(x11)
    lw    x17, 28(x11)
    lw    x18, 32(x11)
    lw    x29, 36(x11)
    lw    x7,  40(x11)
    lw    x5,  44(x11)
    lw    x13, 48(x11)
    lw    x16, 52(x11)
    lw    x14, 56(x11)
    lw    x15, 60(x11)
    addi  x30, x20, 0
    addi  x28, x0,  10
    addi  x0,  x0,  0
"""

      for rnd in range(10):
        text += f"""
    # ---- block {blk}, double round {rnd} ----
"""
        text += inner_round

      text += """
    add   x30, x30, x20
    sw    x30, 0(x19)

    lw    x28, 4(x11)
    add   x28, x28, x31
    sw    x28, 4(x19)

    lw    x28, 8(x11)
    add   x28, x28, x9
    sw    x28, 8(x19)

    lw    x28, 12(x11)
    add   x28, x28, x8
    sw    x28, 12(x19)

    lw    x28, 16(x11)
    add   x10, x28, x10
    sw    x10, 16(x19)

    lw    x10, 20(x11)
    add   x12, x10, x12
    sw    x12, 20(x19)

    lw    x12, 24(x11)
    add   x12, x12, x6
    sw    x12, 24(x19)

    lw    x12, 28(x11)
    add   x12, x12, x17
    sw    x12, 28(x19)

    lw    x12, 32(x11)
    add   x12, x12, x18
    sw    x12, 32(x19)

    lw    x12, 36(x11)
    add   x12, x12, x29
    sw    x12, 36(x19)

    lw    x12, 40(x11)
    add   x12, x12, x7
    sw    x12, 40(x19)

    lw    x12, 44(x11)
    add   x12, x12, x5
    sw    x12, 44(x19)

    lw    x12, 48(x11)
    add   x13, x12, x13
    sw    x13, 48(x19)

    lw    x13, 52(x11)
    add   x13, x13, x16
    sw    x13, 52(x19)

    lw    x13, 56(x11)
    add   x14, x13, x14
    sw    x14, 56(x19)

    lw    x14, 60(x11)
    add   x15, x14, x15
    sw    x15, 60(x19)

    addi  x11, x11, 64
    addi  x19, x19, 64
"""

    #---------------------------------------------------------------------
    # System-level self-check
    #---------------------------------------------------------------------
    # The kernel above incremented x19, so reload a fresh dest base.
    #---------------------------------------------------------------------

    text += """
    # ---- system-level self-check through dcache ----
    csrr  x4, mngr2proc < 0x9000
"""

    for i in range(c_chacha20_nwords):

      off = i * 4
      exp = to_hex32( chacha20_ref[i] )

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

    # Safety check: no branch/jump in generated assembly.

    branch_or_jump_ops = { 'beq', 'bne', 'blt', 'bge', 'bltu', 'bgeu', 'jal', 'jalr' }
    for line in text.splitlines():
      stripped = line.strip()
      if not stripped or stripped.startswith('#'):
        continue
      op = stripped.split()[0]
      assert op not in branch_or_jump_ops, 'branch/jump found in generated assembly: ' + stripped

    mem_image = assemble( text )

    src_section = mk_section( ".data", c_chacha20_src_ptr, chacha20_src )
    mem_image.add_section( src_section )

    return mem_image
