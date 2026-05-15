`ifndef PROC_PROC_MEMUNIT_V
`define PROC_PROC_MEMUNIT_V

`include "vc/mem-msgs.v"

module proj3_MemUnit
#(
  parameter p_paddr_nbits = 6,
  parameter p_rob_nbits   = 3
)
(
  input  logic clk,
  input  logic reset,

  //----------------------------------------------------------------------
  // From IQ / issue stage
  //----------------------------------------------------------------------

  input  logic                     istream_val,
  output logic                     istream_rdy,

  // New feedback to IQ
  output logic                     mem_issue_rdy,

  input  logic [31:0]              istream_base,
  input  logic [31:0]              istream_imm,
  input  logic [p_paddr_nbits-1:0] istream_rd_paddr,
  input  logic [p_rob_nbits-1:0]   istream_rob_idx,

  input  logic                     istream_is_sw,    // 0 for lw, 1 for sw
  input  logic [31:0]              istream_sw_data,

  //----------------------------------------------------------------------
  // To dmem request path
  //----------------------------------------------------------------------

  output logic                     dmem_reqstream_val,
  input  logic                     dmem_reqstream_rdy,
  output logic [31:0]              dmem_reqstream_msg_addr,
  output logic [31:0]              dmem_reqstream_msg_data,
  output logic [2:0]               dmem_reqstream_msg_type,

  //----------------------------------------------------------------------
  // From dmem response path
  //----------------------------------------------------------------------

  input  logic                     dmem_respstream_val,
  output logic                     dmem_respstream_rdy,
  input  logic [31:0]              dmem_respstream_msg_data,

  //----------------------------------------------------------------------
  // To PRF / ROB writeback
  //----------------------------------------------------------------------

  output logic                     ostream_val,
  input  logic                     ostream_rdy,
  output logic                     ostream_rf_wen,
  output logic [31:0]              ostream_data,
  output logic [p_paddr_nbits-1:0] ostream_rd_paddr,
  output logic [p_rob_nbits-1:0]   ostream_rob_idx
);

  //----------------------------------------------------------------------
  // Single M stage state
  //----------------------------------------------------------------------
  // busy_M means there is one outstanding memory request waiting for
  // dmem response. This MemUnit still allows only one in-flight memory
  // instruction, preserving in-order memory issue.

  logic                     busy_M;
  logic                     is_sw_M;
  logic [p_paddr_nbits-1:0] rd_paddr_M;
  logic [p_rob_nbits-1:0]   rob_idx_M;

  //----------------------------------------------------------------------
  // Handshake logic
  //----------------------------------------------------------------------

  logic req_fire;
  logic resp_fire;
  logic can_accept;

  // We can accept a new memory instruction when:
  //   1. there is no outstanding memory request, or
  //   2. the old response is completing in this same cycle
  //
  // dmem_reqstream_rdy is included because this single-stage version does
  // not buffer a request internally. If dmem cannot accept the request,
  // MemUnit should not accept the instruction from IQ.

  assign can_accept = !busy_M || resp_fire;

  assign mem_issue_rdy = can_accept && dmem_reqstream_rdy;
  assign istream_rdy   = mem_issue_rdy;

  // Request path: address is generated directly in the M stage.

  assign dmem_reqstream_val      = istream_val && can_accept;
  assign dmem_reqstream_msg_addr = istream_base + istream_imm;
  assign dmem_reqstream_msg_data = istream_is_sw ? istream_sw_data : 32'b0;
  assign dmem_reqstream_msg_type =
    istream_is_sw ? `VC_MEM_REQ_MSG_TYPE_WRITE
                  : `VC_MEM_REQ_MSG_TYPE_READ;

  assign req_fire = dmem_reqstream_val && dmem_reqstream_rdy;

  // Response / writeback path.

  assign ostream_val      = busy_M && dmem_respstream_val;
  assign ostream_rf_wen   = ostream_val && !is_sw_M;
  assign ostream_data     = is_sw_M ? 32'b0 : dmem_respstream_msg_data;
  assign ostream_rd_paddr = rd_paddr_M;
  assign ostream_rob_idx  = rob_idx_M;

  assign dmem_respstream_rdy = busy_M && ostream_rdy;

  assign resp_fire = ostream_val && ostream_rdy;

  //----------------------------------------------------------------------
  // Sequential logic
  //----------------------------------------------------------------------

  always_ff @( posedge clk ) begin
    if ( reset ) begin
      busy_M     <= 1'b0;
      is_sw_M    <= 1'b0;
      rd_paddr_M <= '0;
      rob_idx_M  <= '0;
    end
    else begin

      // If a new request fires, record the metadata needed when the
      // response comes back. If req_fire and resp_fire happen in the same
      // cycle, the old instruction completes and the new one becomes the
      // new outstanding memory instruction.

      if ( req_fire ) begin
        busy_M     <= 1'b1;
        is_sw_M    <= istream_is_sw;
        rd_paddr_M <= istream_rd_paddr;
        rob_idx_M  <= istream_rob_idx;
      end
      else if ( resp_fire ) begin
        busy_M     <= 1'b0;
        is_sw_M    <= 1'b0;
        rd_paddr_M <= '0;
        rob_idx_M  <= '0;
      end

    end
  end

endmodule

`endif