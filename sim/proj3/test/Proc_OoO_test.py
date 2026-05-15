#=========================================================================
# Proc_OoO_test.py
#=========================================================================

from proj3.ProcOoO import ProcOoO 
from proj3.test.ProcFL_OoO_test import Tests as ProcFL_OoO_TestsBaseClass

#-------------------------------------------------------------------------
# Tests
#-------------------------------------------------------------------------

class Tests( ProcFL_OoO_TestsBaseClass ):

  @classmethod
  def setup_class( cls ):
    cls.ProcType = ProcOoO