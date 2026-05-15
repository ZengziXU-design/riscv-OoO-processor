#========================================================================
# ubmark-chacha20-unrolled-highaddr: branch-less ChaCha20 block kernel
#========================================================================
# Python-generated benchmark version of the standalone chacha20 assembly.
#
# This version is intended for an OoO processor that does not support
# branches/jumps yet. The original assembly had two runtime loops:
#
#   1. outer_block: 4 ChaCha20 blocks
#   2. inner_round: 10 double-round iterations per block
#
# Both loops are fully unrolled here by Python when constructing the assembly
# text. The final assembled program contains no branch or jump instructions.
# Verification is done in Python by checking the destination memory.
#========================================================================

import struct

from pymtl3 import *
from pymtl3.stdlib.proc import SparseMemoryImage

from proj3.test.tinyrv2_encoding_test import mk_section
from proj3.tinyrv2_encoding           import assemble

# ----------------------------------------------------------------------
# Data
# ----------------------------------------------------------------------
#
# The fully-unrolled ChaCha20 program is much larger than simple ubmarks.
# Keep data well above the text region to avoid self-overwriting code through
# stores to dest.
#

c_chacha20_src_ptr  = 0x8000
c_chacha20_dest_ptr = 0x9000

# The standalone assembly used eval_size = 4 blocks, each block is 64 bytes
# or 16 32-bit words.

c_chacha20_nblocks  = 4
c_chacha20_nwords   = c_chacha20_nblocks * 16

# One input block from ubmark-chacha20.dat. The standalone assembly repeats
# this same 16-word block four times.

chacha20_src_block = [
  0x61707865, 0x3320646e, 0x79622d32, 0x6b206574,
  0x03020100, 0x07060504, 0x0b0a0908, 0x0f0e0d0c,
  0x13121110, 0x17161514, 0x1b1a1918, 0x1f1e1d1c,
  0x00000001, 0x09000000, 0x4a000000, 0x00000000,
]

chacha20_src = chacha20_src_block * c_chacha20_nblocks

# Expected output block from the standalone assembly's chacha_ref. It is also
# repeated four times.

chacha20_ref_block = [
  0xe4e7f110, 0x15593bd1, 0x1fdd0f50, 0xc47120a3,
  0xc7f4d1c7, 0x0368c033, 0x9aaa2204, 0x4e6cd4c3,
  0x466482d2, 0x09aa9f07, 0x05d7c214, 0xa2028bd9,
  0xd19c12b5, 0xb94e16de, 0xe883d0cb, 0x4e3c50a2,
]

chacha20_ref = chacha20_ref_block * c_chacha20_nblocks

#========================================================================
# ubmark_chacha20_unrolled
#========================================================================

class ubmark_chacha20_unrolled:

  # Verification function, argument is a bytearray from TestMemory instance.
  # Use unsigned comparison because ChaCha20 naturally produces 32-bit words
  # above 0x7fffffff.

  @staticmethod
  def verify( memory ):

    for i in range(c_chacha20_nwords):
      x = struct.unpack(
        '<I',
        memory[
          c_chacha20_dest_ptr + i * 4 :
          c_chacha20_dest_ptr + (i+1) * 4
        ]
      )[0]

      if x != chacha20_ref[i]:
        print(
          " [ failed ] dest[{i}]: 0x{x:08x} != ref[{i}]: 0x{ref:08x} ".format(
            i=i, x=x, ref=chacha20_ref[i]
          )
        )
        return False

    print( " [ passed ] chacha20-unrolled" )
    return True

  @staticmethod
  def gen_mem_image():

    # ----------------------------------------------------------------
    # Prologue: load fixed source/destination pointers.
    # ----------------------------------------------------------------
    # x11 = source base pointer
    # x19 = destination base pointer
    # ----------------------------------------------------------------

    text = """
    csrr  x11, mngr2proc < 0x8000   # chacha_src base
    csrr  x19, mngr2proc < 0x9000   # chacha_dest base
"""

    # ----------------------------------------------------------------
    # One ChaCha20 double-round body from the original inner_round loop.
    # This body is repeated 10 times per block by Python, so the generated
    # assembly has no runtime loop branch.
    # ----------------------------------------------------------------

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

    # ----------------------------------------------------------------
    # Generate four fully-unrolled blocks. The pointer updates from the
    # original assembly are kept, but the runtime outer branch is removed.
    # ----------------------------------------------------------------

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
    # Output sequence rewritten to use only positive offsets.
    # The original standalone assembly increments x11/x19 first and then
    # uses negative offsets such as -60(x19). That is functionally correct,
    # but it can expose bugs in S-type/I-type negative immediate handling in
    # incomplete OoO designs. Keeping the base pointers fixed until all 16
    # stores are done makes every memory immediate non-negative.
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

    # ----------------------------------------------------------------
    # Epilogue. Do not emit a stop-loop branch; the Python ubmark style uses
    # proc2mngr for completion and Python-side verification.
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

    # Safety check: make sure the generated assembly contains no branch/jump
    # instructions. This checks only actual instruction lines, not comments.

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
