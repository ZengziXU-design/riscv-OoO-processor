//========================================================================
// Null Accelerator Model
//========================================================================
// This is an empty accelerator model. It includes a single 32-bit
// register named xr0 for testing purposes. The model is synthesizable
// and can be combined with an processor RTL model.
//
// We use a two-input normal queue to buffer up the xcelreq. This
// eliminates any combinational loops when composing the accelerator with
// the processor. We combinationally connect the val/rdy from the dequeue
// interface of the xcelreq queue to the xcelresp interface. Essentially,
// an xcelreq is buffered up and waits in the queue until the xcelresp
// interface is ready to accept it.
//
// We directly connect the data from an xcelreq to the input of the xr0
// register, and ideally we would directly connect the output of the xr0
// register to the data of an xcelresp; this would work fine because there
// is only a single accelerator register. So if we are reading or writing
// an accelerator register it must be that one. There is one catch though.
// We don't really have wildcards in our test sources, so it is easier if
// we force the xcelresp data to zero on a write. So we have a little bit
// of muxing to do this.
//
// The final part is that we need to figure out when to set the enable on
// the xr0 register. This register is enabled when the transaction at the
// head of the xcelreq queue is a write and when the xcelresp interface is
// ready.
//

`ifndef PROC_NULL_XCEL_V
`define PROC_NULL_XCEL_V

`include "vc/trace.v"

`include "vc/queues.v"
`include "vc/xcel-msgs.v"

//========================================================================
// Null Xcel Implementation
//========================================================================

module proj3_NullXcel
(
  input  logic        clk,
  input  logic        reset,

  // Interface

  input  xcel_req_t    xcel_reqstream_msg,
  input  logic         xcel_reqstream_val,
  output logic         xcel_reqstream_rdy,

  output xcel_resp_t   xcel_respstream_msg,
  output logic         xcel_respstream_val,
  input  logic         xcel_respstream_rdy

);

  // Accelerator ports and queues

  logic        xcelreq_deq_val;
  logic        xcelreq_deq_rdy;
  xcel_req_t   xcelreq_deq_msg;

  vc_Queue#(`VC_QUEUE_PIPE,$bits(xcel_req_t),1) xcelreq_q
  (
    .clk     (clk),
    .reset   (reset),
    .num_free_entries(),

    .enq_val (xcel_reqstream_val),
    .enq_rdy (xcel_reqstream_rdy),
    .enq_msg (xcel_reqstream_msg),

    .deq_val (xcelreq_deq_val),
    .deq_rdy (xcelreq_deq_rdy),
    .deq_msg (xcelreq_deq_msg)
  );

  // Single accelerator register

  logic        xr0_en;
  logic [31:0] xr0, xr0_next;

  always_ff @(posedge clk) begin
    if ( xr0_en )
      xr0 <= xr0_next;
  end

  // Direct connections for xcelreq/xcelresp

  assign xr0_next                  = xcelreq_deq_msg.data;
  assign xcel_respstream_msg.type_ = xcelreq_deq_msg.type_;

  // Directly connect response val/rdy to queue

  assign xcel_respstream_val = xcelreq_deq_val;
  assign xcelreq_deq_rdy     = xcel_respstream_rdy;

  // Combinational block

  always_comb begin

    // Mux to force xcelresp data to zero on a write
    // Enable xr0 only upon write requests and both val/rdy on resp side

    if ( xcelreq_deq_msg.type_ == `VC_XCEL_REQ_MSG_TYPE_WRITE ) begin
      xr0_en = xcel_respstream_val && xcel_respstream_rdy;
      xcel_respstream_msg.data = '0;
    end
    else begin
      xr0_en = 0;
      xcel_respstream_msg.data = xr0;
    end

  end

  //======================================================================
  // Line Tracing
  //======================================================================

  `ifndef SYNTHESIS

  vc_XcelReqMsgTrace xcel_reqstream_msg_trace
  (
    .clk (clk),
    .reset (reset),
    .val   (xcel_reqstream_val),
    .rdy   (xcel_reqstream_rdy),
    .msg   (xcel_reqstream_msg)
  );

  vc_XcelRespMsgTrace xcel_respstream_msg_trace
  (
    .clk (clk),
    .reset (reset),
    .val   (xcel_respstream_val),
    .rdy   (xcel_respstream_rdy),
    .msg   (xcel_respstream_msg)
  );

  logic [`VC_TRACE_NBITS-1:0] str;
  `VC_TRACE_BEGIN
  begin
    xcel_reqstream_msg_trace.line_trace( trace_str );
    vc_trace.append_str( trace_str, "()" );
    xcel_respstream_msg_trace.line_trace( trace_str );
  end
  `VC_TRACE_END

  `endif /* SYNTHESIS */

endmodule

`endif /* PROC_NULL_XCEL_V */

