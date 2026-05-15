#=========================================================================
# mem_sim_test
#=========================================================================
# Make sure that mem-sim works.

import pytest
import os

from subprocess import check_call, CalledProcessError

impls  = [ "fl", "rtl" ]
inputs = [ "loop1", "loop2", "loop3" ]

test_cases = []
for input_ in inputs:
  for impl in impls:
    test_cases.append([ impl, input_ ])

@pytest.mark.parametrize( "impl,input_", test_cases )
def test( impl, input_, cmdline_opts ):

  # Get path to simulator script

  test_dir = os.path.dirname( os.path.abspath( __file__ ) )
  sim_dir  = os.path.dirname( test_dir )
  sim      = sim_dir + os.path.sep + 'mem-sim'

  # Command

  cmd = [ sim, "--impl", impl, "--input", input_ ]

  # Display simulator command line

  print("")
  print("Simulator command line:", ' '.join(cmd))

  # Run the simulator

  try:
    check_call(cmd)
  except CalledProcessError as e:
    raise Exception( "Error running simulator!" )

