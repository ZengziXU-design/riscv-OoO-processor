#=========================================================================
# ReadDataUnit_test
#=========================================================================

from pymtl3 import *
from pymtl3.stdlib.mem        import MemMsgType
from pymtl3.stdlib.test_utils import run_test_vector_sim

from cache.ReadDataUnit import ReadDataUnit

read  = MemMsgType.READ
write = MemMsgType.WRITE
init  = MemMsgType.WRITE_INIT

#-------------------------------------------------------------------------
# test_len1
#-------------------------------------------------------------------------

def test_len1( cmdline_opts ):
  run_test_vector_sim( ReadDataUnit(), [
    ('in_                                    type_  len offset out*'                                 ),
    [ 0x00000000_00000000_00000000_00000000, read,  1,  0,     0x00000000_00000000_00000000_00000000 ],

    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  1,  0,     0x00000000_00000000_00000000_00000002 ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  1,  1,     0x00000000_00000000_00000000_000000ef ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  1,  2,     0x00000000_00000000_00000000_000000cd ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  1,  3,     0x00000000_00000000_00000000_000000ab ],

    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  1,  4,     0x00000000_00000000_00000000_00000000 ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  1,  5,     0x00000000_00000000_00000000_000000ee ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  1,  6,     0x00000000_00000000_00000000_000000ff ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  1,  7,     0x00000000_00000000_00000000_000000c0 ],

    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  1,  8,     0x00000000_00000000_00000000_000000ac ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  1,  9,     0x00000000_00000000_00000000_000000ef ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  1,  10,    0x00000000_00000000_00000000_000000fe ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  1,  11,    0x00000000_00000000_00000000_000000ca ],

    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  1,  12,    0x00000000_00000000_00000000_000000ef ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  1,  13,    0x00000000_00000000_00000000_000000be ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  1,  14,    0x00000000_00000000_00000000_000000ad ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  1,  15,    0x00000000_00000000_00000000_000000de ],

  ], cmdline_opts )

#-------------------------------------------------------------------------
# test_len2
#-------------------------------------------------------------------------

def test_len2( cmdline_opts ):
  run_test_vector_sim( ReadDataUnit(), [
    ('in_                                    type_  len offset out*'                                 ),
    [ 0x00000000_00000000_00000000_00000000, read,  2,  0,     0x00000000_00000000_00000000_00000000 ],

    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  2,  0,     0x00000000_00000000_00000000_0000ef02 ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  2,  1,     0x00000000_00000000_00000000_0000cdef ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  2,  2,     0x00000000_00000000_00000000_0000abcd ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  2,  3,     0x00000000_00000000_00000000_000000ab ],

    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  2,  4,     0x00000000_00000000_00000000_0000ee00 ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  2,  5,     0x00000000_00000000_00000000_0000ffee ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  2,  6,     0x00000000_00000000_00000000_0000c0ff ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  2,  7,     0x00000000_00000000_00000000_0000acc0 ],

    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  2,  8,     0x00000000_00000000_00000000_0000efac ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  2,  9,     0x00000000_00000000_00000000_0000feef ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  2,  10,    0x00000000_00000000_00000000_0000cafe ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  2,  11,    0x00000000_00000000_00000000_0000efca ],

    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  2,  12,    0x00000000_00000000_00000000_0000beef ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  2,  13,    0x00000000_00000000_00000000_0000adbe ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  2,  14,    0x00000000_00000000_00000000_0000dead ],

  ], cmdline_opts )

#-------------------------------------------------------------------------
# test_len4
#-------------------------------------------------------------------------

