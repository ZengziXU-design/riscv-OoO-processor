`ifndef PROC_PROC_PREGFILE_V
`define PROC_PROC_PREGFILE_V

// ============================================================================
// Physical register file with 4 read ports and 4 write ports.
//   * Read  ports issue0_rs1/issue0_rs2 : first issued instruction
//   * Read  ports issue1_rs1/issue1_rs2 : second issued instruction
//   * Write port alu0 : ALU0 / CSR result writeback
//   * Write port alu1 : ALU1 result writeback
//   * Write port mul  : MUL result writeback
//   * Write port mem  : LW response writeback
// p0 is hardwired to zero on every cycle and write masks ensure no port
// can corrupt it.
// ============================================================================

module proj3_ProcPregfile
(
  input  logic        clk,
  input  logic        reset,

  // --------------------------------------------------
  // Read ports for issue slot 0
  // --------------------------------------------------
  input  logic  [5:0] rd_addr_issue0_rs1,
  output logic [31:0] rd_data_issue0_rs1,

  input  logic  [5:0] rd_addr_issue0_rs2,
  output logic [31:0] rd_data_issue0_rs2,

  // --------------------------------------------------
  // Read ports for issue slot 1
  // --------------------------------------------------
  input  logic  [5:0] rd_addr_issue1_rs1,
  output logic [31:0] rd_data_issue1_rs1,

  input  logic  [5:0] rd_addr_issue1_rs2,
  output logic [31:0] rd_data_issue1_rs2,

  // --------------------------------------------------
  // Write port for ALU0/CSR results
  // --------------------------------------------------
  input  logic        wr_en_alu0,
  input  logic  [5:0] wr_addr_alu0,
  input  logic [31:0] wr_data_alu0,

  // --------------------------------------------------
  // Write port for ALU1 results
  // --------------------------------------------------
  input  logic        wr_en_alu1,
  input  logic  [5:0] wr_addr_alu1,
  input  logic [31:0] wr_data_alu1,

  // --------------------------------------------------
  // Write port for MUL results
  // --------------------------------------------------
  input  logic        wr_en_mul,
  input  logic  [5:0] wr_addr_mul,
  input  logic [31:0] wr_data_mul,

  // --------------------------------------------------
  // Write port for memory response data
  // --------------------------------------------------
  input  logic        wr_en_mem,
  input  logic  [5:0] wr_addr_mem,
  input  logic [31:0] wr_data_mem
);

  // 64-entry physical register file

  logic [31:0] rfile [0:63];

  // Mask writes to p0 so that p0 is always zero

  logic wr_en_alu0_real;
  logic wr_en_alu1_real;
  logic wr_en_mul_real;
  logic wr_en_mem_real;

  assign wr_en_alu0_real = wr_en_alu0 && ( wr_addr_alu0 != 6'd0 );
  assign wr_en_alu1_real = wr_en_alu1 && ( wr_addr_alu1 != 6'd0 );
  assign wr_en_mul_real  = wr_en_mul  && ( wr_addr_mul  != 6'd0 );
  assign wr_en_mem_real  = wr_en_mem  && ( wr_addr_mem  != 6'd0 );

  // --------------------------------------------------
  // Combinational reads
  // All read ports include same-cycle write bypass.
  // p0 always reads as zero
  // Bypass priority: ALU0 > ALU1 > MUL > MEM.
  //
  // The write ports target physically distinct destination paddrs
  // for any given cycle (the rename + scoreboard guarantee no two
  // instructions write the same paddr in flight), so the priority chain
  // among them only matters for the same-cycle read bypass and is set
  // to match the functional-unit ordering.
  // --------------------------------------------------

  function automatic logic [31:0] read_with_bypass
  (
    input logic [5:0] rd_addr
  );
  begin
    read_with_bypass =
      ( rd_addr == 6'd0 )                              ? 32'd0        :
      ( wr_en_alu0_real && ( wr_addr_alu0 == rd_addr ) ) ? wr_data_alu0 :
      ( wr_en_alu1_real && ( wr_addr_alu1 == rd_addr ) ) ? wr_data_alu1 :
      ( wr_en_mul_real  && ( wr_addr_mul  == rd_addr ) ) ? wr_data_mul  :
      ( wr_en_mem_real  && ( wr_addr_mem  == rd_addr ) ) ? wr_data_mem  :
                                                          rfile[rd_addr];
  end
  endfunction

  assign rd_data_issue0_rs1 = read_with_bypass( rd_addr_issue0_rs1 );
  assign rd_data_issue0_rs2 = read_with_bypass( rd_addr_issue0_rs2 );
  assign rd_data_issue1_rs1 = read_with_bypass( rd_addr_issue1_rs1 );
  assign rd_data_issue1_rs2 = read_with_bypass( rd_addr_issue1_rs2 );

  // --------------------------------------------------
  // Sequential writes / reset
  // --------------------------------------------------

  integer i;
  always_ff @(posedge clk) begin
    if ( reset ) begin
      for ( i = 0; i < 64; i = i + 1 )
        rfile[i] <= 32'd0;
    end
    else begin
      if ( wr_en_mem_real )
        rfile[wr_addr_mem] <= wr_data_mem;

      if ( wr_en_mul_real )
        rfile[wr_addr_mul] <= wr_data_mul;

      if ( wr_en_alu1_real )
        rfile[wr_addr_alu1] <= wr_data_alu1;

      if ( wr_en_alu0_real )
        rfile[wr_addr_alu0] <= wr_data_alu0;

      // Keep p0 hardwired to zero
      rfile[0] <= 32'd0;
    end
  end

endmodule

`endif
