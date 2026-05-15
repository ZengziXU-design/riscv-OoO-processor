#=========================================================================
# ProcFL_OoO_test.py
#=========================================================================
# Regression harness for the micro-architectural OoO scenario tests
# defined in inst_OoO.py.
#
# Tests are grouped by the same sections used in inst_OoO.py so that the
# two files stay in sync when new scenarios are added.

import pytest

from pymtl3 import *
from proj3.test.harness import asm_test, run_test
from proj3.ProcFL import ProcFL

from proj3.test import inst_OoO

@pytest.mark.usefixtures("cmdline_opts")
class Tests:

  @classmethod
  def setup_class( cls ):
    cls.ProcType = ProcFL

  @pytest.mark.parametrize(
    "name,test",
    [
      # ---------------------------------------------------------------
      # Section 1: Out-of-order dispatch behavior
      # ---------------------------------------------------------------
      asm_test( inst_OoO.gen_ooo_overtake_test ),
      asm_test( inst_OoO.gen_ooo_extended_overtake_test ),

      # ---------------------------------------------------------------
      # Section 2: Hazard handling via register renaming
      # ---------------------------------------------------------------
      asm_test( inst_OoO.gen_ooo_waw_test ),
      asm_test( inst_OoO.gen_ooo_war_test ),
      asm_test( inst_OoO.gen_ooo_waw_war_complex_test ),

      # ---------------------------------------------------------------
      # Section 3: Resource exhaustion stalls
      # ---------------------------------------------------------------
      asm_test( inst_OoO.gen_ooo_rob_full_test ),
      asm_test( inst_OoO.gen_ooo_iq_full_test ),
      asm_test( inst_OoO.gen_ooo_freelist_wrap_around_test ),

      # ---------------------------------------------------------------
      # Section 4: Writeback path
      # ---------------------------------------------------------------
      asm_test( inst_OoO.gen_ooo_tri_wb_test ),
      asm_test( inst_OoO.gen_ooo_back_to_back_bypass_test ),

      # ---------------------------------------------------------------
      # Section 5: Boundary cases
      # ---------------------------------------------------------------
      asm_test( inst_OoO.gen_ooo_x0_penetration_test ),

      # ---------------------------------------------------------------
      # Section 6: Memory pipeline (Stage 1: in-order lw/sw)
      # ---------------------------------------------------------------
      asm_test( inst_OoO.gen_ooo_mem_bypass_arith_test ),
      asm_test( inst_OoO.gen_ooo_arith_bypass_mem_test ),
      asm_test( inst_OoO.gen_ooo_mem_order_test ),
      asm_test( inst_OoO.gen_ooo_lw_dependent_test ),
      asm_test( inst_OoO.gen_ooo_lw_base_dep_test ),
      asm_test( inst_OoO.gen_ooo_sw_data_dep_test ),
      asm_test( inst_OoO.gen_ooo_mem_inflight_test ),
    ],
    ids=[
      # Section 1
      "ooo_overtake",
      "ooo_extended_overtake",
      # Section 2
      "ooo_waw",
      "ooo_war",
      "ooo_waw_war_complex",
      # Section 3
      "ooo_rob_full",
      "ooo_iq_full",
      "ooo_freelist_wrap_around",
      # Section 4
      "ooo_tri_wb",
      "ooo_back_to_back_bypass",
      # Section 5
      "ooo_x0_penetration",
      # Section 6
      "ooo_mem_bypass_arith",
      "ooo_arith_bypass_mem",
      "ooo_mem_order",
      "ooo_lw_dependent",
      "ooo_lw_base_dep",
      "ooo_sw_data_dep",
      "ooo_mem_inflight",
    ]
  )
  def test_ooo_behavior( s, name, test ):
    run_test( s.ProcType, test, cmdline_opts=s.__class__.cmdline_opts )

  #-----------------------------------------------------------------------
  # Random-delay variants (Section 6 mem tests)
  #-----------------------------------------------------------------------
  # The mem tests are the most useful to also run with random dmem
  # delays, since dmem stalls directly exercise mem-pipe backpressure
  # and the busy_M / mem_issue_rdy handshake. Other sections are
  # deterministic and gain little from delay variants.

  def test_mem_inflight_delays( s ):
    run_test( s.ProcType, inst_OoO.gen_ooo_mem_inflight_test, delays=True,
              cmdline_opts=s.__class__.cmdline_opts )

  def test_mem_order_delays( s ):
    run_test( s.ProcType, inst_OoO.gen_ooo_mem_order_test, delays=True,
              cmdline_opts=s.__class__.cmdline_opts )

  def test_lw_dependent_delays( s ):
    run_test( s.ProcType, inst_OoO.gen_ooo_lw_dependent_test, delays=True,
              cmdline_opts=s.__class__.cmdline_opts )

  def test_lw_base_dep_delays( s ):
    run_test( s.ProcType, inst_OoO.gen_ooo_lw_base_dep_test, delays=True,
              cmdline_opts=s.__class__.cmdline_opts )

  def test_sw_data_dep_delays( s ):
    run_test( s.ProcType, inst_OoO.gen_ooo_sw_data_dep_test, delays=True,
              cmdline_opts=s.__class__.cmdline_opts )