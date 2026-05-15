#=========================================================================
# ProcFL_super_random_test.py
#=========================================================================
# Random instruction-mix tests (super_random.py). ProcFL checks
# architectural results; Proc_super_random_test.py runs RTL.
#
# Per-category random tests are split into many small batches so a
# failing case points to a tiny program instead of a giant one.

import pytest

from pymtl3 import *
from proj3.test.harness import asm_test, run_test
from proj3.ProcFL import ProcFL

from proj3.test import super_random as rnd

#-------------------------------------------------------------------------
# Build the parametrize table
#-------------------------------------------------------------------------

_random_cases = (
    [ asm_test( f ) for f in rnd.random_rr_tests()     ]
  + [ asm_test( f ) for f in rnd.random_rimm_tests()   ]
  + [ asm_test( f ) for f in rnd.random_lw_tests()     ]
  + [ asm_test( f ) for f in rnd.random_sw_tests()     ]
  # + [ asm_test( f ) for f in rnd.random_branch_tests() ]
  # + [ asm_test( f ) for f in rnd.random_jal_tests()    ]
  # + [ asm_test( f ) for f in rnd.random_jalr_tests()   ]
  # + [ asm_test( f ) for f in rnd.random_all_tests()    ]
)

#-------------------------------------------------------------------------
# Tests
#-------------------------------------------------------------------------

@pytest.mark.usefixtures("cmdline_opts")
class Tests:

  @classmethod
  def setup_class( cls ):
    cls.ProcType = ProcFL

  @pytest.mark.parametrize( "name,test", _random_cases )
  def test_super_random( s, name, test ):
    run_test( s.ProcType, test, cmdline_opts=s.__class__.cmdline_opts )
