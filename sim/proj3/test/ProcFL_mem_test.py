#=========================================================================
# ProcFL_mem_test.py
#=========================================================================
# We group all our test cases into a class so that we can easily reuse
# these test cases in our RTL tests. We can simply inherit from this test
# class, overload the setup_class method, and set the ProcType
# appropriately.

import pytest

from pymtl3 import *
from proj3.test.harness import asm_test, run_test
from proj3.ProcFL import ProcFL

from proj3.test import inst_lw
from proj3.test import inst_sw

#-------------------------------------------------------------------------
# Tests
#-------------------------------------------------------------------------

@pytest.mark.usefixtures("cmdline_opts")
class Tests:

  @classmethod
  def setup_class( cls ):
    cls.ProcType = ProcFL

  #-----------------------------------------------------------------------
  # lw
  #-----------------------------------------------------------------------

  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_lw.gen_basic_test     ) ,
    asm_test( inst_lw.gen_dest_dep_test  ) ,
    asm_test( inst_lw.gen_base_dep_test  ) ,
    asm_test( inst_lw.gen_srcs_dest_test ) ,
    asm_test( inst_lw.gen_addr_test      ) ,
    asm_test( inst_lw.gen_random_test    ) ,
  ])
  def test_lw( s, name, test ):
    run_test( s.ProcType, test, cmdline_opts=s.__class__.cmdline_opts )

  def test_lw_delays( s ):
    run_test( s.ProcType, inst_lw.gen_random_test, delays=True,
              cmdline_opts=s.__class__.cmdline_opts )

  #-----------------------------------------------------------------------
  # sw
  #-----------------------------------------------------------------------

  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_sw.gen_basic_test     ),

    # ''' LAB TASK '''''''''''''''''''''''''''''''''''''''''''''''''''''''
    # Add more rows to the test case table to test more complicated
    # scenarios.
    # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\/

    asm_test( inst_sw.gen_dest_dep_test     ),
    asm_test( inst_sw.gen_base_dep_test     ),
    asm_test( inst_sw.gen_src_dep_test      ),
    asm_test( inst_sw.gen_srcs_dep_test     ),
    asm_test( inst_sw.gen_srcs_dest_test    ),
    asm_test( inst_sw.gen_simple_sw_lw_test ),
    asm_test( inst_sw.gen_addr_test         ),
    asm_test( inst_sw.gen_random_test       ),

    #'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''/\
  ])
  def test_sw( s, name, test ):
    run_test( s.ProcType, test, cmdline_opts=s.__class__.cmdline_opts )

  # ''' LAB TASK '''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  # random stall and delay
  # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\/

  def test_sw_delays( s ):
    run_test( s.ProcType, inst_sw.gen_random_test, delays=True,
              cmdline_opts=s.__class__.cmdline_opts )

  #'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''/\

