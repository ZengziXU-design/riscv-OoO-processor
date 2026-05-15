`ifndef PROC_PROC_PREGFILE_V
`define PROC_PROC_PREGFILE_V

// ============================================================================
// Physical register file with 2 read ports and 3 write ports.
//   * Read  port 0  : rs1 read for issue
//   * Read  port 1  : rs2 read for issue
//   * Write port 0  : ALU / CSR result writeback (X stage)
//   * Write port 1  : MUL result writeback     (Y3 stage)
//   * Write port 2  : LW response writeback    (M stage)  [NEW]
// p0 is hardwired to zero on every cycle and write masks ensure no port
// can corrupt it.
// ============================================================================

module proj3_ProcPregfile
(
  input  logic        clk,
  input  logic        reset,

  // --------------------------------------------------
  // Read port 0 (for issue rs1_paddr)
  // --------------------------------------------------
  input  logic  [5:0] rd_addr0,
  output logic [31:0] rd_data0,

  // --------------------------------------------------
  // Read port 1 (for issue rs2_paddr)
  // --------------------------------------------------
  input  logic  [5:0] rd_addr1,
  output logic [31:0] rd_data1,

  // --------------------------------------------------
  // Write port 0 (for ALU/CSR results)
  // --------------------------------------------------
  input  logic        wr_en0,
  input  logic  [5:0] wr_addr0,
  input  logic [31:0] wr_data0,

  // --------------------------------------------------
  // Write port 1 (for MUL results)
  // --------------------------------------------------
  input  logic        wr_en1,
  input  logic  [5:0] wr_addr1,
  input  logic [31:0] wr_data1,

  // --------------------------------------------------
  // Write port 2 (for LW response data) 
  // --------------------------------------------------
  input  logic        wr_en2,
  input  logic  [5:0] wr_addr2,
  input  logic [31:0] wr_data2
);

  // 64-entry physical register file

  logic [31:0] rfile [0:63];

  // Mask writes to p0 so that p0 is always zero

  logic wr_en0_real;
  logic wr_en1_real;
  logic wr_en2_real;

  assign wr_en0_real = wr_en0 && ( wr_addr0 != 6'd0 );
  assign wr_en1_real = wr_en1 && ( wr_addr1 != 6'd0 );
  assign wr_en2_real = wr_en2 && ( wr_addr2 != 6'd0 );

  // --------------------------------------------------
  // Combinational reads
  // Read ports 0/1 include same-cycle write bypass
  // p0 always reads as zero
  // Bypass priority: port 0 (X) > port 1 (Y3) > port 2 (M).
  //
  // The three write ports target physically distinct destination paddrs
  // for any given cycle (the rename + scoreboard guarantee no two
  // instructions write the same paddr in flight), so the priority chain
  // among them only matters for the same-cycle read bypass and is set
  // arbitrarily here.
  // --------------------------------------------------

  assign rd_data0 =
    ( rd_addr0 == 6'd0 )                          ? 32'd0    :
    ( wr_en0_real && ( wr_addr0 == rd_addr0 ) )   ? wr_data0 :
    ( wr_en1_real && ( wr_addr1 == rd_addr0 ) )   ? wr_data1 :
    ( wr_en2_real && ( wr_addr2 == rd_addr0 ) )   ? wr_data2 :
                                                    rfile[rd_addr0];

  assign rd_data1 =
    ( rd_addr1 == 6'd0 )                          ? 32'd0    :
    ( wr_en0_real && ( wr_addr0 == rd_addr1 ) )   ? wr_data0 :
    ( wr_en1_real && ( wr_addr1 == rd_addr1 ) )   ? wr_data1 :
    ( wr_en2_real && ( wr_addr2 == rd_addr1 ) )   ? wr_data2 :
                                                    rfile[rd_addr1];

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
      if ( wr_en0_real )
        rfile[wr_addr0] <= wr_data0;

      if ( wr_en1_real )
        rfile[wr_addr1] <= wr_data1;

      if ( wr_en2_real )
        rfile[wr_addr2] <= wr_data2;

      // Keep p0 hardwired to zero
      rfile[0] <= 32'd0;
    end
  end

endmodule

`endif