#=========================================================================
# super_random.py
#=========================================================================
# Random TinyRV2 instruction tests covering the supported instruction
# classes for this processor: RR, RIMM, and MEM (lw/sw).
#
# This processor does NOT support control-flow instructions (branches,
# JAL, JALR) or the lui/auipc immediate instructions, so those test
# categories are intentionally omitted.
#
# Each generator reseeds the RNG with the same fixed seed (or a derived
# per-batch suffix) so failures are reproducible and the generated
# programs are stable across runs.
#
# Per-category random tests are split into NUM_BATCHES batches of
# BATCH_SIZE instructions each. Each batch is a separate pytest case so
# regressions point to a small program rather than one giant one.

import random
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO

from pymtl3 import *
from pymtl3.stdlib.test_utils import run_sim
from proj3.ProcFL import ProcFL
from proj3.test.harness import TestHarness
from proj3.test.inst_utils import *
from proj3.tinyrv2_encoding import assemble

# Fixed seeds for reproducibility.
# - 1-seed mode: uncomment SEEDS_ONE + SEEDS = SEEDS_ONE
# - 3-seed mode: uncomment SEEDS_THREE + SEEDS = SEEDS_THREE
SEED_BASE   = "ece6745"
SEEDS_ONE   = [ f"{SEED_BASE}-s0" ]
SEEDS_THREE = [ f"{SEED_BASE}-s{i}" for i in range(3) ]

# Default to 3-seed regression mode.
SEEDS = SEEDS_THREE

# For demo speed, use this instead:
# SEEDS = SEEDS_ONE

# Per-category split: x batches of x instructions each.
NUM_BATCHES = 20
BATCH_SIZE  = 50

#-------------------------------------------------------------------------
# Op pools
#-------------------------------------------------------------------------
# Note: lui/auipc and all control-flow ops (branches, jal, jalr) are
# intentionally excluded -- this processor does not support them.

RR_OPS         = [ "add", "sub", "mul", "and", "or", "xor",
                   "slt", "sltu", "sll", "srl", "sra" ]

RIMM_ARITH_OPS = [ "addi", "andi", "ori", "xori", "slti", "sltiu" ]
RIMM_SHIFT_OPS = [ "slli", "srli", "srai" ]

def _run_rr_program_on_fl( init_vals, rr_instrs ):
  asm = []

  for r in range( 1, 32 ):
    asm.append( f"csrr x{r}, mngr2proc < {init_vals[r]}" )

  asm.extend( rr_instrs )

  # Sentinel output ensures the program executes through the RR stream.
  asm.append( "csrw proc2mngr, x0 > 0" )

  model = TestHarness( ProcFL )
  model.elaborate()
  mem_image = assemble( [ "\n".join( asm ) ] )
  model.load( mem_image )
  # Keep FL golden execution silent; only RTL test run should print trace.
  with redirect_stdout( StringIO() ), redirect_stderr( StringIO() ):
    run_sim( model, cmdline_opts=None, duts=[ "proc" ] )

  regs = [ int(model.proc.R[i]) for i in range(32) ]

  return regs

def _run_rimm_program_on_fl( init_imms, rimm_instrs ):
  asm = []

  for r in range( 1, 32 ):
    asm.append( f"addi x{r}, x0, {init_imms[r]}" )

  asm.extend( rimm_instrs )

  # Sentinel output ensures the program executes through the RIMM stream.
  asm.append( "csrw proc2mngr, x0 > 0" )

  model = TestHarness( ProcFL )
  model.elaborate()
  mem_image = assemble( [ "\n".join( asm ) ] )
  model.load( mem_image )
  # Keep FL golden execution silent; only RTL test run should print trace.
  with redirect_stdout( StringIO() ), redirect_stderr( StringIO() ):
    run_sim( model, cmdline_opts=None, duts=[ "proc" ] )

  regs = [ int(model.proc.R[i]) for i in range(32) ]

  return regs

