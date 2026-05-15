//========================================================================
// xcel-msgs : Accelerator message type
//========================================================================
// The accelerator request/response messages are used to interact with
// various accelerators. They are parameterized by the number of bits in
// the address and data.

`ifndef V_XCEL_MSG_V
`define V_XCEL_MSG_V

`include "vc/trace.v"

//========================================================================
// Accelerator Request Message
//========================================================================
// Accelerator request messages can either be to read or write an
// accelerator register. Read requests include just a register specifier,
// while write requests include an accelerator register specifier and the
// actual data to write to the accelerator register.
//
// Message Format:
//
//    1b     5b      32b
//  +------+-------+-----------+
//  | type | raddr | data      |
//  +------+-------+-----------+
//

typedef struct packed
{
  logic [0:0]  type_;
  logic [4:0]  addr;
  logic [31:0] data;
}
xcel_req_t;

`define VC_XCEL_REQ_MSG_TYPE_READ  1'd0
`define VC_XCEL_REQ_MSG_TYPE_WRITE 1'd1
`define VC_XCEL_REQ_MSG_TYPE_X     1'dx

//------------------------------------------------------------------------
// Accelerator Request Message: Trace message
//------------------------------------------------------------------------

`ifndef SYNTHESIS

module vc_XcelReqMsgTrace
(
  input logic       clk,
  input logic       reset,
  input logic       val,
  input logic       rdy,
  input xcel_req_t  msg
);

  // Line tracing

  logic [8*2-1:0] type_str;
  logic [`VC_TRACE_NBITS-1:0] str;

  `VC_TRACE_BEGIN
  begin

    // Convert type into a string

    if ( msg.type_ === `VC_XCEL_REQ_MSG_TYPE_X )
      type_str = "xx";
    else begin
      case ( msg.type_ )
        `VC_XCEL_REQ_MSG_TYPE_READ  : type_str = "rd";
        `VC_XCEL_REQ_MSG_TYPE_WRITE : type_str = "wr";
        default    : type_str = "??";
      endcase
    end

    // Put together the trace string

    if ( msg.type_ == `VC_XCEL_REQ_MSG_TYPE_READ )
      $sformat( str, "%s:%x:        ", type_str, msg.addr );
    else
      $sformat( str, "%s:%x:%x", type_str, msg.addr, msg.data );

    // Trace with val/rdy signals

    vc_trace.append_val_rdy_str( trace_str, val, rdy, str );

  end
  `VC_TRACE_END

endmodule

`endif

//========================================================================
// Accelerator Response Message
//========================================================================
// Accelerator response messages can either be from a read or write of an
// accelerator register. Read requests include the actual value read from
// the accelerator register, while write requests currently include
// nothing other than the type.
//
// Message Format:
//
//    1b     32b
//  +------+-----------+
//  | type | data      |
//  +------+-----------+
//
typedef struct packed
{
  logic [0:0]  type_;
  logic [31:0] data;
}
xcel_resp_t;

`define VC_XCEL_RESP_MSG_TYPE_READ  1'd0
`define VC_XCEL_RESP_MSG_TYPE_WRITE 1'd1
`define VC_XCEL_RESP_MSG_TYPE_X     1'dx

//------------------------------------------------------------------------
// Accelerator Response Message: Trace message
//------------------------------------------------------------------------

`ifndef SYNTHESIS

module vc_XcelRespMsgTrace
(
  input logic       clk,
  input logic       reset,
  input logic       val,
  input logic       rdy,
  input xcel_resp_t msg
);

  // Line tracing

  logic [8*2-1:0] type_str;
  logic [`VC_TRACE_NBITS-1:0] str;

  `VC_TRACE_BEGIN
  begin

    // Convert type into a string

    if ( msg.type_ === `VC_XCEL_RESP_MSG_TYPE_X )
      type_str = "xx";
    else begin
      case ( msg.type_ )
        `VC_XCEL_RESP_MSG_TYPE_READ  : type_str = "rd";
        `VC_XCEL_RESP_MSG_TYPE_WRITE : type_str = "wr";
        default    : type_str = "??";
      endcase
    end

    // Put together the trace string

    if ( msg.type_ == `VC_XCEL_RESP_MSG_TYPE_READ )
      $sformat( str, "%s:%x", type_str, msg.data );
    else
      $sformat( str, "%s:        ", type_str );

    // Trace with val/rdy signals

    vc_trace.append_val_rdy_str( trace_str, val, rdy, str );

  end
  `VC_TRACE_END

endmodule

`endif

`endif /* VC_XCEL_MSG_V */

