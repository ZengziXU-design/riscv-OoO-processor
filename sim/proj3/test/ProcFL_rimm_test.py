#=========================================================================
# ProcFL_rimm_test.py
#=========================================================================
# We group all our test cases into a class so that we can easily reuse
# these test cases in our RTL tests. We can simply inherit from this test
# class, overload the setup_class method, and set the ProcType
# appropriately.

import pytest

from pymtl3 import *
from proj3.test.harness import asm_test, run_test
from proj3.ProcFL import ProcFL

from proj3.test import inst_addi
from proj3.test import inst_andi
from proj3.test import inst_ori
from proj3.test import inst_xori
from proj3.test import inst_slti
from proj3.test import inst_sltiu
from proj3.test import inst_srai
from proj3.test import inst_srli
from proj3.test import inst_slli

#-------------------------------------------------------------------------
# Tests
#-------------------------------------------------------------------------

@pytest.mark.usefixtures("cmdline_opts")
class Tests:

  @classmethod
  def setup_class( cls ):
    cls.ProcType = ProcFL

  #-----------------------------------------------------------------------
  # addi
  #-----------------------------------------------------------------------

  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_addi.gen_basic_test     ) ,

    # ''' LAB TASK '''''''''''''''''''''''''''''''''''''''''''''''''''''''
    # Add more rows to the test case table to test more complicated
    # scenarios.
    # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\/

    asm_test( inst_addi.gen_dest_dep_test  ) ,
    asm_test( inst_addi.gen_src_dep_test   ) ,
    asm_test( inst_addi.gen_srcs_dest_test ) ,
    asm_test( inst_addi.gen_value_test     ) ,
    asm_test( inst_addi.gen_random_test    ) ,
    #'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''/\
  ])
  def test_addi( s, name, test ):
    run_test( s.ProcType, test, cmdline_opts=s.__class__.cmdline_opts )

  # ''' LAB TASK '''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  # random stall and delay
  # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\/

  def test_addi_delays( s ):
    run_test( s.ProcType, inst_addi.gen_random_test, delays=True,
              cmdline_opts=s.__class__.cmdline_opts )

  #'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''/\

  #-----------------------------------------------------------------------
  # andi
  #-----------------------------------------------------------------------

  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_andi.gen_basic_test     ) ,
    asm_test( inst_andi.gen_dest_dep_test  ) ,
    asm_test( inst_andi.gen_src_dep_test   ) ,
    asm_test( inst_andi.gen_srcs_dest_test ) ,
    asm_test( inst_andi.gen_value_test     ) ,
    asm_test( inst_andi.gen_random_test    ) ,
  ])
  def test_andi( s, name, test ):
    run_test( s.ProcType, test, cmdline_opts=s.__class__.cmdline_opts )

  def test_andi_delays( s ):
    run_test( s.ProcType, inst_andi.gen_random_test, delays=True,
              cmdline_opts=s.__class__.cmdline_opts )

  #-----------------------------------------------------------------------
  # ori
  #-----------------------------------------------------------------------

  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_ori.gen_basic_test     ) ,
    asm_test( inst_ori.gen_dest_dep_test  ) ,
    asm_test( inst_ori.gen_src_dep_test   ) ,
    asm_test( inst_ori.gen_srcs_dest_test ) ,
    asm_test( inst_ori.gen_value_test     ) ,
    asm_test( inst_ori.gen_random_test    ) ,
  ])
  def test_ori( s, name, test ):
    run_test( s.ProcType, test, cmdline_opts=s.__class__.cmdline_opts )

  def test_ori_delays( s ):
    run_test( s.ProcType, inst_ori.gen_random_test, delays=True,
              cmdline_opts=s.__class__.cmdline_opts )

  #-----------------------------------------------------------------------
  # xori
  #-----------------------------------------------------------------------

  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_xori.gen_basic_test     ) ,
    asm_test( inst_xori.gen_dest_dep_test  ) ,
    asm_test( inst_xori.gen_src_dep_test   ) ,
    asm_test( inst_xori.gen_srcs_dest_test ) ,
    asm_test( inst_xori.gen_value_test     ) ,
    asm_test( inst_xori.gen_random_test    ) ,
  ])
  def test_xori( s, name, test ):
    run_test( s.ProcType, test, cmdline_opts=s.__class__.cmdline_opts )

  def test_xori_delays( s ):
    run_test( s.ProcType, inst_xori.gen_random_test, delays=True,
              cmdline_opts=s.__class__.cmdline_opts )

  #-----------------------------------------------------------------------
  # slti
  #-----------------------------------------------------------------------

  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_slti.gen_basic_test     ) ,

    # ''' LAB TASK '''''''''''''''''''''''''''''''''''''''''''''''''''''''
    # Add more rows to the test case table to test more complicated
    # scenarios.
    # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\/

    asm_test( inst_slti.gen_dest_dep_test  ) ,
    asm_test( inst_slti.gen_src_dep_test   ) ,
    asm_test( inst_slti.gen_srcs_dest_test ) ,
    asm_test( inst_slti.gen_value_test     ) ,
    asm_test( inst_slti.gen_random_test    ) ,
    #'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''/\
  ])
  def test_slti( s, name, test ):
    run_test( s.ProcType, test, cmdline_opts=s.__class__.cmdline_opts )

  # ''' LAB TASK '''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  # random stall and delay
  # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\/

  def test_slti_delays( s ):
    run_test( s.ProcType, inst_slti.gen_random_test, delays=True,
              cmdline_opts=s.__class__.cmdline_opts )

  #'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''/\

  #-----------------------------------------------------------------------
  # sltiu
  #-----------------------------------------------------------------------

  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_sltiu.gen_basic_test     ) ,

    # ''' LAB TASK '''''''''''''''''''''''''''''''''''''''''''''''''''''''
    # Add more rows to the test case table to test more complicated
    # scenarios.
    # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\/

    asm_test( inst_sltiu.gen_dest_dep_test  ) ,
    asm_test( inst_sltiu.gen_src_dep_test   ) ,
    asm_test( inst_sltiu.gen_srcs_dest_test ) ,
    asm_test( inst_sltiu.gen_value_test     ) ,
    asm_test( inst_sltiu.gen_random_test    ) ,
    #'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''/\
  ])
  def test_sltiu( s, name, test ):
    run_test( s.ProcType, test, cmdline_opts=s.__class__.cmdline_opts )

  # ''' LAB TASK '''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  # random stall and delay
  # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\/

  def test_sltiu_delays( s ):
    run_test( s.ProcType, inst_sltiu.gen_random_test, delays=True,
              cmdline_opts=s.__class__.cmdline_opts )

  #'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''/\

  #-----------------------------------------------------------------------
  # srai
  #-----------------------------------------------------------------------

  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_srai.gen_basic_test     ) ,

    # ''' LAB TASK '''''''''''''''''''''''''''''''''''''''''''''''''''''''
    # Add more rows to the test case table to test more complicated
    # scenarios.
    # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\/

    asm_test( inst_srai.gen_dest_dep_test  ) ,
    asm_test( inst_srai.gen_src_dep_test   ) ,
    asm_test( inst_srai.gen_srcs_dest_test ) ,
    asm_test( inst_srai.gen_value_test     ) ,
    asm_test( inst_srai.gen_random_test    ) ,
    #'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''/\
  ])
  def test_srai( s, name, test ):
    run_test( s.ProcType, test, cmdline_opts=s.__class__.cmdline_opts )

  # ''' LAB TASK '''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  # random stall and delay
  # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\/

  def test_srai_delays( s ):
    run_test( s.ProcType, inst_srai.gen_random_test, delays=True,
              cmdline_opts=s.__class__.cmdline_opts )

  #'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''/\

  #-----------------------------------------------------------------------
  # srli
  #-----------------------------------------------------------------------

  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_srli.gen_basic_test     ) ,

    # ''' LAB TASK '''''''''''''''''''''''''''''''''''''''''''''''''''''''
    # Add more rows to the test case table to test more complicated
    # scenarios.
    # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\/

    asm_test( inst_srli.gen_dest_dep_test  ) ,
    asm_test( inst_srli.gen_src_dep_test   ) ,
    asm_test( inst_srli.gen_srcs_dest_test ) ,
    asm_test( inst_srli.gen_value_test     ) ,
    asm_test( inst_srli.gen_random_test    ) ,
    #'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''/\
  ])
  def test_srli( s, name, test ):
    run_test( s.ProcType, test, cmdline_opts=s.__class__.cmdline_opts )

  # ''' LAB TASK '''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  # random stall and delay
  # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\/

  def test_srli_delays( s ):
    run_test( s.ProcType, inst_srli.gen_random_test, delays=True,
              cmdline_opts=s.__class__.cmdline_opts )

  #'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''/\

  #-----------------------------------------------------------------------
  # slli
  #-----------------------------------------------------------------------

  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_slli.gen_basic_test     ) ,

    # ''' LAB TASK '''''''''''''''''''''''''''''''''''''''''''''''''''''''
    # Add more rows to the test case table to test more complicated
    # scenarios.
    # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\/

    asm_test( inst_slli.gen_dest_dep_test  ) ,
    asm_test( inst_slli.gen_src_dep_test   ) ,
    asm_test( inst_slli.gen_srcs_dest_test ) ,
    asm_test( inst_slli.gen_value_test     ) ,
    asm_test( inst_slli.gen_random_test    ) ,
    #'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''/\
  ])
  def test_slli( s, name, test ):
    run_test( s.ProcType, test, cmdline_opts=s.__class__.cmdline_opts )

  # ''' LAB TASK '''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  # random stall and delay
  # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\/

  def test_slli_delays( s ):
    run_test( s.ProcType, inst_slli.gen_random_test, delays=True,
              cmdline_opts=s.__class__.cmdline_opts )

  #'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''/\
