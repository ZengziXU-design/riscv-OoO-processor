#=========================================================================
# Proc_csr_test.py
#=========================================================================
# It is as simple as inheriting from FL tests and change the ProcType.

from proj3.ProcOoO import ProcOoO
from proj3.test.ProcFL_csr_test import Tests as ProcFL_csr_TestsBaseClass

#-------------------------------------------------------------------------
# Tests
#-------------------------------------------------------------------------

class Tests( ProcFL_csr_TestsBaseClass ):

  @classmethod
  def setup_class( cls ):
    cls.ProcType = ProcOoO

