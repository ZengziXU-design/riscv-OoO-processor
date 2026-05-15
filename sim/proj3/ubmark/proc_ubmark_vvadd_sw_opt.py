#========================================================================
# ubmark-vvadd-sw-opt: software-pipelined vector-vector add kernel
#========================================================================
# Branch-less Python-generated variant of vvadd_sw_opt.S for evaluating an
# out-of-order processor that does not yet support branches/jumps.
#
# Equivalent to:
#
#   void vvadd( int *dest, int *src0, int *src1, int size ) {
#     for ( int i = 0; i < size; i++ )
#       dest[i] = src0[i] + src1[i];
#   }
#
# The original standalone assembly is already mostly unrolled, but it still
# contains a branch for the odd-element drain path and a final stop loop. This
# Python ubmark fixes the size at 32 elements, fully emits only the even-size
# path, and performs verification in Python instead of in-program branches.
#
# The generated TinyRV2 assembly has no branch/jump instructions. Its timed
# kernel intentionally follows the older vvadd_sw_opt.S software-pipelined
# ordering, including the pointer updates before stores and negative offsets.
#========================================================================

import struct

from pymtl3 import *
from pymtl3.stdlib.proc import SparseMemoryImage

from proj3.test.tinyrv2_encoding_test import mk_section
from proj3.tinyrv2_encoding           import assemble

# ----------------------------------------------------------------------
# Data
# ----------------------------------------------------------------------

c_vvadd_sw_opt_src0_ptr = 0x2000
c_vvadd_sw_opt_src1_ptr = 0x3000
c_vvadd_sw_opt_dest_ptr = 0x4000

# The provided vvadd_sw_opt.S data section contains exactly 32 elements.
c_vvadd_sw_opt_size     = 32

src0 = [ i + 1 for i in range(c_vvadd_sw_opt_size) ]
src1 = [ 100 * (i + 1) for i in range(c_vvadd_sw_opt_size) ]

ref = [ src0[i] + src1[i] for i in range(c_vvadd_sw_opt_size) ]

#========================================================================
# ubmark_vvadd_sw_opt
#========================================================================

