#=========================================================================
# Proc_csr_test.py
#=========================================================================
# We group all our test cases into a class so that we can easily reuse
# these test cases in our RTL tests. We can simply inherit from this test
# class, overload the setup_class method, and set the ProcType
# appropriately.

import pytest

from pymtl3 import *
from proj3.test.harness import asm_test, run_test
from proj3.ProcOoO import ProcOoO

from proj3.test import inst_csr

#-------------------------------------------------------------------------
# Tests
#-------------------------------------------------------------------------

@pytest.mark.usefixtures("cmdline_opts")
class Tests:

  @classmethod
  def setup_class( cls ):
    cls.ProcType = ProcOoO

  #-------------------------------------------------------------------------
  # csr
  #-------------------------------------------------------------------------

  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_csr.gen_basic_test      ),
    asm_test( inst_csr.gen_bypass_test     ),
    asm_test( inst_csr.gen_value_test      ),
    asm_test( inst_csr.gen_random_test     ),
    asm_test( inst_csr.gen_core_stats_test ),
  ])
  def test_csr( s, name, test ):
    run_test( s.ProcType, test, cmdline_opts=s.__class__.cmdline_opts )

  def test_csr_delays( s ):
    run_test( s.ProcType, inst_csr.gen_random_test, delays=True,
              cmdline_opts=s.__class__.cmdline_opts )

