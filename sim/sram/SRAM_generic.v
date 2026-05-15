//========================================================================
// Generic Parameterized SRAM
//========================================================================
// This is meant to be instantiated within a carefully named outer module
// so the outer module corresponds to an SRAM generated with the
// SRAM generator.

`ifndef SRAM_SRAM_GENERIC_V
`define SRAM_SRAM_GENERIC_V

module sram_SRAM_generic
#(
  parameter p_num_entries = 2,
  parameter p_data_nbits  = 1,

  // Local constants not meant to be set from outside the module
  parameter c_addr_nbits  = $clog2(p_num_entries),
  parameter c_data_nbytes = (p_data_nbits+7)/8 // $ceil(p_data_nbits/8)
)(
  input  logic                        CLK, // clock
  input  logic                        CEN, // chip enable (active low)
  input  logic                        OEN, // output enable (active low)
  input  logic [c_addr_nbits-1:0]     A,   // address
  input  logic [(p_data_nbits/8)-1:0] WEN, // write byte enable (active low)
  input  logic [p_data_nbits-1:0]     D,   // write data
  output logic [p_data_nbits-1:0]     Q    // read data
);

  logic [p_data_nbits-1:0] mem [p_num_entries];

  // Helper signals

  logic sram_en, read, write;
  assign sram_en = ~CEN;         // active high
  assign read    = &WEN && !OEN; // active high
  assign write   = ~&WEN;        // active high

  logic [(p_data_nbits/8)-1:0] wben;
  assign wben    = ~WEN; // active high

  // Read path

  always @( posedge CLK ) begin
    if ( sram_en && read )
      Q <= mem[A];
    else
      Q <= {p_data_nbits{1'bx}};
  end

  // Write path

  genvar i;
  generate
    for ( i = 0; i < c_data_nbytes; i = i + 1 )
    begin
      always @( posedge CLK ) begin
        if ( sram_en && write && wben[i] ) begin
          mem[A][ (i+1)*8-1 : i*8 ] <= D[ (i+1)*8-1 : i*8 ];
        end
      end
    end
  endgenerate

endmodule

`endif /* SRAM_SRAM_GENERIC_V */