def _run_memmix_program_on_fl( init_imms, body_instrs, data_words ):
  asm = []

  for r in range( 1, 32 ):
    asm.append( f"addi x{r}, x0, {init_imms[r]}" )

  # Use x31 as fixed base pointer for the shared data region at 0x2000.
  # Build the base via addi sequences to avoid lui (unsupported on this
  # processor). 0x2000 = 8192 = 2047 + 2047 + 2047 + 2047 + 4.
  asm.append( "addi x31, x0, 2047" )
  asm.append( "addi x31, x31, 2047" )
  asm.append( "addi x31, x31, 2047" )
  asm.append( "addi x31, x31, 2047" )
  asm.append( "addi x31, x31, 4" )

  asm.extend( body_instrs )

  # Sentinel output ensures program runs through all body instructions.
  asm.append( "csrw proc2mngr, x0 > 0" )

  asm_chunks = [ "\n".join( asm ), gen_word_data( data_words ) ]

  model = TestHarness( ProcFL )
  model.elaborate()
  mem_image = assemble( asm_chunks )
  model.load( mem_image )
  with redirect_stdout( StringIO() ), redirect_stderr( StringIO() ):
    run_sim( model, cmdline_opts=None, duts=[ "proc" ] )

  regs = [ int(model.proc.R[i]) for i in range(32) ]

  return regs

def _gen_random_rr_instr():
  op  = random.choice( RR_OPS )
  rd  = random.randint( 1, 30 )
  rs1 = random.randint( 1, 31 )
  rs2 = random.randint( 1, 31 )
  return f"{op} x{rd}, x{rs1}, x{rs2}"

def _gen_random_rimm_instr():
  rd  = random.randint( 1, 30 )
  rs1 = random.randint( 1, 31 )
  if random.random() < 0.7:
    op  = random.choice( RIMM_ARITH_OPS )
    imm = random.randint( -2048, 2047 )
  else:
    op  = random.choice( RIMM_SHIFT_OPS )
    imm = random.randint( 0, 31 )
  return f"{op} x{rd}, x{rs1}, {imm}"

#-------------------------------------------------------------------------
# Per-batch generators (factories)
#-------------------------------------------------------------------------
# Each factory returns a closure that, when called by run_test, produces
# one batch of `n` random sub-tests for the given instruction category.
# The closure reseeds with a per-(category, batch) suffix so each batch
# is independent and reproducible.

def _make_random_rr( seed_id, idx, n ):
  def gen():
    random.seed( f"{seed_id}-rr-{idx:02d}" )
    init_vals = [ 0 ] * 32
    rr_instrs = []

    for r in range( 1, 32 ):
      init_vals[r] = random.randint( 0, 0xffffffff )

    for _ in range( n ):
      op  = random.choice( RR_OPS )
      rd  = random.randint( 1, 31 )
      rs1 = random.randint( 1, 31 )
      rs2 = random.randint( 1, 31 )
      rr_instrs.append( f"{op} x{rd}, x{rs1}, x{rs2}" )

    final_regs = _run_rr_program_on_fl( init_vals, rr_instrs )

    asm = []

    for r in range( 1, 32 ):
      asm.append( f"csrr x{r}, mngr2proc < {init_vals[r]}" )

    asm.extend( rr_instrs )

    for r in range( 1, 32 ):
      asm.append( f"csrw proc2mngr, x{r} > {final_regs[r]}" )

    return [ "\n".join( asm ) ]
  gen.__name__ = f"gen_random_rr_{seed_id}_{idx:02d}_test"
  return gen

def _make_random_rimm( seed_id, idx, n ):
  def gen():
    random.seed( f"{seed_id}-rimm-{idx:02d}" )
    init_imms = [ 0 ] * 32
    rimm_instrs = []

    for r in range( 1, 32 ):
      init_imms[r] = random.randint( -2048, 2047 )

    for _ in range( n ):
      pick = random.random()
      if pick < 0.60:
        op  = random.choice( RIMM_ARITH_OPS )
        rd  = random.randint( 1, 31 )
        rs1 = random.randint( 1, 31 )
        imm = random.randint( -2048, 2047 )
        rimm_instrs.append( f"{op} x{rd}, x{rs1}, {imm}" )
      else:
        op  = random.choice( RIMM_SHIFT_OPS )
        rd  = random.randint( 1, 31 )
        rs1 = random.randint( 1, 31 )
        imm = random.randint( 0, 31 )
        rimm_instrs.append( f"{op} x{rd}, x{rs1}, {imm}" )

    final_regs = _run_rimm_program_on_fl( init_imms, rimm_instrs )

    asm = []

    for r in range( 1, 32 ):
      asm.append( f"addi x{r}, x0, {init_imms[r]}" )

    asm.extend( rimm_instrs )

    for r in range( 1, 32 ):
      asm.append( f"csrw proc2mngr, x{r} > {final_regs[r]}" )

    return [ "\n".join( asm ) ]
  gen.__name__ = f"gen_random_rimm_{seed_id}_{idx:02d}_test"
  return gen

