#=========================================================================
# Proc_super_random_test.py
#=========================================================================
# Dual-issue RTL runs the same programs as ProcFL_super_random_test.

from proj3.ProcOoO import ProcOoO
from proj3.test.ProcFL_super_random_test import Tests as ProcFL_super_random_TestsBaseClass

#-------------------------------------------------------------------------
# Tests
#-------------------------------------------------------------------------

class Tests( ProcFL_super_random_TestsBaseClass ):

  @classmethod
  def setup_class( cls ):
    cls.ProcType = ProcOoO
