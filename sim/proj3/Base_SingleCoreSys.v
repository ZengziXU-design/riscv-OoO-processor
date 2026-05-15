//========================================================================
// Base Single-Core System
//========================================================================
// Mirror of proj3_OoO_SingleCoreSys but with the in-order pipelined
// ProcBase as the core. Uses the same ICache4B / DCache4B and the same
// xcel tie-off, so this system is port-compatible with the OoO version
// and can plug into the same test harness for apples-to-apples eval.

`ifndef BASE_SINGLE_CORE_SYS_V
`define BASE_SINGLE_CORE_SYS_V

`include "vc/mem-msgs.v"
`include "vc/trace.v"

`include "proj3/ProcBase.v"
`include "cache/DCache4B.v"
`include "cache/ICache4B.v"

module proj3_Base_SingleCoreSys
(
  input  logic          clk,
  input  logic          reset,

  // From mngr streaming port

  input  logic [31:0]   mngr2proc_msg,
  input  logic          mngr2proc_val,
  output logic          mngr2proc_rdy,

  // To mngr streaming port

  output logic [31:0]   proc2mngr_msg,
  output logic          proc2mngr_val,
  input  logic          proc2mngr_rdy,

  // Instruction Memory Request Port

  output mem_req_16B_t  imem_reqstream_msg,
  output logic          imem_reqstream_val,
  input  logic          imem_reqstream_rdy,

  // Instruction Memory Response Port

  input  mem_resp_16B_t imem_respstream_msg,
  input  logic          imem_respstream_val,
  output logic          imem_respstream_rdy,

  // Data Memory Request Port

  output mem_req_16B_t  dmem_reqstream_msg,
  output logic          dmem_reqstream_val,
  input  logic          dmem_reqstream_rdy,

  // Data Memory Response Port

  input  mem_resp_16B_t dmem_respstream_msg,
  input  logic          dmem_respstream_val,
  output logic          dmem_respstream_rdy,

  // Stats output

  output logic          stats_en,
  output logic          commit_inst,
  output logic          icache_access,
  output logic          icache_miss,
  output logic          dcache_access,
  output logic          dcache_miss
);

  //----------------------------------------------------------------------
  // Processor <-> Cache 4B wires
  //----------------------------------------------------------------------

  mem_req_4B_t  icache_reqstream_msg;
  logic         icache_reqstream_val;
  logic         icache_reqstream_rdy;

  mem_resp_4B_t icache_respstream_msg;
  logic         icache_respstream_val;
  logic         icache_respstream_rdy;

  mem_req_4B_t  dcache_reqstream_msg;
  logic         dcache_reqstream_val;
  logic         dcache_reqstream_rdy;

  mem_resp_4B_t dcache_respstream_msg;
  logic         dcache_respstream_val;
  logic         dcache_respstream_rdy;

  //----------------------------------------------------------------------
  // Unused xcel interface wires
  //----------------------------------------------------------------------
  // ProcBase has the same xcel ports as ProcOoO. We tie them off the
  // same way: sink rdy=0 / src val=0 / src msg=0, so the proc never
  // actually issues an accelerator request that completes.

  xcel_req_t  xcel_reqstream_msg;
  logic       xcel_reqstream_val;
  logic       xcel_reqstream_rdy;

  xcel_resp_t xcel_respstream_msg;
  logic       xcel_respstream_val;
  logic       xcel_respstream_rdy;

  assign xcel_reqstream_rdy  = 1'b0;
  assign xcel_respstream_msg = '0;
  assign xcel_respstream_val = 1'b0;

  //----------------------------------------------------------------------
  // Instruction Cache
  //----------------------------------------------------------------------

  cache_ICache4B icache
  (
    .clk   ( clk   ),
    .reset ( reset ),

    .proc2cache_reqstream_msg  ( icache_reqstream_msg ),
    .proc2cache_reqstream_val  ( icache_reqstream_val ),
    .proc2cache_reqstream_rdy  ( icache_reqstream_rdy ),

    .proc2cache_respstream_msg ( icache_respstream_msg ),
    .proc2cache_respstream_val ( icache_respstream_val ),
    .proc2cache_respstream_rdy ( icache_respstream_rdy ),

    .cache2mem_reqstream_msg   ( imem_reqstream_msg ),
    .cache2mem_reqstream_val   ( imem_reqstream_val ),
    .cache2mem_reqstream_rdy   ( imem_reqstream_rdy ),

    .cache2mem_respstream_msg  ( imem_respstream_msg ),
    .cache2mem_respstream_val  ( imem_respstream_val ),
    .cache2mem_respstream_rdy  ( imem_respstream_rdy )
  );

  //----------------------------------------------------------------------
  // Data Cache
  //----------------------------------------------------------------------

  cache_DCache4B dcache
  (
    .clk   ( clk   ),
    .reset ( reset ),

    .proc2cache_reqstream_msg  ( dcache_reqstream_msg ),
    .proc2cache_reqstream_val  ( dcache_reqstream_val ),
    .proc2cache_reqstream_rdy  ( dcache_reqstream_rdy ),

    .proc2cache_respstream_msg ( dcache_respstream_msg ),
    .proc2cache_respstream_val ( dcache_respstream_val ),
    .proc2cache_respstream_rdy ( dcache_respstream_rdy ),

    .cache2mem_reqstream_msg   ( dmem_reqstream_msg ),
    .cache2mem_reqstream_val   ( dmem_reqstream_val ),
    .cache2mem_reqstream_rdy   ( dmem_reqstream_rdy ),

    .cache2mem_respstream_msg  ( dmem_respstream_msg ),
    .cache2mem_respstream_val  ( dmem_respstream_val ),
    .cache2mem_respstream_rdy  ( dmem_respstream_rdy )
  );

  //----------------------------------------------------------------------
  // Processor (5-stage in-order pipeline)
  //----------------------------------------------------------------------

  proj3_ProcBase
  #(
    .p_num_cores( 1 )
  )
  proc
  (
    .clk   ( clk   ),
    .reset ( reset ),

    .mngr2proc_msg ( mngr2proc_msg ),
    .mngr2proc_val ( mngr2proc_val ),
    .mngr2proc_rdy ( mngr2proc_rdy ),

    .proc2mngr_msg ( proc2mngr_msg ),
    .proc2mngr_val ( proc2mngr_val ),
    .proc2mngr_rdy ( proc2mngr_rdy ),

    .xcel_reqstream_msg ( xcel_reqstream_msg ),
    .xcel_reqstream_val ( xcel_reqstream_val ),
    .xcel_reqstream_rdy ( xcel_reqstream_rdy ),

    .xcel_respstream_msg ( xcel_respstream_msg ),
    .xcel_respstream_val ( xcel_respstream_val ),
    .xcel_respstream_rdy ( xcel_respstream_rdy ),

    .imem_reqstream_msg ( icache_reqstream_msg ),
    .imem_reqstream_val ( icache_reqstream_val ),
    .imem_reqstream_rdy ( icache_reqstream_rdy ),

    .imem_respstream_msg ( icache_respstream_msg ),
    .imem_respstream_val ( icache_respstream_val ),
    .imem_respstream_rdy ( icache_respstream_rdy ),

    .dmem_reqstream_msg ( dcache_reqstream_msg ),
    .dmem_reqstream_val ( dcache_reqstream_val ),
    .dmem_reqstream_rdy ( dcache_reqstream_rdy ),

    .dmem_respstream_msg ( dcache_respstream_msg ),
    .dmem_respstream_val ( dcache_respstream_val ),
    .dmem_respstream_rdy ( dcache_respstream_rdy ),

    .core_id     ( 32'b0       ),
    .commit_inst ( commit_inst ),
    .stats_en    ( stats_en    )
  );

  //----------------------------------------------------------------------
  // Cache statistics
  //----------------------------------------------------------------------

  assign icache_access = icache_reqstream_val  & icache_reqstream_rdy;
  assign icache_miss   = icache_respstream_val & icache_respstream_rdy
                       & ~icache_respstream_msg.test[0];

  assign dcache_access = dcache_reqstream_val  & dcache_reqstream_rdy;
  assign dcache_miss   = dcache_respstream_val & dcache_respstream_rdy
                       & ~dcache_respstream_msg.test[0];

  //----------------------------------------------------------------------
  // Line tracing
  //----------------------------------------------------------------------

`ifndef SYNTHESIS

  `VC_TRACE_BEGIN
  begin
    proc.line_trace( trace_str );
    vc_trace.append_str( trace_str, "|" );
    icache.line_trace( trace_str );
    dcache.line_trace( trace_str );
  end
  `VC_TRACE_END

`endif /* SYNTHESIS */

endmodule

`endif /* BASE_SINGLE_CORE_SYS_V */