def _make_random_lw( seed_id, idx, n ):
  def gen():
    random.seed( f"{seed_id}-lw-{idx:02d}" )
    init_imms = [ 0 ] * 32
    data      = [ random.randint( 0, 0xffffffff ) for _ in range( 64 ) ]
    body      = []

    for r in range( 1, 32 ):
      init_imms[r] = random.randint( -2048, 2047 )

    # Ensure we always include at least one lw in this batch.
    i = random.randint( 0, 63 )
    body.append( f"lw x{random.randint(1,30)}, {4*i}(x31)" )

    for _ in range( max( n-1, 0 ) ):
      pick = random.random()
      if pick < 0.40:
        i = random.randint( 0, 63 )
        body.append( f"lw x{random.randint(1,30)}, {4*i}(x31)" )
      elif pick < 0.70:
        body.append( _gen_random_rr_instr() )
      else:
        body.append( _gen_random_rimm_instr() )

    final_regs = _run_memmix_program_on_fl( init_imms, body, data )

    asm = []
    for r in range( 1, 32 ):
      asm.append( f"addi x{r}, x0, {init_imms[r]}" )
    # Build base = 0x2000 without using lui.
    asm.append( "addi x31, x0, 2047" )
    asm.append( "addi x31, x31, 2047" )
    asm.append( "addi x31, x31, 2047" )
    asm.append( "addi x31, x31, 2047" )
    asm.append( "addi x31, x31, 4" )
    asm.extend( body )
    for r in range( 1, 32 ):
      asm.append( f"csrw proc2mngr, x{r} > {final_regs[r]}" )

    return [ "\n".join( asm ), gen_word_data( data ) ]
  gen.__name__ = f"gen_random_lw_{seed_id}_{idx:02d}_test"
  return gen

def _make_random_sw( seed_id, idx, n ):
  def gen():
    random.seed( f"{seed_id}-sw-{idx:02d}" )
    init_imms = [ 0 ] * 32
    data      = [ random.randint( 0, 0xffffffff ) for _ in range( 64 ) ]
    body      = []

    for r in range( 1, 32 ):
      init_imms[r] = random.randint( -2048, 2047 )

    for i_step in range( n ):
      pick = random.random()
      if i_step == 0 or pick < 0.35:
        idx_w = random.randint( 0, 63 )
        rs2   = random.randint( 1, 30 )
        body.append( f"sw x{rs2}, {4*idx_w}(x31)" )
        # Frequent readback to make store effects visible in final regs.
        if random.random() < 0.6:
          rd = random.randint( 1, 30 )
          body.append( f"lw x{rd}, {4*idx_w}(x31)" )
      elif pick < 0.55:
        idx_l = random.randint( 0, 63 )
        body.append( f"lw x{random.randint(1,30)}, {4*idx_l}(x31)" )
      elif pick < 0.78:
        body.append( _gen_random_rr_instr() )
      else:
        body.append( _gen_random_rimm_instr() )

    final_regs = _run_memmix_program_on_fl( init_imms, body, data )

    asm = []
    for r in range( 1, 32 ):
      asm.append( f"addi x{r}, x0, {init_imms[r]}" )
    # Build base = 0x2000 without using lui.
    asm.append( "addi x31, x0, 2047" )
    asm.append( "addi x31, x31, 2047" )
    asm.append( "addi x31, x31, 2047" )
    asm.append( "addi x31, x31, 2047" )
    asm.append( "addi x31, x31, 4" )
    asm.extend( body )
    for r in range( 1, 32 ):
      asm.append( f"csrw proc2mngr, x{r} > {final_regs[r]}" )

    return [ "\n".join( asm ), gen_word_data( data ) ]
  gen.__name__ = f"gen_random_sw_{seed_id}_{idx:02d}_test"
  return gen

