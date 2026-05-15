//=========================================================================
// ICache4B
//=========================================================================
// This is just a wrapper around the 16B cache to provide a 4B cache
// request/response interface.

`ifndef CACHE_ICACHE_4B_V
`define CACHE_ICACHE_4B_V

`include "vc/mem-msgs.v"
`include "vc/trace.v"

`include "cache/Cache.v"

module cache_ICache4B
(
  input  logic          clk,
  input  logic          reset,

  // Processor <-> Cache Interface

  input  mem_req_4B_t   proc2cache_reqstream_msg,
  input  logic          proc2cache_reqstream_val,
  output logic          proc2cache_reqstream_rdy,

  output mem_resp_4B_t  proc2cache_respstream_msg,
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

  // Convert 4B cache request into 16B cache request

  mem_req_16B_t proc2cache_reqstream_msg_16B;

  always_comb begin

    proc2cache_reqstream_msg_16B.type_  = proc2cache_reqstream_msg.type_;
    proc2cache_reqstream_msg_16B.opaque = proc2cache_reqstream_msg.opaque;
    proc2cache_reqstream_msg_16B.addr   = proc2cache_reqstream_msg.addr;

    if ( proc2cache_reqstream_msg.len == 0 )
      proc2cache_reqstream_msg_16B.len = 4'd4;
    else
      proc2cache_reqstream_msg_16B.len = { 2'b0, proc2cache_reqstream_msg.len };

    proc2cache_reqstream_msg_16B.data = { 96'b0, proc2cache_reqstream_msg.data };

  end

  // Instantiate 16B cache

  mem_resp_16B_t proc2cache_respstream_msg_16B;

  cache_Cache cache
  (
    .proc2cache_reqstream_msg  (proc2cache_reqstream_msg_16B),
    .proc2cache_respstream_msg (proc2cache_respstream_msg_16B),
    .*
  );

  // Convert 16B cache response to 4B cache response

  always_comb begin

    proc2cache_respstream_msg.type_  = proc2cache_respstream_msg_16B.type_;
    proc2cache_respstream_msg.opaque = proc2cache_respstream_msg_16B.opaque;
    proc2cache_respstream_msg.test   = proc2cache_respstream_msg_16B.test;

    if ( proc2cache_respstream_msg_16B.len == 4 )
      proc2cache_respstream_msg.len = 2'd0;
    else
      proc2cache_respstream_msg.len = proc2cache_respstream_msg_16B.len[1:0];

    proc2cache_respstream_msg.data = proc2cache_respstream_msg_16B.data[31:0];

  end

  // Line tracing

  `ifndef SYNTHESIS

  `VC_TRACE_BEGIN
  begin
    cache.line_trace( trace_str );
  end
  `VC_TRACE_END

  `endif

endmodule

`endif /* CACHE_ICACHE_4B_V */

