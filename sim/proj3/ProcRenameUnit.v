// ==================================================
// Rename Unit: maintain the RAT and free list for register renaming
// --------------------------------------------------
// Dataflow: [Dispatch] ARF -> RAT (retrieve old) + Freelist (allocate new) 
// -> send the old PRF to the ROB to wait for reclamation 
// ===> [Commit] ROB -> return the old PRF to the Freelist.
// ==================================================
`ifndef PROC_PROC_RENAME_UNIT_V
`define PROC_PROC_RENAME_UNIT_V

module proj3_ProcRenameUnit #(
  parameter p_preg_addr_nbits = 6   // 64 physical regs
)(
  input  logic clk,
  input  logic reset,

  input  logic rename_en_D,  // perform rename update in D stage
  output logic rename_rdy_D, // Has free physical register for rename

  // --------------------------------------------------
  // From PreDecode (D stage)
  // --------------------------------------------------
  input  logic [4:0] rs1_addr_D,
  input  logic [4:0] rs2_addr_D,
  input  logic [4:0] rd_addr_D,

  input  logic       rs1_valid_D,
  input  logic       rs2_valid_D,
  input  logic       rd_valid_D,

  // --------------------------------------------------
  // To IQ (renamed physical register addresses)
  // --------------------------------------------------
  output logic [p_preg_addr_nbits-1:0] rs1_paddr_D,
  output logic [p_preg_addr_nbits-1:0] rs2_paddr_D,

  output logic                         rs1_paddr_valid_D,
  output logic                         rs2_paddr_valid_D,

  // --------------------------------------------------
  // To ROB allocate (rename metadata)
  // --------------------------------------------------
  output logic                         rd_rename_valid_D,
  output logic [p_preg_addr_nbits-1:0] rd_paddr_old_D,
  output logic [p_preg_addr_nbits-1:0] rd_paddr_new_D, // to ROB and IQ

  // --------------------------------------------------
  // Commit feedback from ROB
  // --------------------------------------------------
  input  logic                         commit_rd_valid_C,
  input  logic [p_preg_addr_nbits-1:0] commit_rd_paddr_old_C
);

  localparam int c_num_arch_regs = 32;
  localparam int c_num_phys_regs = (1 << p_preg_addr_nbits);

  // --------------------------------------------------
  // RAT: architectural reg -> current physical reg
  // --------------------------------------------------

  logic [p_preg_addr_nbits-1:0] rat [0:c_num_arch_regs-1];

  // --------------------------------------------------
  // Free list bitmap
  // freelist_free[i] = 1 means physical reg i is free
  // --------------------------------------------------

  logic [c_num_phys_regs-1:0] freelist_free;

  // --------------------------------------------------
  // Internal allocation helper
  // --------------------------------------------------

  logic [p_preg_addr_nbits-1:0] freelist_alloc_preg;
  logic                         freelist_has_free;

  // --------------------------------------------------
  // Simple pass-through valids
  // --------------------------------------------------

  assign rs1_paddr_valid_D = rs1_valid_D;
  assign rs2_paddr_valid_D = rs2_valid_D;

  // Really needs a new physical destination?
  assign rd_rename_valid_D = rd_valid_D && ( rd_addr_D != 5'd0 );

  // --------------------------------------------------
  // RAT lookup (combinational)
  // --------------------------------------------------

  assign rs1_paddr_D    = rat[rs1_addr_D];
  assign rs2_paddr_D    = rat[rs2_addr_D];
  assign rd_paddr_old_D = rat[rd_addr_D];

  // --------------------------------------------------
  // Free list allocate candidate (combinational)
  //
  // Reset state:
  //   p0  is permanently reserved for x0
  //   p1~p31 are initially occupied by identity mapping x1~x31
  //   p32~p63 are initially free
  //
  // Runtime:
  //   Any physical register that is freed by commit (except p0) can be
  //   allocated again later. So allocation scans from p1 upward.
  // --------------------------------------------------

  always_comb begin
    int i;

    freelist_has_free   = 1'b0;
    freelist_alloc_preg = '0;

    // p0 is never allocatable; scan p1 ~ p63
    for ( i = 1; i < c_num_phys_regs; i = i + 1 ) begin
      if ( !freelist_has_free && freelist_free[i] ) begin
        freelist_has_free   = 1'b1;
        freelist_alloc_preg = i[p_preg_addr_nbits-1:0];
      end
    end
  end

  assign rd_paddr_new_D = freelist_alloc_preg;

  // --------------------------------------------------
  // Sequential state update
  // --------------------------------------------------

  always_ff @(posedge clk) begin
    int i;

    if ( reset ) begin
      // Identity mapping: x0->p0, x1->p1, ..., x31->p31
      for ( i = 0; i < c_num_arch_regs; i = i + 1 ) begin
        rat[i] <= i[p_preg_addr_nbits-1:0];
      end

      // Initial free list:
      // p0~p31 occupied by initial architectural mapping
      // p32~p63 free
      freelist_free <= { {(c_num_phys_regs-c_num_arch_regs){1'b1}}, {c_num_arch_regs{1'b0}} };
    end
    else begin
      // ----------------------------------------------
      // Commit-stage free of old physical destination
      // ----------------------------------------------
      if ( commit_rd_valid_C && ( commit_rd_paddr_old_C != '0 ) ) begin
        freelist_free[commit_rd_paddr_old_C] <= 1'b1;
      end

      // ----------------------------------------------
      // D-stage rename update
      // Only update state when rename_en_D is asserted.
      // ----------------------------------------------
      if ( rename_en_D && rd_rename_valid_D ) begin
        // Assume there is always a free physical reg when rename is enabled
        if ( freelist_has_free ) begin
          rat[rd_addr_D] <= rd_paddr_new_D;
          freelist_free[rd_paddr_new_D] <= 1'b0;
        end
      end

      // Keep x0 permanently mapped to p0, and p0 never free
      rat[0]            <= '0;
      freelist_free[0]  <= 1'b0;
    end
  end

assign rename_rdy_D = !rd_rename_valid_D || freelist_has_free;

endmodule

`endif /* PROC_PROC_RENAME_UNIT_V */