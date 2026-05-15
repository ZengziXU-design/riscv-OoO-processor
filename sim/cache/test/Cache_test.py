#=========================================================================
# Cache_test.py
#=========================================================================

import pytest

from pymtl3 import *

from cache.test.harness      import run_test
from cache.test.CacheFL_test import \
  ( test_case_table_generic, test_case_table_random,
    test_case_table_sassoc, cmp_wo_test_field )

from cache.Cache import Cache

#-------------------------------------------------------------------------
# Generic tests for both baseline and alternative design
#-------------------------------------------------------------------------

@pytest.mark.parametrize( **test_case_table_generic )
def test_generic( test_params, cmdline_opts ):
  run_test( Cache(), test_params, cmdline_opts )

#-------------------------------------------------------------------------
# Random tests for both baseline and alternative design
#-------------------------------------------------------------------------

@pytest.mark.parametrize( **test_case_table_random )
def test_random( test_params, cmdline_opts ):
  run_test( Cache(), test_params, cmdline_opts, cmp_wo_test_field )

#-------------------------------------------------------------------------
# Tests for just alternative design
#-------------------------------------------------------------------------

@pytest.mark.parametrize( **test_case_table_sassoc )
def test_sassoc( test_params, cmdline_opts ):
  run_test( Cache(), test_params, cmdline_opts )

