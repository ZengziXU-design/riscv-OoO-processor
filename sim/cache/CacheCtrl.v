//=========================================================================
// CacheCtrl
//=========================================================================

`ifndef CACHE_CACHE_CTRL_V
`define CACHE_CACHE_CTRL_V

`include "vc/regfiles.v"
`include "vc/mem-msgs.v"

module cache_CacheCtrl
(
  input  logic        clk,
  input  logic        reset,

  // Processor <-> Cache Interface

  input  logic        proc2cache_reqstream_val,
  output logic        proc2cache_reqstream_rdy,

  output logic        proc2cache_respstream_val,
  input  logic        proc2cache_respstream_rdy,

  // Cache <-> Memory Interface

  output logic        cache2mem_reqstream_val,
  input  logic        cache2mem_reqstream_rdy,

  input  logic        cache2mem_respstream_val,
  output logic        cache2mem_respstream_rdy,

  // control signals (ctrl->dpath)

  output logic        cachereq_reg_en,
  output logic        memresp_data_reg_en,
  output logic        write_data_mux_sel,
  output logic        set_index_bypass_mux_sel,
  output logic        tag_array_way0_val,
  output logic        tag_array_way1_val,
  output logic        tag_array_type,
  output logic        data_array_way0_val,
  output logic        data_array_way1_val,
  output logic        data_array_type,
  output logic        way_sel,
  output logic        evict_addr_reg_en,
  output logic        memreq_type,
  output logic        memreq_addr_mux_sel,
  output logic        read_data_reg_en,
  output logic        read_data_bypass_mux_sel,
  output logic        cacheresp_test,

  // status signals (dpath->ctrl)

  input  logic  [3:0] cachereq_type,
  input  logic [31:0] cachereq_addr,
  input  logic        tag_match_way0,
  input  logic        tag_match_way1
);

  //----------------------------------------------------------------------
  // State Definitions
  //----------------------------------------------------------------------

  localparam IDLE           = 6'd0;
  localparam TAG_CHECK      = 6'd1;
  localparam INIT           = 6'd2;  // write init
  localparam HIT_WDA        = 6'd3;  // write hit, response sent
  localparam HIT_WDB        = 6'd4;  // write hit, response not sent
  localparam HIT_WAIT       = 6'd5;
  localparam REFILL_REQ     = 6'd6;
  localparam REFILL_WAIT    = 6'd7;
  localparam REFILL_UPDATE  = 6'd8;
  localparam EVICT_PREP0    = 6'd9;
  localparam EVICT_PREP1    = 6'd10;
  localparam EVICT_REQ      = 6'd11;
  localparam EVICT_WAIT     = 6'd12;
  localparam MISS_RD0       = 6'd13;
  localparam MISS_RD1       = 6'd14;
  localparam MISS_WD        = 6'd15;
  localparam MISS_WAIT      = 6'd16;

  //----------------------------------------------------------------------
  // Address Map
  //----------------------------------------------------------------------

  logic [7:0] set_index;
  assign set_index = cachereq_addr[11:4];

  //----------------------------------------------------------------------
  // Cache Request Type
  //----------------------------------------------------------------------

  logic is_read;
  logic is_write;
  logic is_init;

  assign is_read  = cachereq_type == `VC_MEM_REQ_MSG_TYPE_READ;
  assign is_write = cachereq_type == `VC_MEM_REQ_MSG_TYPE_WRITE;
  assign is_init  = cachereq_type == `VC_MEM_REQ_MSG_TYPE_WRITE_INIT;

  //----------------------------------------------------------------------
  // Valid Bits
  //----------------------------------------------------------------------

  logic is_valid_way0;

  vc_ResetRegfile_1r1w#(1,256) valid_bits_way0
  (
    .clk        (clk),
    .reset      (reset),
    .read_addr  (set_index),
    .read_data  (is_valid_way0),
    .write_en   (tag_array_way0_val && (tag_array_type == 1'b1)),
    .write_addr (set_index),
    .write_data (1'b1)
  );

  logic is_valid_way1;

  vc_ResetRegfile_1r1w#(1,256) valid_bits_way1
  (
    .clk        (clk),
    .reset      (reset),
    .read_addr  (set_index),
    .read_data  (is_valid_way1),
    .write_en   (tag_array_way1_val && (tag_array_type == 1'b1)),
    .write_addr (set_index),
    .write_data (1'b1)
  );

  //----------------------------------------------------------------------
  // Hit and Way Select Logic
  //----------------------------------------------------------------------

  logic hit_way0_TC;
  logic hit_way1_TC;
  logic hit_TC;
  logic use_bit;

  assign hit_way0_TC = (is_valid_way0 && tag_match_way0);
  assign hit_way1_TC = (is_valid_way1 && tag_match_way1);
  assign hit_TC      = hit_way0_TC || hit_way1_TC;

  // Way select is which way we want to use. For a hit, it is the way
  // that we found a tag match. For a miss, it is the way we want to use
  // for evict and refill.

  logic way_sel_TC;

  always @(*) begin
    way_sel_TC = 1'b0;
    if      ( is_init )     way_sel_TC = 1'b0;
    else if ( hit_way0_TC ) way_sel_TC = 1'b0;
    else if ( hit_way1_TC ) way_sel_TC = 1'b1;
    else                    way_sel_TC = ~use_bit;
  end

  // We need to save some information from tag check to use in the future
  // including which way (if any) we hit in, and which way we want to use
  // for eviction/refill.

  logic tag_check_reg_en;
  logic way_sel_X;

  always @( posedge clk ) begin
    if ( tag_check_reg_en )
      way_sel_X <= way_sel_TC;
  end

  //----------------------------------------------------------------------
  // Dirty Bits
  //----------------------------------------------------------------------

  logic dirty_bit_in;
  logic dirty_bits_wen;
  logic is_dirty;

  vc_ResetRegfile_1r1w#(1,512) dirty_bits
  (
    .clk        (clk),
    .reset      (reset),
    .read_addr  ({way_sel_TC,set_index}),
    .read_data  (is_dirty),
    .write_en   (dirty_bits_wen),
    .write_addr ({way_sel_X,set_index}),
    .write_data (dirty_bit_in)
  );

  //----------------------------------------------------------------------
  // Use bits
  //----------------------------------------------------------------------

  logic use_bits_wen;

  vc_ResetRegfile_1r1w#(1,256,{256{1'b1}}) use_bits
  (
    .clk        (clk),
    .reset      (reset),
    .read_addr  (set_index),
    .read_data  (use_bit),
    .write_en   (use_bits_wen),
    .write_addr (set_index),
    .write_data (way_sel)
  );

  //----------------------------------------------------------------------
  // State
  //----------------------------------------------------------------------

  logic [5:0] state;
  logic [5:0] state_next;

  always @( posedge clk ) begin
    if ( reset ) begin
      state <= IDLE;
    end
    else begin
      state <= state_next;
    end
  end

  //----------------------------------------------------------------------
  // State Transitions
  //----------------------------------------------------------------------

  always @(*) begin

    state_next = state;
    case ( state )

      IDLE:
        if ( proc2cache_reqstream_val )
          state_next = TAG_CHECK;

      TAG_CHECK:

        // write init
        if ( is_init )
          state_next = INIT;

        // read hit
        else if (  hit_TC &&  is_read  ) begin
          if ( proc2cache_respstream_rdy && proc2cache_reqstream_val )
            state_next = TAG_CHECK;
          else if ( proc2cache_respstream_rdy )
            state_next = IDLE;
          else
            state_next = HIT_WAIT;
        end

        // write hit
        else if (  hit_TC &&  is_write ) begin
          if ( proc2cache_respstream_rdy )
            state_next = HIT_WDA;
          else
            state_next = HIT_WDB;
        end

        // miss (victim is clean)
        else if ( !hit_TC && !is_dirty )
          state_next = REFILL_REQ;

        // miss (victim is dirty)
        else if ( !hit_TC && is_dirty )
          state_next = EVICT_PREP0;

      INIT:
        if ( proc2cache_respstream_rdy && proc2cache_reqstream_val )
          state_next = TAG_CHECK;
        else if ( proc2cache_respstream_rdy )
          state_next = IDLE;
        else
          state_next = HIT_WAIT;

      HIT_WDA:
        if ( proc2cache_reqstream_val )
          state_next = TAG_CHECK;
        else
          state_next = IDLE;

      HIT_WDB:
        if ( proc2cache_respstream_rdy && proc2cache_reqstream_val )
          state_next = TAG_CHECK;
        else if ( proc2cache_respstream_rdy )
          state_next = IDLE;
        else
          state_next = HIT_WAIT;

      HIT_WAIT:
        if ( proc2cache_respstream_rdy )
          state_next = IDLE;

      REFILL_REQ:
        if ( cache2mem_reqstream_rdy )
          state_next = REFILL_WAIT;

      REFILL_WAIT:
        if ( cache2mem_respstream_val )
          state_next = REFILL_UPDATE;

      REFILL_UPDATE:
        if      ( is_read  ) state_next = MISS_RD0;
        else if ( is_write ) state_next = MISS_WD;

      EVICT_PREP0: state_next = EVICT_PREP1;
      EVICT_PREP1: state_next = EVICT_REQ;

      EVICT_REQ:
        if ( cache2mem_reqstream_rdy )
          state_next = EVICT_WAIT;

      EVICT_WAIT:
        if ( cache2mem_respstream_val )
          state_next = REFILL_REQ;

      MISS_RD0: state_next = MISS_RD1;
      MISS_RD1: state_next = MISS_WAIT;
      MISS_WD:  state_next = MISS_WAIT;

      MISS_WAIT:
        if ( proc2cache_respstream_rdy )
          state_next = IDLE;

      default:
        state_next = IDLE;

    endcase

  end

  //----------------------------------------------------------------------
  // State Outputs
  //----------------------------------------------------------------------

  localparam x = 1'bx;
  localparam _ = 1'bx;

  // Tag array index bypass mux sel

  localparam idreg = 1'b0; // cachereq addr reg
  localparam idbyp = 1'b1; // bypass cachereq addr reg

  // Write data mux select

  localparam creq = 1'b0; // cache request
  localparam mrsp = 1'b1; // memory response

  // Memory request type

  localparam rd = 0; // read
  localparam wr = 1; // write

  // Memory address mux select

  //         creq = 1'b0  // cache request
  localparam eadr = 1'b1; // eviction address

  // Read data bypass mux select

  localparam rdreg = 1'b0; // read data register
  localparam rdbyp = 1'b1; // bypass read data register

  // Helper signals

  logic tag_array_val;
  logic data_array_val;

  // See comment below about calculating cacheresp_val

  logic ignore;

  task cs
  (
    input logic cs_cachereq_rdy,
    input logic cs_cacheresp_val,
    input logic cs_memreq_val,
    input logic cs_memresp_rdy,
    input logic cs_cachereq_reg_en,
    input logic cs_memresp_data_reg_en,
    input logic cs_write_data_mux_sel,
    input logic cs_set_index_bypass_mux_sel,
    input logic cs_tag_array_val,
    input logic cs_tag_array_type,
    input logic cs_data_array_val,
    input logic cs_data_array_type,
    input logic cs_evict_addr_reg_en,
    input logic cs_memreq_type,
    input logic cs_memreq_addr_mux_sel,
    input logic cs_tag_check_reg_en,
    input logic cs_read_data_reg_en,
    input logic cs_read_data_bypass_mux_sel,
    input logic cs_cacheresp_test,
    input logic cs_dirty_bit_in,
    input logic cs_dirty_bits_wen,
    input logic cs_use_bits_wen
  );
  begin
    proc2cache_reqstream_rdy  = cs_cachereq_rdy;
    ignore                    = cs_cacheresp_val;
    cache2mem_reqstream_val   = cs_memreq_val;
    cache2mem_respstream_rdy  = cs_memresp_rdy;
    cachereq_reg_en           = cs_cachereq_reg_en;
    memresp_data_reg_en       = cs_memresp_data_reg_en;
    write_data_mux_sel        = cs_write_data_mux_sel;
    set_index_bypass_mux_sel  = cs_set_index_bypass_mux_sel;
    tag_array_val             = cs_tag_array_val;
    tag_array_type            = cs_tag_array_type;
    data_array_val            = cs_data_array_val;
    data_array_type           = cs_data_array_type;
    evict_addr_reg_en         = cs_evict_addr_reg_en;
    memreq_type               = cs_memreq_type;
    memreq_addr_mux_sel       = cs_memreq_addr_mux_sel;
    tag_check_reg_en          = cs_tag_check_reg_en;
    read_data_reg_en          = cs_read_data_reg_en;
    read_data_bypass_mux_sel  = cs_read_data_bypass_mux_sel;
    cacheresp_test            = cs_cacheresp_test;
    dirty_bit_in              = cs_dirty_bit_in;
    dirty_bits_wen            = cs_dirty_bits_wen;
    use_bits_wen              = cs_use_bits_wen;
  end
  endtask

  // Set outputs using a control signal "table"

  logic [5:0] sn;
  assign sn = state_next;

  always @(*) begin
                               cs( x,  x,  x,  x,  x,    x,    x,    x,     x,  x,   x,  x,   x,    x,    x,    x,    x,    x,     x,    x,  x,   x  );
    case ( state )
      //                                                 mem         set                                  mem               read
      //                           proc2   cache   cache resp  write index                    evict       req   tag   read  data
      //                           cache   2mem    req   data  data  byp    tag      data     addr  mem   addr  check data  byp    cache dirty    use
      //                           req rsp req rsp reg   reg   mux   mux    array    array    reg   req   mux   reg   reg   mux    resp  bits     bits
      //                           rdy val val rdy en    en    sel   sel    val/typ  val/typ  en    type  sel   en    en    sel    test  in/wen   wen
      IDLE: begin
        if (sn == TAG_CHECK)   cs( 1,  0,  0,  0,  1,    0,    _,    idbyp, 1,  rd,  1,  rd,  0,    _,    _,    0,    0,    _,     _,    _,  0,   0  );
        if (sn == IDLE)        cs( 1,  0,  0,  0,  0,    0,    _,    _,     0,  _,   0,  _,   0,    _,    _,    0,    0,    _,     _,    _,  0,   0  );
      end

      TAG_CHECK: begin
        if (sn == INIT)        cs( 0,  0,  0,  0,  0,    0,    creq, idreg, 1,  wr,  1,  wr,  0,    _,    _,    1,    0,    _,     _,    _,  0,   0  );
        if (sn == TAG_CHECK)   cs( 1,  1,  0,  0,  1,    0,    _,    idbyp, 1,  rd,  1,  rd,  0,    _,    _,    0,    0,    rdbyp, 1,    _,  0,   1  );
        if (sn == IDLE)        cs( 1,  1,  0,  0,  0,    0,    _,    _,     0,  _,   0,  _,   0,    _,    _,    0,    0,    rdbyp, 1,    _,  0,   1  );
        if (sn == HIT_WAIT)    cs( 0,  1,  0,  0,  0,    0,    _,    _,     0,  _,   0,  _,   0,    _,    _,    0,    1,    rdbyp, 1,    _,  0,   1  );
        if (sn == HIT_WDA)     cs( 0,  1,  0,  0,  0,    0,    creq, idreg, 0,  _,   1,  wr,  0,    _,    _,    1,    0,    _,     1,    _,  0,   0  );
        if (sn == HIT_WDB)     cs( 0,  1,  0,  0,  0,    0,    creq, idreg, 0,  _,   1,  wr,  0,    _,    _,    1,    0,    _,     1,    _,  0,   0  );
        if (sn == REFILL_REQ)  cs( 0,  0,  0,  0,  0,    0,    _,    _,     0,  _,   0,  _,   0,    _,    _,    1,    0,    _,     _,    _,  0,   0  );
        if (sn == EVICT_PREP0) cs( 0,  0,  0,  0,  0,    0,    _,    _,     0,  _,   0,  _,   0,    _,    _,    1,    0,    _,     _,    _,  0,   0  );
      end

      INIT: begin
        if (sn == TAG_CHECK)   cs( 1,  1,  0,  0,  1,    0,    _,    idbyp, 1,  rd,  1,  rd,  0,    _,    _,    0,    0,    _,     0,    _,  0,   1  );
        if (sn == IDLE)        cs( 1,  1,  0,  0,  0,    0,    _,    _,     0,  _,   0,  _,   0,    _,    _,    0,    0,    _,     0,    _,  0,   1  );
        if (sn == HIT_WAIT)    cs( 0,  1,  0,  0,  0,    0,    _,    _,     0,  _,   0,  _,   0,    _,    _,    0,    0,    _,     0,    _,  0,   1  );
      end

      HIT_WDA: begin
        if (sn == TAG_CHECK)   cs( 1,  0,  0,  0,  1,    0,    _,    idbyp, 1,  rd,  1,  rd,  0,    _,    _,    0,    0,    _,     _,    1,  1,   1  );
        if (sn == IDLE)        cs( 1,  0,  0,  0,  0,    0,    _,    _,     0,  _,   0,  _,   0,    _,    _,    0,    0,    _,     _,    1,  1,   1  );
      end

      HIT_WDB: begin
        if (sn == TAG_CHECK)   cs( 1,  1,  0,  0,  1,    0,    _,    idbyp, 1,  rd,  1,  rd,  0,    _,    _,    0,    0,    _,     1,    1,  1,   1  );
        if (sn == IDLE)        cs( 1,  1,  0,  0,  0,    0,    _,    _,     0,  _,   0,  _,   0,    _,    _,    0,    0,    _,     1,    1,  1,   1  );
        if (sn == HIT_WAIT)    cs( 0,  1,  0,  0,  0,    0,    _,    _,     0,  _,   0,  _,   0,    _,    _,    0,    0,    _,     1,    1,  1,   1  );
      end

      HIT_WAIT:                cs( 0,  1,  0,  0,  0,    0,    _,    _,     0,  _,   0,  _,   0,    _,    _,    0,    0,    rdreg, 1,    _,  0,   0  );

      REFILL_REQ:              cs( 0,  0,  1,  0,  0,    0,    _,    _,     0,  _,   0,  _,   0,    rd,   creq, 0,    0,    _,     _,    _,  0,   0  );
      REFILL_WAIT:             cs( 0,  0,  0,  1,  0,    1,    _,    _,     0,  _,   0,  _,   0,    _,    _,    0,    0,    _,     _,    _,  0,   0  );
      REFILL_UPDATE:           cs( 0,  0,  0,  0,  0,    0,    mrsp, idreg, 1,  wr,  1,  wr,  0,    _,    _,    0,    0,    _,     _,    0,  1,   0  );

      EVICT_PREP0:             cs( 0,  0,  0,  0,  0,    0,    _,    idreg, 1,  rd,  1,  rd,  0,    _,    _,    0,    0,    _,     _,    _,  0,   0  );
      EVICT_PREP1:             cs( 0,  0,  0,  0,  0,    0,    _,    _,     0,  _,   0,  _,   1,    _,    _,    0,    1,    _,     _,    _,  0,   0  );
      EVICT_REQ:               cs( 0,  0,  1,  0,  0,    0,    _,    _,     0,  _,   0,  _,   0,    wr,   eadr, 0,    0,    _,     _,    _,  0,   0  );
      EVICT_WAIT:              cs( 0,  0,  0,  1,  0,    1,    _,    _,     0,  _,   0,  _,   0,    _,    _,    0,    0,    _,     _,    _,  0,   0  );

      MISS_RD0:                cs( 0,  0,  0,  0,  0,    0,    _,    idreg, 0,  _,   1,  rd,  0,    _,    _,    0,    0,    _,     _,    _,  0,   0  );
      MISS_RD1:                cs( 0,  0,  0,  0,  0,    0,    _,    _,     0,  _,   0,  _,   0,    _,    _,    0,    1,    _,     _,    _,  0,   1  );
      MISS_WD:                 cs( 0,  0,  0,  0,  0,    0,    creq, idreg, 0,  _,   1,  wr,  0,    _,    _,    0,    0,    _,     _,    1,  1,   1  );
      MISS_WAIT:               cs( 0,  1,  0,  0,  0,    0,    _,    _,     0,  _,   0,  _,   0,    _,    _,    0,    0,    rdreg, 0,    _,  0,   0  );

      default:                 cs( x,  x,  x,  x,  x,    x,    x,    x,     x,  x,   x,  x,   x,    x,    x,    x,    x,    x,     x,    x,  x,   x  );

    endcase

    // Make sure init transactions always set test field to zero even if
    // we are in the HIT_WAIT state

    if ( is_init )
      cacheresp_test = 0;

    // Control which data SRAM to read

    if ( state == TAG_CHECK )
      way_sel = way_sel_TC;
    else
      way_sel = way_sel_X;

    // Control the valid bits for each way of the tag/data arrays

    tag_array_way0_val = tag_array_val;
    tag_array_way1_val = tag_array_val;
    if ( tag_array_val && (tag_array_type == wr) )begin
      tag_array_way0_val = (way_sel == 1'b0);
      tag_array_way1_val = (way_sel == 1'b1);
    end

    data_array_way0_val = data_array_val;
    data_array_way1_val = data_array_val;
    if ( data_array_val && (data_array_type == wr) )begin
      data_array_way0_val = (way_sel == 1'b0);
      data_array_way1_val = (way_sel == 1'b1);
    end

  end

  // We want to calculate proc2cache_respstream_val as indicated in the
  // control signal table above. However, if we just use the control
  // signal table approach it will create an unwanted combinational path
  // from proc2cache_respstream_rdy through state_next and to
  // proc2cache_respstream_val. This will in turn create a combinational
  // loop when we compose the cache with the processor since the
  // processor already has a combinational path from
  // proc2cache_respstream_val to proc2cache_respstream_rdy.
  //
  // The solution is to carefully derive the logic equation for
  // proc2cache_respstream_val such that it does not depend on
  // proc2cache_respstream_rdy.

  always_comb begin

    proc2cache_respstream_val = 1'b0;

    // We have a valid cache response if we are in one of the following
    // states: INIT, HIT_WDB, HIT_WAIT, or MISS_WAIT. This part of the
    // logic only depends on the current state so it was never really an
    // issue with respect to the combinational path.

    if ( (state == INIT) || (state == HIT_WDB) || (state == HIT_WAIT) || (state == MISS_WAIT) )
      proc2cache_respstream_val = 1'b1;

    // We also have a valid cache response if we are in the TAG_CHECK
    // state and we are transtioning back to TAG_CHECK or to IDLE,
    // HIT_WAIT, HIT_WDA, or HIT_WDB. This part of the logic depends on
    // state_next so it is the tricky pary. We are transitioning into
    // these states when there is a hit _and_ the current transaction is
    // not an init. We can write this without using
    // proc2cache_respstream_rdy which avoids the combinational path.

    if ( state == TAG_CHECK ) begin
      if ( hit_TC && !is_init )
        proc2cache_respstream_val = 1'b1;
    end

  end

endmodule

`endif /* CACHE_CTRL_V */