#-------------------------------------------------------------------------
# Public batch-list builders
#-------------------------------------------------------------------------
# These return NUM_BATCHES generator functions, each emitting a small
# program of BATCH_SIZE sub-tests. The pytest test file consumes these
# lists directly into its parametrize table.

def random_rr_tests( num_batches=NUM_BATCHES, batch_size=BATCH_SIZE, seeds=SEEDS ):
  return [ _make_random_rr( seed_id, i, batch_size )
           for seed_id in seeds
           for i in range( num_batches ) ]

def random_rimm_tests( num_batches=NUM_BATCHES, batch_size=BATCH_SIZE, seeds=SEEDS ):
  return [ _make_random_rimm( seed_id, i, batch_size )
           for seed_id in seeds
           for i in range( num_batches ) ]

def random_lw_tests( num_batches=NUM_BATCHES, batch_size=BATCH_SIZE, seeds=SEEDS ):
  return [ _make_random_lw( seed_id, i, batch_size )
           for seed_id in seeds
           for i in range( num_batches ) ]

def random_sw_tests( num_batches=NUM_BATCHES, batch_size=BATCH_SIZE, seeds=SEEDS ):
  return [ _make_random_sw( seed_id, i, batch_size )
           for seed_id in seeds
           for i in range( num_batches ) ]

#-------------------------------------------------------------------------
# Combined random test
#-------------------------------------------------------------------------
# Mixes RR / RIMM / lw / sw in the same program to stress dispatch, ROB,
# rename, and the MEM unit ordering against a non-uniform instruction
# mix. No control-flow or lui/auipc instructions are used.

def _make_random_all( seed_id, idx, n ):
  def gen():
    random.seed( f"{seed_id}-all-{idx:02d}" )
    init_imms = [ 0 ] * 32
    data      = [ random.randint( 0, 0xffffffff ) for _ in range( 64 ) ]
    body      = []

    for r in range( 1, 32 ):
      init_imms[r] = random.randint( -2048, 2047 )

    # Ensure all supported instruction classes appear at least once.
    i = random.randint( 0, 63 )
    body.append( f"lw x{random.randint(1,30)}, {4*i}(x31)" )
    i = random.randint( 0, 63 )
    body.append( f"sw x{random.randint(1,30)}, {4*i}(x31)" )
    body.append( _gen_random_rr_instr() )
    body.append( _gen_random_rimm_instr() )

    for _ in range( max( n - 4, 0 ) ):
      pick = random.random()
      if pick < 0.20:
        i = random.randint( 0, 63 )
        body.append( f"lw x{random.randint(1,30)}, {4*i}(x31)" )
      elif pick < 0.40:
        i = random.randint( 0, 63 )
        body.append( f"sw x{random.randint(1,30)}, {4*i}(x31)" )
      elif pick < 0.70:
        body.append( _gen_random_rr_instr() )
      else:
        body.append( _gen_random_rimm_instr() )

    final_regs = _run_memmix_program_on_fl( init_imms, body, data )

    asm = []
    for r in range( 1, 32 ):
      asm.append( f"addi x{r}, x0, {init_imms[r]}" )
    # Build base = 0x2000 without using lui.
    asm.append( "addi x31, x0, 2047" )
    asm.append( "addi x31, x31, 2047" )
    asm.append( "addi x31, x31, 2047" )
    asm.append( "addi x31, x31, 2047" )
    asm.append( "addi x31, x31, 4" )
    asm.extend( body )
    for r in range( 1, 32 ):
      asm.append( f"csrw proc2mngr, x{r} > {final_regs[r]}" )

    return [ "\n".join( asm ), gen_word_data( data ) ]
  gen.__name__ = f"gen_random_all_{seed_id}_{idx:02d}_test"
  return gen

def random_all_tests( num_batches=NUM_BATCHES, batch_size=BATCH_SIZE, seeds=SEEDS ):
  return [ _make_random_all( seed_id, i, batch_size )
           for seed_id in seeds
           for i in range( num_batches ) ]