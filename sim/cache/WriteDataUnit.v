//========================================================================
// WriteDataUnit
//========================================================================

`ifndef CACHE_WRITE_DATA_UNIT_V
`define CACHE_WRITE_DATA_UNIT_V

module cache_WriteDataUnit
(
  input  logic [127:0] in_,
  input  logic   [3:0] len,
  input  logic   [3:0] offset,
  output logic  [15:0] wben,
  output logic [127:0] out
);

  logic [15:0] unshifted_wben;

  always_comb begin
    case ( len )
      4'd0:    unshifted_wben = 16'b1111_1111_1111_1111;
      4'd1:    unshifted_wben = 16'b0000_0000_0000_0001;
      4'd2:    unshifted_wben = 16'b0000_0000_0000_0011;
      4'd4:    unshifted_wben = 16'b0000_0000_0000_1111;
      4'd8:    unshifted_wben = 16'b0000_0000_1111_1111;
      default: unshifted_wben = 16'bxxxx_xxxx_xxxx_xxxx;
    endcase
  end

  assign wben = unshifted_wben << offset;
  assign out  = in_ << (offset*8);

endmodule

`endif /* CACHE_WRITE_DATA_UNIT_V */

