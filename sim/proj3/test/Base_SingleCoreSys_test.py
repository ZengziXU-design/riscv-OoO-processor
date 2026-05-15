#=========================================================================
# Base_SingleCoreSys_test.py
#=========================================================================
# RTL test for the in-order Base SingleCoreSys. Reuses the FL system test
# class (OoO_SingleCoreSysFL_test.Tests) since the FL reference (ProcFL +
# caches) is the same regardless of which RTL processor we are testing.
# We only swap the `SysType` to point at our Base_SingleCoreSys placeholder.
#
# Note: the FL test class also runs the inst_OoO suite. Those tests are
# correctness tests written as plain TinyRV2 assembly that compares
# proc2mngr outputs against expected values, so they pass on any correct
# in-order processor as well -- they just don't exercise OoO-specific
# microarchitecture. If you want to skip them on Base, override
# `test_OoO` in this class (see commented stub at the bottom).

from proj3.Base_SingleCoreSys import Base_SingleCoreSys
from proj3.test.OoO_SingleCoreSysFL_test import Tests as OoO_SingleCoreSysFL_TestsBaseClass

#-------------------------------------------------------------------------
# Tests
#-------------------------------------------------------------------------

class Tests( OoO_SingleCoreSysFL_TestsBaseClass ):

  @classmethod
  def setup_class( cls ):
    cls.SysType = Base_SingleCoreSys

  # --- Optional: skip the inst_OoO suite on the in-order baseline ---
  #
  # import pytest
  # @pytest.mark.skip(reason="inst_OoO suite is not the focus for Base")
  # def test_OoO( s, name, test ):
  #   pass