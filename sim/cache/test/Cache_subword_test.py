#=========================================================================
# Cache_subword_test.py
#=========================================================================

import pytest

from pymtl3 import *

from cache.test.harness import run_test
from cache.test.CacheFL_subword_test import \
  ( test_case_table, test_case_table_random, cmp_wo_test_field )

from cache.Cache import Cache

@pytest.mark.parametrize( **test_case_table )
def test_subword( test_params, cmdline_opts ):
  run_test( Cache(), test_params, cmdline_opts )

@pytest.mark.parametrize( **test_case_table_random )
def test_subword_random( test_params, cmdline_opts ):
  run_test( Cache(), test_params, cmdline_opts, cmp_wo_test_field )

