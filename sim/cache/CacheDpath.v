//=========================================================================
// CacheDpath
//=========================================================================

`ifndef CACHE_CACHE_DPATH_V
`define CACHE_CACHE_DPATH_V

`include "vc/mem-msgs.v"
`include "vc/regs.v"
`include "vc/arithmetic.v"
`include "vc/muxes.v"

`include "sram/SRAM.v"

`include "cache/WriteDataUnit.v"
`include "cache/ReadDataUnit.v"

module cache_CacheDpath
(
  input  logic          clk,
  input  logic          reset,

  // Processor <-> Cache Interface

  input  mem_req_16B_t  proc2cache_reqstream_msg,
  output mem_resp_16B_t proc2cache_respstream_msg,

  // Cache <-> Memory Interface

  output mem_req_16B_t  cache2mem_reqstream_msg,
  input  mem_resp_16B_t cache2mem_respstream_msg,

  // control signals (ctrl->dpath)

  input  logic          cachereq_reg_en,
  input  logic          memresp_data_reg_en,
  input  logic          write_data_mux_sel,
  input  logic          set_index_bypass_mux_sel,
  input  logic          tag_array_way0_val,
  input  logic          tag_array_way1_val,
  input  logic          tag_array_type,
  input  logic          data_array_way0_val,
  input  logic          data_array_way1_val,
  input  logic          data_array_type,
  input  logic          way_sel,
  input  logic          evict_addr_reg_en,
  input  logic          memreq_type,
  input  logic          memreq_addr_mux_sel,
  input  logic          read_data_reg_en,
  input  logic          read_data_bypass_mux_sel,
  input  logic          cacheresp_test,

  // status signals (dpath->ctrl)

  output logic  [3:0]   cachereq_type,
  output logic [31:0]   cachereq_addr,
  output logic          tag_match_way0,
  output logic          tag_match_way1
);

  //----------------------------------------------------------------------
  // Logic before tag/data array
  //----------------------------------------------------------------------

  // Cache request register

  mem_req_16B_t cachereq_reg_out;

  vc_EnResetReg#($bits(mem_req_16B_t),0) cachereq_reg
  (
    .clk    (clk),
    .reset  (reset),
    .en     (cachereq_reg_en),
    .d      (proc2cache_reqstream_msg),
    .q      (cachereq_reg_out)
  );

  assign cachereq_type = cachereq_reg_out.type_;
  assign cachereq_addr = cachereq_reg_out.addr;

  // Address Mapping

  logic  [3:0] cachereq_addr_offset;
  logic  [1:0] cachereq_addr_byte_offset;
  logic  [1:0] cachereq_addr_word_offset;
  logic  [7:0] cachereq_addr_index;
  logic [19:0] cachereq_addr_tag;

  assign cachereq_addr_offset      = cachereq_reg_out.addr[3:0];
  assign cachereq_addr_byte_offset = cachereq_reg_out.addr[1:0];
  assign cachereq_addr_word_offset = cachereq_reg_out.addr[3:2];
  assign cachereq_addr_index       = cachereq_reg_out.addr[11:4];
  assign cachereq_addr_tag         = cachereq_reg_out.addr[31:12];

  // Set index bypass mux

  logic [7:0] set_index;

  vc_Mux2#(8) set_index_bypass_mux
  (
    .in0   (cachereq_addr_index),
    .in1   (proc2cache_reqstream_msg.addr[11:4]),
    .sel   (set_index_bypass_mux_sel),
    .out   (set_index)
  );

  // Write data unit

  logic  [15:0] write_data_unit_wben;
  logic [127:0] write_data_unit_out;

  cache_WriteDataUnit write_data_unit
  (
    .in_    (cachereq_reg_out.data),
    .len    (cachereq_reg_out.len),
    .offset (cachereq_addr_offset),
    .wben   (write_data_unit_wben),
    .out    (write_data_unit_out)
  );

  // Memory response register

  mem_resp_16B_t memresp_reg_out;

  vc_EnResetReg#($bits(mem_resp_16B_t),0) memresp_reg
  (
    .clk    (clk),
    .reset  (reset),
    .en     (memresp_data_reg_en),
    .d      (cache2mem_respstream_msg),
    .q      (memresp_reg_out)
  );

  // Write byte enable mux

  logic [15:0] wben_mux_out;

  vc_Mux2#(16) wben_mux
  (
    .in0 (write_data_unit_wben),
    .in1 (16'hffff),
    .sel (write_data_mux_sel),
    .out (wben_mux_out)
  );

  // Write data mux

  logic [127:0] write_data_mux_out;

  vc_Mux2#(128) write_data_mux
  (
    .in0 (write_data_unit_out),
    .in1 (memresp_reg_out.data),
    .sel (write_data_mux_sel),
    .out (write_data_mux_out)
  );

  //----------------------------------------------------------------------
  // Tag/data array
  //----------------------------------------------------------------------

  // Tag array for way 0 (256 tags, 20 bits/tag)

  logic [11:0] tag_array_way0_read_unused;
  logic [19:0] tag_array_way0_read_out;

  sram_SRAM#(256,32) tag_array_way0
  (
    .clk         (clk),
    .reset       (reset),
    .port0_val   (tag_array_way0_val),
    .port0_type  (tag_array_type),
    .port0_idx   (set_index),
    .port0_wben  (4'b1111),
    .port0_wdata ({12'b0,cachereq_addr_tag}),
    .port0_rdata ({tag_array_way0_read_unused,tag_array_way0_read_out})
  );

  // Tag array for way 1 (256 tags, 20 bits/tag)

  logic [11:0] tag_array_way1_read_unused;
  logic [19:0] tag_array_way1_read_out;

  sram_SRAM#(256,32) tag_array_way1
  (
    .clk         (clk),
    .reset       (reset),
    .port0_val   (tag_array_way1_val),
    .port0_type  (tag_array_type),
    .port0_idx   (set_index),
    .port0_wben  (4'b1111),
    .port0_wdata ({12'b0,cachereq_addr_tag}),
    .port0_rdata ({tag_array_way1_read_unused,tag_array_way1_read_out})
  );

  // Data array for way 0 (256 cacheslines, 128 bits/cacheline)

  logic [127:0] data_array_way0_read_out;

  sram_SRAM#(256,128) data_array_way0
  (
    .clk         (clk),
    .reset       (reset),
    .port0_val   (data_array_way0_val),
    .port0_type  (data_array_type),
    .port0_idx   (set_index),
    .port0_wben  (wben_mux_out),
    .port0_wdata (write_data_mux_out),
    .port0_rdata (data_array_way0_read_out)
  );

  // Data array for way 1 (256 cacheslines, 128 bits/cacheline)

  logic [127:0] data_array_way1_read_out;

  sram_SRAM#(256,128) data_array_way1
  (
    .clk         (clk),
    .reset       (reset),
    .port0_val   (data_array_way1_val),
    .port0_type  (data_array_type),
    .port0_idx   (set_index),
    .port0_wben  (wben_mux_out),
    .port0_wdata (write_data_mux_out),
    .port0_rdata (data_array_way1_read_out)
  );

  //----------------------------------------------------------------------
  // Logic after tag/data array
  //----------------------------------------------------------------------

  // Eq comparator to check for tag matching in way 0

  vc_EqComparator#(20) tag_compare_way0
  (
    .in0   (cachereq_addr_tag),
    .in1   (tag_array_way0_read_out),
    .out   (tag_match_way0)
  );

  // Eq comparator to check for tag matching in way 1

  vc_EqComparator#(20) tag_compare_way1
  (
    .in0   (cachereq_addr_tag),
    .in1   (tag_array_way1_read_out),
    .out   (tag_match_way1)
  );

  // Tag read mux

  logic [19:0] tag_read_mux_out;

  vc_Mux2#(20) tag_read_mux
  (
    .in0   (tag_array_way0_read_out),
    .in1   (tag_array_way1_read_out),
    .sel   (way_sel),
    .out   (tag_read_mux_out)
  );

  // Make address for eviction

  logic [31:0] evict_addr;
  assign evict_addr = { tag_read_mux_out, cachereq_addr_index, 4'b0 };

  // Eviction address register

  logic [31:0] evict_addr_reg_out;

  vc_EnResetReg#(32,0) evict_addr_reg
  (
    .clk   (clk),
    .reset (reset),
    .en    (evict_addr_reg_en),
    .d     (evict_addr),
    .q     (evict_addr_reg_out)
  );

  // Make address for refill

  logic [31:0] refill_addr;
  assign refill_addr = { cachereq_addr_tag, cachereq_addr_index, 4'b0 };

  // Memory request address mux

  logic [31:0] memreq_addr_mux_out;

  vc_Mux2#(32) memreq_addr_mux
  (
    .in0   (refill_addr),
    .in1   (evict_addr_reg_out),
    .sel   (memreq_addr_mux_sel),
    .out   (memreq_addr_mux_out)
  );

  // Read data mux

  logic [127:0] read_data_mux_out;

  vc_Mux2#(128) read_data_mux
  (
    .in0   (data_array_way0_read_out),
    .in1   (data_array_way1_read_out),
    .sel   (way_sel),
    .out   (read_data_mux_out)
  );

  // Read data register

  logic [127:0] read_data_reg_out;

  vc_EnResetReg#(128,0) read_data_reg
  (
    .clk   (clk),
    .reset (reset),
    .en    (read_data_reg_en),
    .d     (read_data_mux_out),
    .q     (read_data_reg_out)
  );

  // Read data bypass mux

  logic [127:0] read_data_bypass_mux_out;

  vc_Mux2#(128) read_data_bypass_mux
  (
    .in0   (read_data_reg_out),
    .in1   (read_data_mux_out),
    .sel   (read_data_bypass_mux_sel),
    .out   (read_data_bypass_mux_out)
  );

  // Read data unit

  logic [127:0] read_data_unit_out;

  cache_ReadDataUnit read_data_unit
  (
    .in_    (read_data_bypass_mux_out),
    .type_  (cachereq_reg_out.type_),
    .len    (cachereq_reg_out.len),
    .offset (cachereq_addr_offset),
    .out    (read_data_unit_out)
  );

  // Create cache response

  assign proc2cache_respstream_msg.type_  = cachereq_reg_out.type_;
  assign proc2cache_respstream_msg.opaque = cachereq_reg_out.opaque;
  assign proc2cache_respstream_msg.test   = { 1'b0, cacheresp_test };
  assign proc2cache_respstream_msg.len    = cachereq_reg_out.len;
  assign proc2cache_respstream_msg.data   = read_data_unit_out;

  // Create memory request

  assign cache2mem_reqstream_msg.type_    = memreq_type;
  assign cache2mem_reqstream_msg.opaque   = 8'b0;
  assign cache2mem_reqstream_msg.addr     = memreq_addr_mux_out;
  assign cache2mem_reqstream_msg.len      = 4'b0;
  assign cache2mem_reqstream_msg.data     = read_data_reg_out;

endmodule

`endif /* CACHE_DPATH_V */

