//========================================================================
// Proc Datapath ALU
//========================================================================

`ifndef PROC_PROC_DPATH_ALU_V
`define PROC_PROC_DPATH_ALU_V

`include "vc/arithmetic.v"

module proj3_ProcDpathAlu
(
  input  logic [31:0] in0,
  input  logic [31:0] in1,
  input  logic [ 3:0] fn,
  output logic [31:0] out,
  output logic        ops_eq,
  output logic        ops_lt,
  output logic        ops_ltu
);

  always_comb begin

    case ( fn )
      4'd0    : out = in0 + in1;                                // ADD
      4'd11   : out = in0;                                      // CP OP0
      4'd12   : out = in1;                                      // CP OP1
      4'd1    : out = in0 - in1;                                // SUB
      4'd2    : out = in0 << in1[4:0];                          // SLL
      4'd3    : out = in0 | in1;                                // OR
      4'd4    : out = { 31'b0, ($signed(in0) < $signed(in1)) }; // SLT
      4'd5    : out = { 31'b0, (in0 < in1) };                   // SLTU
      4'd6    : out = in0 & in1;                                // AND
      4'd7    : out = in0 ^ in1;                                // XOR
      4'd8    : out = ~(in0 | in1);                             // NOR
      4'd9    : out = in0 >> in1[4:0];                          // SRL
      4'd10   : out = $signed(in0) >>> in1[4:0];                // SRA
      4'd13   : begin
                  out = in0 + in1;
                  out[0] = 1'b0;
                end
      default : out = 32'b0;
    endcase

  end

  // Calculate equality, zero, negative flags

  vc_EqComparator #(32) cond_eq_comp
  (
    .in0  (in0),
    .in1  (in1),
    .out  (ops_eq)
  );

  assign ops_lt = $signed(in0) < $signed(in1);
  assign ops_ltu = in0 < in1;

endmodule

`endif /* PROC_PROC_DPATH_ALU_V */

