// ==================================================
// Reorder Buffer: maintain the ROB for in-order commit
// --------------------------------------------------
// Dataflow: [Allocate] Store old PRF + distribute Tag (pending=1) 
// ===> [Writeback] Wake up by Tag (pending=0) 
// ===> [Commit] Verify and commit in order at Head -> Return old PRF to Rename.
// --------------------------------------------------
// Supports two-wide allocate, four completion ports, and single-wide commit.
// ==================================================
`ifndef PROC_REORDER_BUFFER_V
`define PROC_REORDER_BUFFER_V

module proj3_ProcReorderBuffer #(
  parameter p_num_entries      = 16,
  parameter p_preg_addr_nbits  = 6   // 64 physical registers
)(
  input  logic                   clk,
  input  logic                   reset,

  //---------------------------------------------------------
  // D stage - Allocate
  //---------------------------------------------------------
  input  logic                   alloc_req_lane0,            // request allocate an entry for older inst
  input  logic                   alloc_has_rd_lane0,         // whether lane0 has rd after rename
  input  logic [4:0]             alloc_rd_addr_lane0,        // architectural rd (Line Trace / Debug)
  input  logic [p_preg_addr_nbits-1:0] alloc_rd_paddr_old_lane0, // old physical destination

  input  logic                   alloc_req_lane1,            // request allocate an entry for younger inst
  input  logic                   alloc_has_rd_lane1,         // whether lane1 has rd after rename
  input  logic [4:0]             alloc_rd_addr_lane1,        // architectural rd (Line Trace / Debug)
  input  logic [p_preg_addr_nbits-1:0] alloc_rd_paddr_old_lane1, // old physical destination

  output logic [$clog2(p_num_entries)-1:0] alloc_tag_lane0,  // ROB tag for lane0
  output logic [$clog2(p_num_entries)-1:0] alloc_tag_lane1,  // ROB tag for lane1
  output logic                   rob_alloc_rdy_D,
  output logic                   rob_full,

  //---------------------------------------------------------
  // Writeback/complete interface: ALU0/CSR
  //---------------------------------------------------------
  input  logic                   wb_req_alu0,
  input  logic [$clog2(p_num_entries)-1:0] wb_tag_alu0,

  //---------------------------------------------------------
  // Writeback/complete interface: ALU1
  //---------------------------------------------------------
  input  logic                   wb_req_alu1,
  input  logic [$clog2(p_num_entries)-1:0] wb_tag_alu1,

  //---------------------------------------------------------
  // Writeback/complete interface: MUL
  //---------------------------------------------------------
  input  logic                   wb_req_mul,
  input  logic [$clog2(p_num_entries)-1:0] wb_tag_mul,

  //---------------------------------------------------------
  // Writeback/complete interface: MEM
  //---------------------------------------------------------
  input  logic                   wb_req_mem,
  input  logic [$clog2(p_num_entries)-1:0] wb_tag_mem,

  //---------------------------------------------------------
  // Commit interface
  //---------------------------------------------------------
  output logic                   commit_val,
  output logic                   commit_has_rd,
  output logic [4:0]             commit_rd_addr,        // architectural rd (kept for Line Trace / Debug)
  output logic [p_preg_addr_nbits-1:0] commit_rd_paddr_old
  
);

  //----------------------------------------------------------------------
  // Local parameters
  //----------------------------------------------------------------------
  localparam int c_tag_nbits   = ( p_num_entries > 1 ) ? $clog2( p_num_entries ) : 1;
  localparam int c_count_nbits = $clog2( p_num_entries + 1 );
  localparam logic [c_count_nbits-1:0] c_dual_alloc_count = c_count_nbits'(2);

  function automatic [c_tag_nbits-1:0] incr_ptr
  (
    input logic [c_tag_nbits-1:0] ptr
  );
  begin
    incr_ptr = ( ptr == p_num_entries - 1 ) ? '0 : ptr + 1'b1;
  end
  endfunction

  //----------------------------------------------------------------------
  // Internal storage for ROB entries
  //----------------------------------------------------------------------
  logic        v_entry       [0:p_num_entries-1];
  logic        pending       [0:p_num_entries-1];

  logic        rd_valid      [0:p_num_entries-1];
  logic [4:0]  rd_addr       [0:p_num_entries-1];  // architectural rd
  logic [p_preg_addr_nbits-1:0] rd_paddr_old [0:p_num_entries-1];
  
  //----------------------------------------------------------------------
  // Pointers & Counter
  //----------------------------------------------------------------------
  logic [c_tag_nbits-1:0]   head;
  logic [c_tag_nbits-1:0]   tail;
  logic [c_count_nbits-1:0] count;

  logic [c_tag_nbits-1:0]   tail_plus1;
  logic [c_tag_nbits-1:0]   tail_plus2;
  logic [c_tag_nbits-1:0]   alloc_slot_lane1;
  logic [c_count_nbits-1:0] num_free_entries;

  logic                     do_alloc_lane0;
  logic                     do_alloc_lane1;
  logic [1:0]               do_alloc_count;

  //----------------------------------------------------------------------
  // Combinational status logic
  //----------------------------------------------------------------------
  assign rob_full  = ( count == p_num_entries );
  logic rob_empty;
  assign rob_empty = ( count == 0 );

  assign tail_plus1 = incr_ptr( tail );
  assign tail_plus2 = incr_ptr( tail_plus1 );

  assign alloc_slot_lane1 = alloc_req_lane0 ? tail_plus1 : tail;

  assign alloc_tag_lane0 = tail;
  assign alloc_tag_lane1 = alloc_slot_lane1;

  assign num_free_entries = p_num_entries - count;

  // The frontend dispatches a two-instruction D-stage group atomically.
  // Keep ready independent of alloc_req_lane* so ctrl can use this signal
  // to form the final allocate fire without creating a combinational loop.
  assign rob_alloc_rdy_D = ( c_dual_alloc_count <= num_free_entries );

  assign do_alloc_lane0  = alloc_req_lane0 && rob_alloc_rdy_D;
  assign do_alloc_lane1  = alloc_req_lane1 && rob_alloc_rdy_D;
  assign do_alloc_count  = { 1'b0, do_alloc_lane0 }
                         + { 1'b0, do_alloc_lane1 };

  //----------------------------------------------------------------------
  // Commit logic
  //----------------------------------------------------------------------
  assign commit_val          = !rob_empty && v_entry[head] && !pending[head];
  assign commit_has_rd       = rd_valid[head];
  assign commit_rd_addr      = rd_addr[head];
  assign commit_rd_paddr_old = rd_paddr_old[head];
  
  //----------------------------------------------------------------------
  // Sequential state update
  //----------------------------------------------------------------------
  always_ff @(posedge clk) begin
    int i;
    if ( reset ) begin
      head  <= '0;
      tail  <= '0;
      count <= '0;
      for ( i = 0; i < p_num_entries; i = i + 1 ) begin
        v_entry[i]      <= 1'b0;
        pending[i]      <= 1'b0;
        rd_valid[i]     <= 1'b0;
        rd_addr[i]      <= 5'd0;
        rd_paddr_old[i] <= '0;
      end
    end
    else begin
      // Counter update. Commit remains single-wide.
      count <= count + do_alloc_count - { 1'b0, commit_val };

      // D-stage allocate
      if ( do_alloc_lane0 ) begin
        v_entry[tail]      <= 1'b1;
        pending[tail]      <= 1'b1;
        rd_valid[tail]     <= alloc_has_rd_lane0;
        rd_addr[tail]      <= alloc_rd_addr_lane0;
        rd_paddr_old[tail] <= alloc_rd_paddr_old_lane0;
      end

      if ( do_alloc_lane1 ) begin
        v_entry[alloc_slot_lane1]      <= 1'b1;
        pending[alloc_slot_lane1]      <= 1'b1;
        rd_valid[alloc_slot_lane1]     <= alloc_has_rd_lane1;
        rd_addr[alloc_slot_lane1]      <= alloc_rd_addr_lane1;
        rd_paddr_old[alloc_slot_lane1] <= alloc_rd_paddr_old_lane1;
      end

      if ( do_alloc_count == 2'd2 ) begin
        tail <= tail_plus2;
      end
      else if ( do_alloc_count == 2'd1 ) begin
        tail <= tail_plus1;
      end

      // C-stage commit
      if ( commit_val ) begin
        head <= ( head == p_num_entries - 1 ) ? '0 : head + 1'b1;
        v_entry[head] <= 1'b0;
      end

      // Completion / writeback tag marks instruction ready
      if ( wb_req_alu0 ) begin
        pending[wb_tag_alu0] <= 1'b0;
      end

      if ( wb_req_alu1 ) begin
        pending[wb_tag_alu1] <= 1'b0;
      end

      if ( wb_req_mul ) begin
        pending[wb_tag_mul] <= 1'b0;
      end

      if ( wb_req_mem ) begin
        pending[wb_tag_mem] <= 1'b0;
      end
    end
  end

endmodule

`endif /* PROC_REORDER_BUFFER_V */
