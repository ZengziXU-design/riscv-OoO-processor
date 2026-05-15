#=========================================================================
# OoO_SingleCoreSysFL_test.py
#=========================================================================

import pytest

from pymtl3 import *

from proj3.test.harness_sys import asm_test
from proj3.test.harness_sys import run_score_test as run_test

from proj3.OoO_SingleCoreSysFL import OoO_SingleCoreSysFL

from proj3.test import inst_csr
from proj3.test import inst_add
from proj3.test import inst_mul
from proj3.test import inst_addi
from proj3.test import inst_lw
from proj3.test import inst_sw
from proj3.test import inst_sub
from proj3.test import inst_and
from proj3.test import inst_andi
from proj3.test import inst_or
from proj3.test import inst_xor
from proj3.test import inst_xori
from proj3.test import inst_slt
from proj3.test import inst_slti
from proj3.test import inst_sll
from proj3.test import inst_srl
from proj3.test import inst_srli
from proj3.test import inst_sra
from proj3.test import inst_slli
from proj3.test import inst_srai
from proj3.test import inst_ori
from proj3.test import inst_OoO

#-------------------------------------------------------------------------
# Tests
#-------------------------------------------------------------------------

@pytest.mark.usefixtures("cmdline_opts")
class Tests:

  @classmethod
  def setup_class( cls ):
    cls.SysType = OoO_SingleCoreSysFL

  #-----------------------------------------------------------------------
  # csr
  #-----------------------------------------------------------------------

  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_csr.gen_basic_test      ),
    asm_test( inst_csr.gen_bypass_test     ),
    asm_test( inst_csr.gen_value_test      ),
    asm_test( inst_csr.gen_random_test     ),
    asm_test( inst_csr.gen_core_stats_test ),
  ])
  def test_csr( s, name, test ):
    run_test( s.SysType, test, cmdline_opts=s.__class__.cmdline_opts )

  def test_csr_delays( s ):
    run_test( s.SysType, inst_csr.gen_random_test, delays=True,
              cmdline_opts=s.__class__.cmdline_opts )

  #-----------------------------------------------------------------------
  # add
  #-----------------------------------------------------------------------

  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_add.gen_basic_test     ),
    asm_test( inst_add.gen_dest_dep_test  ),
    asm_test( inst_add.gen_src0_dep_test  ),
    asm_test( inst_add.gen_src1_dep_test  ),
    asm_test( inst_add.gen_srcs_dep_test  ),
    asm_test( inst_add.gen_srcs_dest_test ),
    asm_test( inst_add.gen_value_test     ),
    asm_test( inst_add.gen_random_test    ),
  ])
  def test_add( s, name, test ):
    run_test( s.SysType, test, cmdline_opts=s.__class__.cmdline_opts )

  def test_add_delays( s ):
    run_test( s.SysType, inst_add.gen_random_test, delays=True,
              cmdline_opts=s.__class__.cmdline_opts )

  #-----------------------------------------------------------------------
  # sub
  #-----------------------------------------------------------------------

  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_sub.gen_basic_test     ),
    asm_test( inst_sub.gen_dest_dep_test  ),
    asm_test( inst_sub.gen_src0_dep_test  ),
    asm_test( inst_sub.gen_src1_dep_test  ),
    asm_test( inst_sub.gen_srcs_dep_test  ),
    asm_test( inst_sub.gen_srcs_dest_test ),
    asm_test( inst_sub.gen_value_test     ),
    asm_test( inst_sub.gen_random_test    ),
  ])
  def test_sub( s, name, test ):
    run_test( s.SysType, test, cmdline_opts=s.__class__.cmdline_opts )

  def test_sub_delays( s ):
    run_test( s.SysType, inst_sub.gen_random_test, delays=True,
              cmdline_opts=s.__class__.cmdline_opts )

  #-----------------------------------------------------------------------
  # mul
  #-----------------------------------------------------------------------
  
  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_mul.gen_basic_test     ),
    
    #''' LAB TASK ''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    # Add more rows to the test case table to test more complicated
    # scenarios.
    #'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    asm_test( inst_mul.gen_dest_dep_test   ),
    asm_test( inst_mul.gen_src0_dep_test   ),
    asm_test( inst_mul.gen_src1_dep_test   ),
    asm_test( inst_mul.gen_srcs_dep_test   ),
    asm_test( inst_mul.gen_srcs_dest_test  ),
    asm_test( inst_mul.gen_value_test      ),
    asm_test( inst_mul.gen_random_test     ),
  ])
  def test_mul( s, name, test ):
    run_test( s.SysType, test, cmdline_opts=s.__class__.cmdline_opts )

  #'''' LAB TASK '''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  # random stall and delay
  #'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

  def test_mul_delays( s ):
    run_test( s.SysType, inst_mul.gen_random_test, delays=True,
              cmdline_opts=s.__class__.cmdline_opts )

  #-----------------------------------------------------------------------
  # and
  #-----------------------------------------------------------------------

  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_and.gen_basic_test     ),
    asm_test( inst_and.gen_dest_dep_test  ),
    asm_test( inst_and.gen_src0_dep_test  ),
    asm_test( inst_and.gen_src1_dep_test  ),
    asm_test( inst_and.gen_srcs_dep_test  ),
    asm_test( inst_and.gen_srcs_dest_test ),
    asm_test( inst_and.gen_value_test     ),
    asm_test( inst_and.gen_random_test    ),
  ])
  def test_and( s, name, test ):
    run_test( s.SysType, test, cmdline_opts=s.__class__.cmdline_opts )

  def test_and_delays( s ):
    run_test( s.SysType, inst_and.gen_random_test, delays=True,
              cmdline_opts=s.__class__.cmdline_opts )

  #-----------------------------------------------------------------------
  # or
  #-----------------------------------------------------------------------

  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_or.gen_basic_test     ),
    asm_test( inst_or.gen_dest_dep_test  ),
    asm_test( inst_or.gen_src0_dep_test  ),
    asm_test( inst_or.gen_src1_dep_test  ),
    asm_test( inst_or.gen_srcs_dep_test  ),
    asm_test( inst_or.gen_srcs_dest_test ),
    asm_test( inst_or.gen_value_test     ),
    asm_test( inst_or.gen_random_test    ),
  ])
  def test_or( s, name, test ):
    run_test( s.SysType, test, cmdline_opts=s.__class__.cmdline_opts )

  def test_or_delays( s ):
    run_test( s.SysType, inst_or.gen_random_test, delays=True,
              cmdline_opts=s.__class__.cmdline_opts )

  #-----------------------------------------------------------------------
  # xor
  #-----------------------------------------------------------------------

  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_xor.gen_basic_test     ),
    asm_test( inst_xor.gen_dest_dep_test  ),
    asm_test( inst_xor.gen_src0_dep_test  ),
    asm_test( inst_xor.gen_src1_dep_test  ),
    asm_test( inst_xor.gen_srcs_dep_test  ),
    asm_test( inst_xor.gen_srcs_dest_test ),
    asm_test( inst_xor.gen_value_test     ),
    asm_test( inst_xor.gen_random_test    ),
  ])
  def test_xor( s, name, test ):
    run_test( s.SysType, test, cmdline_opts=s.__class__.cmdline_opts )

  def test_xor_delays( s ):
    run_test( s.SysType, inst_xor.gen_random_test, delays=True,
              cmdline_opts=s.__class__.cmdline_opts )

  #-----------------------------------------------------------------------
  # slt
  #-----------------------------------------------------------------------

  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_slt.gen_basic_test     ),
    asm_test( inst_slt.gen_dest_dep_test  ),
    asm_test( inst_slt.gen_src0_dep_test  ),
    asm_test( inst_slt.gen_src1_dep_test  ),
    asm_test( inst_slt.gen_srcs_dep_test  ),
    asm_test( inst_slt.gen_srcs_dest_test ),
    asm_test( inst_slt.gen_value_test     ),
    asm_test( inst_slt.gen_random_test    ),
  ])
  def test_slt( s, name, test ):
    run_test( s.SysType, test, cmdline_opts=s.__class__.cmdline_opts )

  def test_slt_delays( s ):
    run_test( s.SysType, inst_slt.gen_random_test, delays=True,
              cmdline_opts=s.__class__.cmdline_opts )

  #-----------------------------------------------------------------------
  # sll
  #-----------------------------------------------------------------------

  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_sll.gen_basic_test     ),
    asm_test( inst_sll.gen_dest_dep_test  ),
    asm_test( inst_sll.gen_src0_dep_test  ),
    asm_test( inst_sll.gen_src1_dep_test  ),
    asm_test( inst_sll.gen_srcs_dep_test  ),
    asm_test( inst_sll.gen_srcs_dest_test ),
    asm_test( inst_sll.gen_value_test     ),
    asm_test( inst_sll.gen_random_test    ),
  ])
  def test_sll( s, name, test ):
    run_test( s.SysType, test, cmdline_opts=s.__class__.cmdline_opts )

  def test_sll_delays( s ):
    run_test( s.SysType, inst_sll.gen_random_test, delays=True,
              cmdline_opts=s.__class__.cmdline_opts )

  #-----------------------------------------------------------------------
  # srl
  #-----------------------------------------------------------------------

  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_srl.gen_basic_test     ),
    asm_test( inst_srl.gen_dest_dep_test  ),
    asm_test( inst_srl.gen_src0_dep_test  ),
    asm_test( inst_srl.gen_src1_dep_test  ),
    asm_test( inst_srl.gen_srcs_dep_test  ),
    asm_test( inst_srl.gen_srcs_dest_test ),
    asm_test( inst_srl.gen_value_test     ),
    asm_test( inst_srl.gen_random_test    ),
  ])
  def test_srl( s, name, test ):
    run_test( s.SysType, test, cmdline_opts=s.__class__.cmdline_opts )

  def test_srl_delays( s ):
    run_test( s.SysType, inst_srl.gen_random_test, delays=True,
              cmdline_opts=s.__class__.cmdline_opts )

  #-----------------------------------------------------------------------
  # sra
  #-----------------------------------------------------------------------

  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_sra.gen_basic_test     ),
    asm_test( inst_sra.gen_dest_dep_test  ),
    asm_test( inst_sra.gen_src0_dep_test  ),
    asm_test( inst_sra.gen_src1_dep_test  ),
    asm_test( inst_sra.gen_srcs_dep_test  ),
    asm_test( inst_sra.gen_srcs_dest_test ),
    asm_test( inst_sra.gen_value_test     ),
    asm_test( inst_sra.gen_random_test    ),
  ])
  def test_sra( s, name, test ):
    run_test( s.SysType, test, cmdline_opts=s.__class__.cmdline_opts )

  def test_sra_delays( s ):
    run_test( s.SysType, inst_sra.gen_random_test, delays=True,
              cmdline_opts=s.__class__.cmdline_opts )
    
  #-----------------------------------------------------------------------
  # addi
  #-----------------------------------------------------------------------

  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_addi.gen_basic_test     ) ,
    
    #''' LAB TASK ''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    # Add more rows to the test case table to test more complicated
    # scenarios.
    #'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    asm_test( inst_addi.gen_dest_dep_test  ) ,
    asm_test( inst_addi.gen_src_dep_test   ) ,
    asm_test( inst_addi.gen_srcs_dest_test ) ,
    asm_test( inst_addi.gen_value_test     ) ,
    asm_test( inst_addi.gen_random_test    ) ,
  ])
  def test_addi( s, name, test ):
    run_test( s.SysType, test, cmdline_opts=s.__class__.cmdline_opts )

  #''' LAB TASK ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  # random stall and delay
  #'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  def test_addi_delays( s ):
    run_test( s.SysType, inst_addi.gen_random_test, delays=True,
              cmdline_opts=s.__class__.cmdline_opts )

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
    run_test( s.SysType, test, cmdline_opts=s.__class__.cmdline_opts )  
  def test_andi_delays( s ):
    run_test( s.SysType, inst_andi.gen_random_test, delays=True,
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
    run_test( s.SysType, test, cmdline_opts=s.__class__.cmdline_opts )

  def test_ori_delays( s ):
    run_test( s.SysType, inst_ori.gen_random_test, delays=True,
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
    run_test( s.SysType, test, cmdline_opts=s.__class__.cmdline_opts )
  def test_xori_delays( s ):
    run_test( s.SysType, inst_xori.gen_random_test, delays=True,
              cmdline_opts=s.__class__.cmdline_opts )

  #-----------------------------------------------------------------------
  # slti
  #-----------------------------------------------------------------------

  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_slti.gen_basic_test     ) ,
    asm_test( inst_slti.gen_dest_dep_test  ) ,
    asm_test( inst_slti.gen_src_dep_test   ) ,
    asm_test( inst_slti.gen_srcs_dest_test ) ,
    asm_test( inst_slti.gen_value_test     ) ,
    asm_test( inst_slti.gen_random_test    ) ,
  ])
  def test_slti( s, name, test ):
    run_test( s.SysType, test, cmdline_opts=s.__class__.cmdline_opts )

  def test_slti_delays( s ):
    run_test( s.SysType, inst_slti.gen_random_test, delays=True,
              cmdline_opts=s.__class__.cmdline_opts )

  #-----------------------------------------------------------------------
  # slli
  #-----------------------------------------------------------------------

  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_slli.gen_basic_test     ) ,
    asm_test( inst_slli.gen_dest_dep_test  ) ,
    asm_test( inst_slli.gen_src_dep_test   ) ,
    asm_test( inst_slli.gen_srcs_dest_test ) ,
    asm_test( inst_slli.gen_value_test     ) ,
    asm_test( inst_slli.gen_random_test    ) ,
  ])
  def test_slli( s, name, test ):
    run_test( s.SysType, test, cmdline_opts=s.__class__.cmdline_opts )

  def test_slli_delays( s ):
    run_test( s.SysType, inst_slli.gen_random_test, delays=True,
              cmdline_opts=s.__class__.cmdline_opts )
    
  #-----------------------------------------------------------------------
  # srli
  #-----------------------------------------------------------------------
  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_srli.gen_basic_test     ) ,
    asm_test( inst_srli.gen_dest_dep_test  ) ,
    asm_test( inst_srli.gen_src_dep_test   ) ,
    asm_test( inst_srli.gen_srcs_dest_test ) ,
    asm_test( inst_srli.gen_value_test     ) ,
    asm_test( inst_srli.gen_random_test    ) ,
  ])
  def test_srli( s, name, test ):
    run_test( s.SysType, test, cmdline_opts=s.__class__.cmdline_opts )
    
  def test_srli_delays( s ):
    run_test( s.SysType, inst_srli.gen_random_test, delays=True,
              cmdline_opts=s.__class__.cmdline_opts ) 

  #-----------------------------------------------------------------------
  # srai
  #-----------------------------------------------------------------------

  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_srai.gen_basic_test     ) ,
    asm_test( inst_srai.gen_dest_dep_test  ) ,
    asm_test( inst_srai.gen_src_dep_test   ) ,
    asm_test( inst_srai.gen_srcs_dest_test ) ,
    asm_test( inst_srai.gen_value_test     ) ,
    asm_test( inst_srai.gen_random_test    ) ,
  ])
  def test_srai( s, name, test ):
    run_test( s.SysType, test, cmdline_opts=s.__class__.cmdline_opts )

  def test_srai_delays( s ):
    run_test( s.SysType, inst_srai.gen_random_test, delays=True,
              cmdline_opts=s.__class__.cmdline_opts )

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
    run_test( s.SysType, test, cmdline_opts=s.__class__.cmdline_opts )

  def test_lw_delays( s ):
    run_test( s.SysType, inst_lw.gen_random_test, delays=True,
              cmdline_opts=s.__class__.cmdline_opts )

  #-----------------------------------------------------------------------
  # sw
  #-----------------------------------------------------------------------

  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_sw.gen_basic_test     ),
    
    #''' LAB TASK ''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    # Add more rows to the test case table to test more complicated
    # scenarios.
    #'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    asm_test( inst_sw.gen_dest_dep_test  ) ,
    asm_test( inst_sw.gen_base_dep_test  ) ,
    asm_test( inst_sw.gen_srcs_dest_test ) ,
    asm_test( inst_sw.gen_addr_test      ) ,
    asm_test( inst_sw.gen_random_test    ) ,
  ])
  def test_sw( s, name, test ):
    run_test( s.SysType, test, cmdline_opts=s.__class__.cmdline_opts )

  #''' LAB TASK ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  # random stall and delay
  #'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  def test_sw_delays( s ):
    run_test( s.SysType, inst_sw.gen_random_test, delays=True,
              cmdline_opts=s.__class__.cmdline_opts )




  #-----------------------------------------------------------------------
  # inst_OoO
  #-----------------------------------------------------------------------

  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_OoO.gen_ooo_overtake_test     ),
    asm_test( inst_OoO.gen_ooo_waw_test ) ,
    asm_test( inst_OoO.gen_ooo_war_test     ) ,
    asm_test( inst_OoO.gen_ooo_waw_war_complex_test    ) ,
    asm_test( inst_OoO.gen_ooo_rob_full_test ) ,
    asm_test( inst_OoO.gen_ooo_iq_full_test  ) ,
    asm_test( inst_OoO.gen_ooo_freelist_wrap_around_test  ) ,
    asm_test( inst_OoO.gen_ooo_back_to_back_bypass_test ) ,
    asm_test( inst_OoO.gen_ooo_x0_penetration_test ) ,
    asm_test( inst_OoO.gen_ooo_mem_bypass_arith_test ) ,
    asm_test( inst_OoO.gen_ooo_arith_bypass_mem_test ) ,
    asm_test( inst_OoO.gen_ooo_mem_order_test ) ,
    asm_test( inst_OoO.gen_ooo_lw_dependent_test ) ,
    asm_test( inst_OoO.gen_ooo_mem_inflight_test ) ,
    asm_test( inst_OoO.gen_ooo_tri_wb_test ) ,
  ])
  def test_OoO( s, name, test ):
    run_test( s.SysType, test, cmdline_opts=s.__class__.cmdline_opts )
    