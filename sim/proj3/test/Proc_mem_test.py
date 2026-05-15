#=========================================================================
# Proc_mem_test.py
#=========================================================================
# It is as simple as inheriting from FL tests and change the ProcType.

from proj3.ProcOoO import ProcOoO
from proj3.test.ProcFL_mem_test import Tests as ProcFL_mem_TestsBaseClass

#-------------------------------------------------------------------------
# Tests
#-------------------------------------------------------------------------

class Tests( ProcFL_mem_TestsBaseClass ):

  @classmethod
  def setup_class( cls ):
    cls.ProcType = ProcOoO

