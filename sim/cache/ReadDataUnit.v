//========================================================================
// ReadDataUnit
//========================================================================

`ifndef CACHE_READ_DATA_UNIT_V
`define CACHE_READ_DATA_UNIT_V

`include "vc/mem-msgs.v"

module cache_ReadDataUnit
(
  input  logic [127:0] in_,
  input  logic   [3:0] type_,
  input  logic   [3:0] len,
  input  logic   [3:0] offset,
  output logic [127:0] out
);

  logic [127:0] shifted_in;
  assign shifted_in = in_ >> (offset*8);

  always_comb begin

    // Make sure read data is zero if not doing a read

    out = 128'b0;

    // Mux data based on length

    if ( type_ == `VC_MEM_REQ_MSG_TYPE_READ ) begin
      case ( len )
        4'd0    : out = shifted_in;
        4'd1    : out = { 120'b0, shifted_in[ 7:0] };
        4'd2    : out = { 112'b0, shifted_in[15:0] };
        4'd4    : out = {  96'b0, shifted_in[31:0] };
        4'd8    : out = {  64'b0, shifted_in[63:0] };
        default : out = 'x;
      endcase
    end
  end

endmodule

`endif /* CACHE_READ_DATA_UNIT_V */

