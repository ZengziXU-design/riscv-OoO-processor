//========================================================================
// 128 words x 32 bits SRAM
//========================================================================

`ifndef SRAM_128x32_1rw
`define SRAM_128x32_1rw

`include "sram/SRAM_generic.v"

`ifndef SYNTHESIS

module SRAM_128x32_1rw
(
  input  logic        CLK, // clock
  input  logic        CEN, // chip enable (active low)
  input  logic        OEN, // output enable (active low)
  input  logic  [6:0] A,   // address
  input  logic  [3:0] WEN, // write byte enable (active low)
  input  logic [31:0] D,   // write data
  output logic [31:0] Q    // read data
);

  sram_SRAM_generic
  #(
    .p_num_entries (128),
    .p_data_nbits  (32)
  )
  sram_generic
  (
    .CLK (CLK),
    .CEN (CEN),
    .OEN (OEN),
    .A   (A),
    .WEN (WEN),
    .D   (D),
    .Q   (Q)
  );

endmodule

`endif /* SYNTHESIS */

`endif /* SRAM_128x32_1rw */

