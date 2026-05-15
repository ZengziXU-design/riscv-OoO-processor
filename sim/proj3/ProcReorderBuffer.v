// ==================================================
// Reorder Buffer: maintain the ROB for in-order commit
// --------------------------------------------------
// Dataflow: [Allocate] Store old PRF + distribute Tag (pending=1) 
// ===> [Writeback] Wake up by Tag (pending=0) 
// ===> [Commit] Verify and commit in order at Head -> Return old PRF to Rename.
// --------------------------------------------------
// Stage 1 mem-pipe additions:
//   * A third writeback completion port (wb2) is added so that lw / sw
//     can mark their ROB entry pending=0 when the dmem response arrives.
// ==================================================
`ifndef PROC_REORDER_BUFFER_V
`define PROC_REORDER_BUFFER_V

module proj3_ProcReorderBuffer #(
  parameter p_num_entries      = 8,
  parameter p_preg_addr_nbits  = 6   // 64 physical registers
)(
  input  logic                   clk,
  input  logic                   reset,

  //---------------------------------------------------------
  // D stage - Allocate
  //---------------------------------------------------------
  input  logic                   alloc_req,            // request allocate an entry
  input  logic                   alloc_has_rd,         // whether the instruction has rd after rename
  input  logic [4:0]             alloc_rd_addr,        // architectural rd (kept for Line Trace / Debug)
  input  logic [p_preg_addr_nbits-1:0] alloc_rd_paddr_old, // old physical destination (MUST KEEP for freeing)

  output logic [$clog2(p_num_entries)-1:0] alloc_tag,  // ROB tag = tail
  output logic                   rob_full,

  //---------------------------------------------------------
  // Writeback/complete interface 0 (X stage - ALU/CSR)
  //---------------------------------------------------------
  input  logic                   wb0_req,              // instruction with wb0_tag is finished
  input  logic [$clog2(p_num_entries)-1:0] wb0_tag,

  //---------------------------------------------------------
  // Writeback/complete interface 1 (Y3 stage - MUL)
  //---------------------------------------------------------
  input  logic                   wb1_req,              // instruction with wb1_tag is finished
  input  logic [$clog2(p_num_entries)-1:0] wb1_tag,

  //---------------------------------------------------------
  // Writeback/complete interface 2 (M stage - LW/SW)  
  //---------------------------------------------------------
  input  logic                   wb2_req,              // instruction with wb2_tag is finished
  input  logic [$clog2(p_num_entries)-1:0] wb2_tag,

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

  //----------------------------------------------------------------------
  // Combinational status logic
  //----------------------------------------------------------------------
  assign rob_full  = ( count == p_num_entries );
  logic rob_empty;
  assign rob_empty = ( count == 0 );

  assign alloc_tag = tail;

  logic do_alloc;
  assign do_alloc = alloc_req && !rob_full;

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
      // Counter update
      if ( do_alloc && !commit_val )
        count <= count + 1'b1;
      else if ( !do_alloc && commit_val )
        count <= count - 1'b1;

      // D-stage allocate
      if ( do_alloc ) begin
        tail <= ( tail == p_num_entries - 1 ) ? '0 : tail + 1'b1;

        v_entry[tail]      <= 1'b1;
        pending[tail]      <= 1'b1;
        rd_valid[tail]     <= alloc_has_rd;
        rd_addr[tail]      <= alloc_rd_addr;
        rd_paddr_old[tail] <= alloc_rd_paddr_old;
      end

      // C-stage commit
      if ( commit_val ) begin
        head <= ( head == p_num_entries - 1 ) ? '0 : head + 1'b1;
        v_entry[head] <= 1'b0;
      end

      // Completion / writeback tag marks instruction ready
      if ( wb0_req ) begin
        pending[wb0_tag] <= 1'b0;
      end

      if ( wb1_req ) begin
        pending[wb1_tag] <= 1'b0;
      end

      if ( wb2_req ) begin
        pending[wb2_tag] <= 1'b0;
      end
    end
  end

endmodule

`endif /* PROC_REORDER_BUFFER_V */