class ubmark_vvadd_sw_opt:

  # verification function, argument is a bytearray from TestMemory instance

  @staticmethod
  def verify( memory ):

    for i in range(c_vvadd_sw_opt_size):
      x = struct.unpack(
        'i',
        memory[
          c_vvadd_sw_opt_dest_ptr + i * 4 :
          c_vvadd_sw_opt_dest_ptr + (i+1) * 4
        ]
      )[0]

      if x != ref[i]:
        print(
          " [ failed ] dest[{i}]: {x} != ref[{i}]: {ref} ".format(
            i=i, x=x, ref=ref[i]
          )
        )
        return False

    print( " [ passed ] vvadd-sw-opt" )
    return True

  @staticmethod
  def gen_mem_image():

    # ----------------------------------------------------------------
    # Register mapping, following vvadd_sw_opt.S
    # ----------------------------------------------------------------
    # x10 = dest_ptr
    # x11 = src0_ptr
    # x12 = src1_ptr
    #
    # Bank A:
    #   x5  = a0_val
    #   x6  = b0_val
    #   x7  = a1_val
    #   x28 = b1_val
    #
    # Bank B:
    #   x14 = c0_val
    #   x15 = d0_val
    #   x16 = c1_val
    #   x17 = d1_val
    # ----------------------------------------------------------------

    text = """
    csrr  x10, mngr2proc < 0x4000   # dest base
    csrr  x11, mngr2proc < 0x2000   # src0 base
    csrr  x12, mngr2proc < 0x3000   # src1 base
"""

    # ----------------------------------------------------------------
    # Preload first pair into register bank A.
    # ----------------------------------------------------------------
    # This mirrors the standalone assembly exactly:
    #   a0 = src0[0], b0 = src1[0]
    #   src pointers advance by two words
    #   a1/b1 are then loaded through -4 offsets.
    # ----------------------------------------------------------------

    text += """
    # ---- preload pair 0 into bank A ----
    lw    x5,  0(x11)              # a0 = src0[0]
    addi  x11, x11, 8              # src0_ptr += 2 words
    lw    x6,  0(x12)              # b0 = src1[0]
    addi  x12, x12, 8              # src1_ptr += 2 words
    lw    x7,  -4(x11)             # a1 = src0[1]
    lw    x28, -4(x12)             # b1 = src1[1]
"""

    def emit_compute_a_load_b( pair_idx ):
      # Current loaded pair is pair_idx in bank A; next pair is pair_idx+1 in bank B.
      elem0 = 2 * pair_idx
      elem1 = elem0 + 1
      next_pair = pair_idx + 1
      next0 = 2 * next_pair
      next1 = next0 + 1
      return f"""
    addi  x10, x10, 8              # dest_ptr += 2 words

    # ---- pair {pair_idx}: compute/store bank A elements {elem0},{elem1}; load bank B elements {next0},{next1} ----
    lw    x14, 0(x11)              # c0 = src0[{next0}]
    add   x5,  x5,  x6             # a0 = a0 + b0
    lw    x15, 0(x12)              # d0 = src1[{next0}]
    add   x7,  x7,  x28            # a1 = a1 + b1
    lw    x16, 4(x11)              # c1 = src0[{next1}]
    addi  x11, x11, 8              # src0_ptr += 2 words
    sw    x5,  -8(x10)             # dest[{elem0}] = a0
    addi  x12, x12, 8              # src1_ptr += 2 words
    lw    x17, -4(x12)             # d1 = src1[{next1}]
    sw    x7,  -4(x10)             # dest[{elem1}] = a1
"""

    def emit_compute_b_load_a( pair_idx ):
      # Current loaded pair is pair_idx in bank B; next pair is pair_idx+1 in bank A.
      elem0 = 2 * pair_idx
      elem1 = elem0 + 1
      next_pair = pair_idx + 1
      next0 = 2 * next_pair
      next1 = next0 + 1
      return f"""
    addi  x10, x10, 8              # dest_ptr += 2 words

    # ---- pair {pair_idx}: compute/store bank B elements {elem0},{elem1}; load bank A elements {next0},{next1} ----
    lw    x5,  0(x11)              # a0 = src0[{next0}]
    add   x14, x14, x15            # c0 = c0 + d0
    lw    x6,  0(x12)              # b0 = src1[{next0}]
    add   x16, x16, x17            # c1 = c1 + d1
    lw    x7,  4(x11)              # a1 = src0[{next1}]
    addi  x11, x11, 8              # src0_ptr += 2 words
    sw    x14, -8(x10)             # dest[{elem0}] = c0
    addi  x12, x12, 8              # src1_ptr += 2 words
    lw    x28, -4(x12)             # b1 = src1[{next1}]
    sw    x16, -4(x10)             # dest[{elem1}] = c1
"""

    # ----------------------------------------------------------------
    # Fully-unrolled software-pipelined body.
    # ----------------------------------------------------------------
    # There are 16 pairs total. Pair 0 is preloaded. For pairs 0..14,
    # compute/store the current bank while loading the next pair into the
    # other bank. Pair 15 is then drained without the original odd-element
    # branch path.
    # ----------------------------------------------------------------

    for pair_idx in range((c_vvadd_sw_opt_size // 2) - 1):
      if pair_idx % 2 == 0:
        text += emit_compute_a_load_b( pair_idx )
      else:
        text += emit_compute_b_load_a( pair_idx )

    # Drain final pair 15, which is in bank B because pair 14 loaded bank B.

    text += """
    # ---- drain final bank B pair 15 elements 30,31 ----
    add   x14, x14, x15            # c0 = c0 + d0
    add   x16, x16, x17            # c1 = c1 + d1
    sw    x14, 0(x10)              # dest[30] = c0
    sw    x16, 4(x10)              # dest[31] = c1
    addi  x10, x10, 8              # dest_ptr += 2 words
"""

    # ----------------------------------------------------------------
    # Epilogue
    # ----------------------------------------------------------------
    # No branch-based odd path, no in-program verification loop, and no
    # final infinite branch. proc-sim verifies the destination memory through
    # the Python verify() method.
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

    src0_section = mk_section( ".data", c_vvadd_sw_opt_src0_ptr, src0 )
    src1_section = mk_section( ".data", c_vvadd_sw_opt_src1_ptr, src1 )
    dest_section = mk_section( ".data", c_vvadd_sw_opt_dest_ptr, [0] * c_vvadd_sw_opt_size )

    mem_image.add_section( src0_section )
    mem_image.add_section( src1_section )
    mem_image.add_section( dest_section )

    return mem_image


# Backward-compatible aliases for common ubmark naming styles.
ubmark_vvadd_sw_pipelining = ubmark_vvadd_sw_opt
ubmark_vvadd_sw_opt_unrolled = ubmark_vvadd_sw_opt
