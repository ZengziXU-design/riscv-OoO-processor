#=========================================================================
# ProcBase_OoO_test.py
#=========================================================================
# Runs the inst_OoO scenario suite against the in-order ProcBase.
# These tests are pure correctness tests (proc2mngr value checks), so they
# pass on any conforming RV2 implementation. They will not exercise OoO
# microarchitectural state on Base, but the cycle counts they produce are
# directly comparable to ProcOoO running the same suite.

from proj3.ProcBase import ProcBase
from proj3.test.ProcFL_OoO_test import Tests as ProcFL_OoO_TestsBaseClass

#-------------------------------------------------------------------------
# Tests
#-------------------------------------------------------------------------

class Tests( ProcFL_OoO_TestsBaseClass ):

  @classmethod
  def setup_class( cls ):
    cls.ProcType = ProcBase
