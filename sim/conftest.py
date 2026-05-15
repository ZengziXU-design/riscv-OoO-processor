#=========================================================================
# conftest
#=========================================================================

import pytest
import random

@pytest.fixture(autouse=True)
def fix_randseed():
  """Set the random seed prior to each test case."""
  random.seed(0xdeadbeef)

#-------------------------------------------------------------------------
# --dump-xmsgs option
#-------------------------------------------------------------------------

def pytest_addoption( parser ):
  parser.addoption( "--dump-xmsgs", dest="dump_xmsgs", action="store_true",
                    default=False, help="dump xcel message transaction file" )

@pytest.fixture
def dump_xmsgs( request ):
  """Returns True if --dump-xmsgs was passed on the command line."""
  return request.config.getoption("dump_xmsgs")
