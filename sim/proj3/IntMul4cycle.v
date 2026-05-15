//=========================================================================
// Integer Multiplier 4-Cycle Pipelined Implementation
//=========================================================================

`ifndef PROC_INT_MUL_4CYCLE_V
`define PROC_INT_MUL_4CYCLE_V

`include "vc/trace.v"
`include "vc/regs.v"

module proj3_IntMul4cycle
(
  input  logic        clk,
  input  logic        reset,

  input  logic        istream_val,
  output logic        istream_rdy,
  input  logic [63:0] istream_msg,

  output logic        ostream_val,
  input  logic        ostream_rdy,
  output logic [31:0] ostream_msg
);

  //----------------------------------------------------------------------
  // Stage 1: Input Registers & Multiplication
  //----------------------------------------------------------------------

  logic val_q1;
  vc_EnResetReg#(1) val_reg_s1
  (
    .clk   (clk),
    .reset (reset),
    .d     (istream_val),
    .en    (ostream_rdy), // Global stall signal
    .q     (val_q1)
  );

  logic [31:0] a_reg_out;
  vc_EnReg#(32) a_reg
  (
    .clk   (clk),
    .reset (reset),
    .d     (istream_msg[63:32]),
    .en    (ostream_rdy),
    .q     (a_reg_out)
  );

  logic [31:0] b_reg_out;
  vc_EnReg#(32) b_reg
  (
    .clk   (clk),
    .reset (reset),
    .d     (istream_msg[31:0]),
    .en    (ostream_rdy),
    .q     (b_reg_out)
  );

  // Perform multiplication in Stage 1
  logic [31:0] product_s1;
  assign product_s1 = a_reg_out * b_reg_out;

  //----------------------------------------------------------------------
  // Stage 2: Pipeline Register
  //----------------------------------------------------------------------

  logic val_q2;
  vc_EnResetReg#(1) val_reg_s2
  (
    .clk   (clk),
    .reset (reset),
    .d     (val_q1),
    .en    (ostream_rdy),
    .q     (val_q2)
  );

  logic [31:0] product_q2;
  vc_EnReg#(32) product_reg_s2
  (
    .clk   (clk),
    .reset (reset),
    .d     (product_s1),
    .en    (ostream_rdy),
    .q     (product_q2)
  );

  //----------------------------------------------------------------------
  // Stage 3: Pipeline Register
  //----------------------------------------------------------------------

  logic val_q3;
  vc_EnResetReg#(1) val_reg_s3
  (
    .clk   (clk),
    .reset (reset),
    .d     (val_q2),
    .en    (ostream_rdy),
    .q     (val_q3)
  );

  logic [31:0] product_q3;
  vc_EnReg#(32) product_reg_s3
  (
    .clk   (clk),
    .reset (reset),
    .d     (product_q2),
    .en    (ostream_rdy),
    .q     (product_q3)
  );

  //----------------------------------------------------------------------
  // Stage 4: Output Registers
  //----------------------------------------------------------------------

  logic val_q4;
  vc_EnResetReg#(1) val_reg_s4
  (
    .clk   (clk),
    .reset (reset),
    .d     (val_q3),
    .en    (ostream_rdy),
    .q     (val_q4)
  );

  logic [31:0] product_q4;
  vc_EnReg#(32) product_reg_s4
  (
    .clk   (clk),
    .reset (reset),
    .d     (product_q3),
    .en    (ostream_rdy),
    .q     (product_q4)
  );

  //----------------------------------------------------------------------
  // Output Assignments
  //----------------------------------------------------------------------

  // A fully rigid pipeline: if the downstream is stalled (!ostream_rdy), 
  // the entire multiplier stalls, meaning it cannot accept new inputs.
  assign istream_rdy = ostream_rdy; 
  
  assign ostream_val = val_q4;
  assign ostream_msg = product_q4 & {32{ostream_val}}; // 4-state sim fix

  //----------------------------------------------------------------------
  // Line Tracing
  //----------------------------------------------------------------------

  `ifndef SYNTHESIS

  logic [`VC_TRACE_NBITS-1:0] str;
  `VC_TRACE_BEGIN
  begin

    $sformat( str, "%x", istream_msg );
    vc_trace.append_val_rdy_str( trace_str, istream_val, istream_rdy, str );

    // Visualizing the internal pipeline stages [S1 S2 S3 S4]
    vc_trace.append_str( trace_str, "[" );
    vc_trace.append_str( trace_str, val_q1 ? "*" : " " );
    vc_trace.append_str( trace_str, val_q2 ? "*" : " " );
    vc_trace.append_str( trace_str, val_q3 ? "*" : " " );
    vc_trace.append_str( trace_str, val_q4 ? "*" : " " );
    vc_trace.append_str( trace_str, "]" );

    $sformat( str, "%x", ostream_msg );
    vc_trace.append_val_rdy_str( trace_str, ostream_val, ostream_rdy, str );
  end
  `VC_TRACE_END

  `endif /* SYNTHESIS */

endmodule

`endif /* PROC_INT_MUL_4CYCLE_V */