def test_len4( cmdline_opts ):
  run_test_vector_sim( ReadDataUnit(), [
    ('in_                                    type_  len offset out*'                                 ),
    [ 0x00000000_00000000_00000000_00000000, read,  4,  0,     0x00000000_00000000_00000000_00000000 ],

    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  4,  0,     0x00000000_00000000_00000000_abcdef02 ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  4,  1,     0x00000000_00000000_00000000_00abcdef ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  4,  2,     0x00000000_00000000_00000000_ee00abcd ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  4,  3,     0x00000000_00000000_00000000_ffee00ab ],

    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  4,  4,     0x00000000_00000000_00000000_c0ffee00 ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  4,  5,     0x00000000_00000000_00000000_acc0ffee ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  4,  6,     0x00000000_00000000_00000000_efacc0ff ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  4,  7,     0x00000000_00000000_00000000_feefacc0 ],

    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  4,  8,     0x00000000_00000000_00000000_cafeefac ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  4,  9,     0x00000000_00000000_00000000_efcafeef ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  4,  10,    0x00000000_00000000_00000000_beefcafe ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  4,  11,    0x00000000_00000000_00000000_adbeefca ],

    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  4,  12,    0x00000000_00000000_00000000_deadbeef ],

  ], cmdline_opts )

#-------------------------------------------------------------------------
# test_len8
#-------------------------------------------------------------------------

def test_len8( cmdline_opts ):
  run_test_vector_sim( ReadDataUnit(), [
    ('in_                                    type_  len offset out*'                                 ),
    [ 0x00000000_00000000_00000000_00000000, read,  8,  0,     0x00000000_00000000_00000000_00000000 ],

    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  8,  0,     0x00000000_00000000_c0ffee00_abcdef02 ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  8,  1,     0x00000000_00000000_acc0ffee_00abcdef ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  8,  2,     0x00000000_00000000_efacc0ff_ee00abcd ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  8,  3,     0x00000000_00000000_feefacc0_ffee00ab ],

    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  8,  4,     0x00000000_00000000_cafeefac_c0ffee00 ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  8,  5,     0x00000000_00000000_efcafeef_acc0ffee ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  8,  6,     0x00000000_00000000_beefcafe_efacc0ff ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  8,  7,     0x00000000_00000000_adbeefca_feefacc0 ],

    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  8,  8,     0x00000000_00000000_deadbeef_cafeefac ],

  ], cmdline_opts )

#-------------------------------------------------------------------------
# test_len0 (16 bytes)
#-------------------------------------------------------------------------

def test_len16( cmdline_opts ):
  run_test_vector_sim( ReadDataUnit(), [
    ('in_                                    type_  len offset out*'                                 ),
    [ 0x00000000_00000000_00000000_00000000, read,  0,  0,     0x00000000_00000000_00000000_00000000 ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, read,  0,  0,     0xdeadbeef_cafeefac_c0ffee00_abcdef02 ],
  ], cmdline_opts )

#-------------------------------------------------------------------------
# test_type
#-------------------------------------------------------------------------

def test_type( cmdline_opts ):
  run_test_vector_sim( ReadDataUnit(), [
    ('in_                                    type_  len offset out*'                                 ),
    [ 0x00000000_00000000_00000000_00000000, read,  4,  0,     0x00000000_00000000_00000000_00000000 ],

    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, write, 4,  0,     0x00000000_00000000_00000000_00000000 ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, write, 4,  4,     0x00000000_00000000_00000000_00000000 ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, init,  4,  8,     0x00000000_00000000_00000000_00000000 ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, write, 4,  12,    0x00000000_00000000_00000000_00000000 ],

    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, init,  1,  8,     0x00000000_00000000_00000000_00000000 ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, write, 1,  9,     0x00000000_00000000_00000000_00000000 ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, write, 1,  10,    0x00000000_00000000_00000000_00000000 ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, init,  1,  11,    0x00000000_00000000_00000000_00000000 ],

    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, write, 2,  8,     0x00000000_00000000_00000000_00000000 ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, init,  2,  9,     0x00000000_00000000_00000000_00000000 ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, write, 2,  10,    0x00000000_00000000_00000000_00000000 ],
    [ 0xdeadbeef_cafeefac_c0ffee00_abcdef02, init,  2,  11,    0x00000000_00000000_00000000_00000000 ],

  ], cmdline_opts )

