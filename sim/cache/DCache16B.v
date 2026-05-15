//=========================================================================
// DCache16B
//=========================================================================
// This is just a wrapper around the 16B cache.

`ifndef CACHE_DCACHE_16B_V
`define CACHE_DCACHE_16B_V

`include "vc/mem-msgs.v"
`include "vc/trace.v"

`include "cache/Cache.v"

module cache_DCache16B
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

  cache_Cache cache(.*);

  // Line tracing

  `ifndef SYNTHESIS

  `VC_TRACE_BEGIN
  begin
    cache.line_trace( trace_str );
  end
  `VC_TRACE_END

  `endif

endmodule

`endif /* CACHE_DCACHE_16B_V */

