#=========================================================================
# NullXcel_test
#=========================================================================

import pytest

from pymtl3.stdlib.test_utils import run_sim

from proj3.test.NullXcelFL_test import TestHarness, test_case_table
from proj3.NullXcel import NullXcel

@pytest.mark.parametrize( **test_case_table )
def test( cmdline_opts, test_params ):
  th = TestHarness( NullXcel() )

  th.set_param("top.src.construct",
    msgs=test_params.msgs[::2],
    initial_delay=test_params.src_delay+3,
    interval_delay=test_params.src_delay )

  th.set_param("top.sink.construct",
    msgs=test_params.msgs[1::2],
    initial_delay=test_params.sink_delay+3,
    interval_delay=test_params.sink_delay )

  run_sim( th, cmdline_opts, duts=['xcel'] )
