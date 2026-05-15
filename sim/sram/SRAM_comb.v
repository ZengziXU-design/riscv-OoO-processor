//========================================================================
// SRAM Combinational
//========================================================================
// This should only be used to help transition from to synchronous SRAMs.
// This will _not_ turn into a real SRAM macro, but it can help students
// transition to the specific interface used by the synchronous SRAMs
// before using SRAM.v
//
// The interface of this module are prefixed by port0_, meaning all reads
// and writes happen through the only port. Multiported SRAMs have ports
// prefixed by port1_, port2_, etc.
//
// The following list describes each port of this module.
//
//  Port Name     Direction  Description
//  ----------------------------------------------------------------------
//  port0_val     I          port enable (1 = enabled)
//  port0_type    I          transaction type, 0 = read, 1 = write
//  port0_idx     I          index of the SRAM
//  port0_wben    I          write byte enables
//  port0_wdata   I          write data
//  port0_rdata   O          read data output
//

`ifndef SRAM_SRAM_COMB_V
`define SRAM_SRAM_COMB_V

module sram_SRAM_comb
#(
  parameter p_num_entries = 256,
  parameter p_data_nbits  = 32,

  // Local constants not meant to be set from outside the module
  parameter c_addr_nbits  = $clog2(p_num_entries),
  parameter c_data_nbytes = (p_data_nbits+7)/8 // $ceil(p_data_nbits/8)
)(
  input  logic                        clk,
  input  logic                        reset,
  input  logic                        port0_val,
  input  logic                        port0_type,
  input  logic [c_addr_nbits-1:0]     port0_idx,
  input  logic [(p_data_nbits/8)-1:0] port0_wben,
  input  logic [p_data_nbits-1:0]     port0_wdata,
  output logic [p_data_nbits-1:0]     port0_rdata
);

  logic                        clk0;
  logic                        web0;
  logic                        csb0;
  logic [(p_data_nbits/8)-1:0] wmask0;
  logic [c_addr_nbits-1:0]     addr0;
  logic [p_data_nbits-1:0]     din0;
  logic [p_data_nbits-1:0]     dout0;

  assign clk0   = clk;
  assign web0   = ~port0_type;
  assign csb0   = ~port0_val;
  assign wmask0 = port0_wben;
  assign addr0  = port0_idx;
  assign din0   = port0_wdata;

  assign port0_rdata = dout0;

  logic [p_data_nbits-1:0] mem[p_num_entries-1:0];

  logic [p_data_nbits-1:0] data_out1;
  logic [p_data_nbits-1:0] wdata1;

  // Read path

  always_comb begin

    if ( ~csb0 && web0 )
      data_out1 = mem[addr0];
    else
      data_out1 = {p_data_nbits{1'bx}};

  end

  // Write path

  genvar i;
  generate
    for ( i = 0; i < c_data_nbytes; i = i + 1 )
    begin : write
      always @( posedge clk0 ) begin
        if ( ~csb0 && ~web0 && wmask0[i] )
          mem[addr0][ (i+1)*8-1 : i*8 ] <= din0[ (i+1)*8-1 : i*8 ];
      end
    end
  endgenerate

  assign dout0 = data_out1;

endmodule

`endif /* SRAM_SRAM_COMB_V */

