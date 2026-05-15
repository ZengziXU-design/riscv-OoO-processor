#=========================================================================
# Cache_rand_test.py
#=========================================================================

import pytest

from pymtl3 import *

from cache.test.harness import run_test
from cache.test.CacheFL_rand_test import test_case_table_sassoc_rand

from cache.Cache import Cache

#-------------------------------------------------------------------------
# Enhanced random testing
#-------------------------------------------------------------------------

@pytest.mark.parametrize( **test_case_table_sassoc_rand )
def test_sassoc_rand( test_params, cmdline_opts ):
  run_test( Cache(), test_params, cmdline_opts )

