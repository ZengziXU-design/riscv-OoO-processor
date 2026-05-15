#=========================================================================
# OoO_SingleCoreSys_test.py
#=========================================================================
# It is as simple as inheriting from FL tests and change the SysType.

from proj3.OoO_SingleCoreSys import OoO_SingleCoreSys
from proj3.test.OoO_SingleCoreSysFL_test import Tests as OoO_SingleCoreSysFL_TestsBaseClass

#-------------------------------------------------------------------------
# Tests
#-------------------------------------------------------------------------

class Tests( OoO_SingleCoreSysFL_TestsBaseClass ):

  @classmethod
  def setup_class( cls ):
    cls.SysType = OoO_SingleCoreSys

