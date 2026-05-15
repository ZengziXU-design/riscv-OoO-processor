//=========================================================================
// Cache
//=========================================================================
// Blocking 8KB two-way set-associative cache with a single-cycle read
// hit latency, single-cycle write hit latency, two-cycle write hit
// occupancy. The cache uses synchornous SRAMs for both the tag and data
// arrays.
//
// Address Mapping:
//
//   31                                         12 11        4 3  2 1  0
//  +---------------------------------------------+-----------+----+----+
//  | tag                                         | set index | wo | bo |
//  +---------------------------------------------+-----------+----+----+
//
//  - byte offset (bo) is 2 bits and assumed to always be zero
//  - word offset (wo) is 2 bits
//  - set index is 8 bits (256 sets, 2 ways, 512 total cache lines)
//  - tag is 20 bits
//

`ifndef CACHE_CACHE_V
`define CACHE_CACHE_V

`include "vc/mem-msgs.v"
`include "vc/trace.v"

`include "cache/CacheCtrl.v"
`include "cache/CacheDpath.v"

module cache_Cache
(
  input  logic          clk,
  input  logic          reset,

  // Processor <-> Cache Interface

  input  mem_req_16B_t  proc2cache_reqstream_msg,
  input  logic          proc2cache_reqstream_val,
  output logic          proc2cache_reqstream_rdy,

  output mem_resp_16B_t proc2cache_respstream_msg,
  output logic          proc2cache_respstream_val,
  input  logic          proc2cache_respstream_rdy,

  // Cache <-> Memory Interface

  output mem_req_16B_t  cache2mem_reqstream_msg,
  output logic          cache2mem_reqstream_val,
  input  logic          cache2mem_reqstream_rdy,

  input  mem_resp_16B_t cache2mem_respstream_msg,
  input  logic          cache2mem_respstream_val,
  output logic          cache2mem_respstream_rdy
);

  //----------------------------------------------------------------------
  // Wires
  //----------------------------------------------------------------------

  // control signals (ctrl->dpath)

  logic         cachereq_reg_en;
  logic         memresp_data_reg_en;
  logic         write_data_mux_sel;
  logic         set_index_bypass_mux_sel;
  logic         tag_array_way0_val;
  logic         tag_array_way1_val;
  logic         tag_array_type;
  logic         data_array_way0_val;
  logic         data_array_way1_val;
  logic         data_array_type;
  logic         way_sel;
  logic         evict_addr_reg_en;
  logic         memreq_type;
  logic         memreq_addr_mux_sel;
  logic         read_data_reg_en;
  logic         read_data_bypass_mux_sel;
  logic         cacheresp_test;

  // status signals (dpath->ctrl)

  logic [ 3:0]  cachereq_type;
  logic [31:0]  cachereq_addr;
  logic         tag_match_way0;
  logic         tag_match_way1;

  // four-state sim fix

  mem_resp_16B_t proc2cache_respstream_msg_raw;
  assign proc2cache_respstream_msg
    = proc2cache_respstream_msg_raw & {$bits(mem_resp_16B_t){proc2cache_respstream_val}};

  mem_req_16B_t cache2mem_reqstream_msg_raw;
  assign cache2mem_reqstream_msg
    = cache2mem_reqstream_msg_raw & {$bits(mem_req_16B_t){cache2mem_reqstream_val}};

  //----------------------------------------------------------------------
  // Control
  //----------------------------------------------------------------------

  cache_CacheCtrl ctrl
  (
   // Processor <-> Cache Interface

   .proc2cache_reqstream_val  (proc2cache_reqstream_val),
   .proc2cache_reqstream_rdy  (proc2cache_reqstream_rdy),
   .proc2cache_respstream_val (proc2cache_respstream_val),
   .proc2cache_respstream_rdy (proc2cache_respstream_rdy),

   // Cache <-> Memory Interface

   .cache2mem_reqstream_val   (cache2mem_reqstream_val),
   .cache2mem_reqstream_rdy   (cache2mem_reqstream_rdy),
   .cache2mem_respstream_val  (cache2mem_respstream_val),
   .cache2mem_respstream_rdy  (cache2mem_respstream_rdy),

    // clk/reset/control/status signals

   .*
  );

  //----------------------------------------------------------------------
  // Datapath
  //----------------------------------------------------------------------

  cache_CacheDpath dpath
  (
   // Processor <-> Cache Interface

   .proc2cache_reqstream_msg  (proc2cache_reqstream_msg),
   .proc2cache_respstream_msg (proc2cache_respstream_msg_raw),

   // Cache <-> Memory Interface

   .cache2mem_reqstream_msg   (cache2mem_reqstream_msg_raw),
   .cache2mem_respstream_msg  (cache2mem_respstream_msg),

    // clk/reset/control/status signals

   .*
  );

  //----------------------------------------------------------------------
  // Line tracing
  //----------------------------------------------------------------------

  `ifndef SYNTHESIS

  integer i;

  logic [`VC_TRACE_NBITS-1:0] str;
  `VC_TRACE_BEGIN
  begin

    // vc_trace.append_str( trace_str, "(" );

    // Display state

    case ( ctrl.state )

      ctrl.IDLE:           vc_trace.append_str( trace_str, "I  " );
      ctrl.TAG_CHECK:      vc_trace.append_str( trace_str, "TC " );
      ctrl.INIT:           vc_trace.append_str( trace_str, "IN " );
      ctrl.HIT_WDA:        vc_trace.append_str( trace_str, "HWA" );
      ctrl.HIT_WDB:        vc_trace.append_str( trace_str, "HWB" );
      ctrl.HIT_WAIT:       vc_trace.append_str( trace_str, "HWT" );
      ctrl.REFILL_REQ:     vc_trace.append_str( trace_str, "RRQ" );
      ctrl.REFILL_WAIT:    vc_trace.append_str( trace_str, "RWT" );
      ctrl.REFILL_UPDATE:  vc_trace.append_str( trace_str, "RUP" );
      ctrl.EVICT_PREP0:    vc_trace.append_str( trace_str, "EP0" );
      ctrl.EVICT_PREP1:    vc_trace.append_str( trace_str, "EP1" );
      ctrl.EVICT_REQ:      vc_trace.append_str( trace_str, "ERQ" );
      ctrl.EVICT_WAIT:     vc_trace.append_str( trace_str, "EWT" );
      ctrl.MISS_RD0:       vc_trace.append_str( trace_str, "MR0" );
      ctrl.MISS_RD1:       vc_trace.append_str( trace_str, "MR1" );
      ctrl.MISS_WD:        vc_trace.append_str( trace_str, "MWD" );
      ctrl.MISS_WAIT:      vc_trace.append_str( trace_str, "MWT" );
      default:             vc_trace.append_str( trace_str, "?  " );

    endcase

    // vc_trace.append_str( trace_str, " " );
    //
    // // Use a "hit" signal in the control unit to display h/m
    //
    // if ( ctrl.state == ctrl.TAG_CHECK ) begin
    //   if ( ctrl.hit_TC )
    //     vc_trace.append_str( trace_str, "h" );
    //   else
    //     vc_trace.append_str( trace_str, "m" );
    // end
    // else
    //   vc_trace.append_str( trace_str, " " );
    //
    // // Way 0: Display all valid tags, show dirty bits with ; symbol
    //
    // vc_trace.append_str( trace_str, "[" );
    // for ( i = 0; i < 16; i = i + 1 ) begin
    //   if ( !ctrl.valid_bits_way0.rfile[i] )
    //     vc_trace.append_str( trace_str, " " );
    //   else begin
    //     // $sformat( str, "%x", dpath.tag_array_way0.sram.mem[i][7:0] );
    //     // vc_trace.append_str( trace_str, str );
    //     if      (  ctrl.dirty_bits.rfile[i] && (ctrl.use_bits.rfile[i] != 1'b0) ) vc_trace.append_str( trace_str, "," );
    //     else if ( !ctrl.dirty_bits.rfile[i] && (ctrl.use_bits.rfile[i] == 1'b0) ) vc_trace.append_str( trace_str, "." );
    //     else if (  ctrl.dirty_bits.rfile[i] && (ctrl.use_bits.rfile[i] == 1'b0) ) vc_trace.append_str( trace_str, ";" );
    //     else                                                                      vc_trace.append_str( trace_str, " " );
    //   end
    // end
    // vc_trace.append_str( trace_str, "]" );
    //
    // // Way 1: Display all valid tags, show dirty bits with ; symbol
    //
    // vc_trace.append_str( trace_str, "[" );
    // for ( i = 0; i < 16; i = i + 1 ) begin
    //   if ( !ctrl.valid_bits_way1.rfile[i] )
    //     vc_trace.append_str( trace_str, " " );
    //   else begin
    //     // $sformat( str, "%x", dpath.tag_array_way1.sram.mem[i][7:0] );
    //     // vc_trace.append_str( trace_str, str );
    //     if      (  ctrl.dirty_bits.rfile[256+i] && (ctrl.use_bits.rfile[i] != 1'b1) ) vc_trace.append_str( trace_str, "," );
    //     else if ( !ctrl.dirty_bits.rfile[256+i] && (ctrl.use_bits.rfile[i] == 1'b1) ) vc_trace.append_str( trace_str, "." );
    //     else if (  ctrl.dirty_bits.rfile[256+i] && (ctrl.use_bits.rfile[i] == 1'b1) ) vc_trace.append_str( trace_str, ";" );
    //     else                                                                        vc_trace.append_str( trace_str, " " );
    //   end
    // end
    // vc_trace.append_str( trace_str, "]" );

    // vc_trace.append_str( trace_str, ")" );

  end
  `VC_TRACE_END

  `endif

endmodule

`endif /* CACHE_CACHE_V */
