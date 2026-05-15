// ===========================================================================
// Issue Queue for the out-of-order processor
// ---------------------------------------------------------------------------
// Dataflow: [Input] Store instructions and blacklist in Scoreboard 
// ===> [Wakeup] Query Scoreboard + monitor write-back bypass 
// ===> [Select] Issue the oldest ready instruction  
// ===> [Compress] Queue compression and forward shift.
// ===========================================================================
`ifndef PROC_PROC_IQ_V
`define PROC_PROC_IQ_V

module proj3_ProcIssueQueue #(
  parameter p_num_entries    = 4,
  parameter p_prf_addr_nbits = 6,
  parameter p_rob_tag_nbits  = 3
)(
  input  logic        clk,
  input  logic        reset,

  //----------------------------------------------------------------------
  // Upstream interface 
  //----------------------------------------------------------------------
  input  logic        input_val,
  output logic        input_rdy,
  
  // store 
  input  logic [31:0]                  input_inst,    
  input  logic [p_rob_tag_nbits-1:0]   input_rob_tag, 
  input  logic                         input_is_csr,
  input  logic                         input_is_mem,  

  // pr1/pr2/prd address & valid (come from renameunit)
  input  logic [p_prf_addr_nbits-1:0]  input_rs1_addr,
  input  logic                         input_rs1_valid,
  input  logic [p_prf_addr_nbits-1:0]  input_rs2_addr,
  input  logic                         input_rs2_valid,
  input  logic [p_prf_addr_nbits-1:0]  input_rd_addr,
  input  logic                         input_rd_valid,

  //----------------------------------------------------------------------
  // Downstream interface 
  //----------------------------------------------------------------------
  output logic        dispatch_val,
  input  logic        dispatch_rdy,

  // MemUnit availability feedback
  input  logic        mem_issue_rdy,
  
  output logic [31:0]                  dispatch_inst,
  output logic [p_rob_tag_nbits-1:0]   dispatch_rob_tag,
  output logic [p_prf_addr_nbits-1:0]  dispatch_rs1_addr,
  output logic [p_prf_addr_nbits-1:0]  dispatch_rs2_addr,
  output logic [p_prf_addr_nbits-1:0]  dispatch_rd_addr, 
  output logic                         dispatch_rd_valid,

  //----------------------------------------------------------------------
  // Writeback feedback 
  //----------------------------------------------------------------------
  input  logic                         rf_wen0,   
  input  logic [p_prf_addr_nbits-1:0]  rf_waddr0, 
  input  logic                         rf_wen1,   
  input  logic [p_prf_addr_nbits-1:0]  rf_waddr1, 
  input  logic                         rf_wen2,
  input  logic [p_prf_addr_nbits-1:0]  rf_waddr2
);

  //----------------------------------------------------------------------
  // Local parameters 
  //----------------------------------------------------------------------
  localparam int c_idx_nbits = ( p_num_entries > 1 ) ? $clog2( p_num_entries ) : 1;
  localparam int c_cnt_nbits = $clog2( p_num_entries + 1 );
  localparam int c_num_prf   = 1 << p_prf_addr_nbits;

  //----------------------------------------------------------------------
  // Internal storage for the issue queue
  //----------------------------------------------------------------------
  logic                              IQ_valid      [0:p_num_entries-1];
  logic [31:0]                       IQ_insts      [0:p_num_entries-1];
  logic [p_rob_tag_nbits-1:0]        IQ_rob_tag    [0:p_num_entries-1];
  logic                              IQ_is_csr     [0:p_num_entries-1];
  logic                              IQ_is_mem     [0:p_num_entries-1];

  logic [p_prf_addr_nbits-1:0]       IQ_rs1_addr   [0:p_num_entries-1];
  logic                              IQ_rs1_valid  [0:p_num_entries-1];
  logic [p_prf_addr_nbits-1:0]       IQ_rs2_addr   [0:p_num_entries-1];
  logic                              IQ_rs2_valid  [0:p_num_entries-1];
  logic [p_prf_addr_nbits-1:0]       IQ_rd_addr    [0:p_num_entries-1];
  logic                              IQ_rd_valid   [0:p_num_entries-1];

  //----------------------------------------------------------------------
  // Next-state storage
  //----------------------------------------------------------------------
  logic                              IQ_valid_next      [0:p_num_entries-1];
  logic [31:0]                       IQ_insts_next      [0:p_num_entries-1];
  logic [p_rob_tag_nbits-1:0]        IQ_rob_tag_next    [0:p_num_entries-1];
  logic                              IQ_is_csr_next     [0:p_num_entries-1];
  logic                              IQ_is_mem_next     [0:p_num_entries-1];

  logic [p_prf_addr_nbits-1:0]       IQ_rs1_addr_next   [0:p_num_entries-1];
  logic                              IQ_rs1_valid_next  [0:p_num_entries-1];
  logic [p_prf_addr_nbits-1:0]       IQ_rs2_addr_next   [0:p_num_entries-1];
  logic                              IQ_rs2_valid_next  [0:p_num_entries-1];
  logic [p_prf_addr_nbits-1:0]       IQ_rd_addr_next    [0:p_num_entries-1];
  logic                              IQ_rd_valid_next   [0:p_num_entries-1];

  //----------------------------------------------------------------------
  // Scoreboard 
  //----------------------------------------------------------------------
  logic [c_num_prf-1:0] scoreboard_busy;
  logic [c_num_prf-1:0] scoreboard_busy_next;

  //----------------------------------------------------------------------
  // Internal control wires
  //----------------------------------------------------------------------
  logic [c_cnt_nbits-1:0] num_valid_entries;
  logic                   issue_found;
  logic [c_idx_nbits-1:0] issue_idx;
  logic                   entry_ready [0:p_num_entries-1];
  logic                   input_fire;
  logic                   issue_fire;

  //----------------------------------------------------------------------
  // Count valid entries
  //----------------------------------------------------------------------
  always_comb begin
    int i;
    num_valid_entries = '0;
    for ( i = 0; i < p_num_entries; i = i + 1 )
      if ( IQ_valid[i] )
        num_valid_entries = num_valid_entries + 1'b1;
  end

  //----------------------------------------------------------------------
  // Ready check for each IQ entry
  //----------------------------------------------------------------------

  logic rs1_bypass_hit [0:p_num_entries-1];
  logic rs2_bypass_hit [0:p_num_entries-1];

  always_comb begin
    int i;
    for ( i = 0; i < p_num_entries; i = i + 1 ) begin
      rs1_bypass_hit[i] = 1'b0;
      rs2_bypass_hit[i] = 1'b0;
      entry_ready[i]    = 1'b0;

      if ( IQ_valid[i] ) begin

        if ( IQ_rs1_valid[i] ) begin
          rs1_bypass_hit[i]
            = ( rf_wen0 && ( rf_waddr0 != '0 ) && ( rf_waddr0 == IQ_rs1_addr[i] ) )
           || ( rf_wen1 && ( rf_waddr1 != '0 ) && ( rf_waddr1 == IQ_rs1_addr[i] ) )
           || ( rf_wen2 && ( rf_waddr2 != '0 ) && ( rf_waddr2 == IQ_rs1_addr[i] ) );
        end

        if ( IQ_rs2_valid[i] ) begin
          rs2_bypass_hit[i]
            = ( rf_wen0 && ( rf_waddr0 != '0 ) && ( rf_waddr0 == IQ_rs2_addr[i] ) )
           || ( rf_wen1 && ( rf_waddr1 != '0 ) && ( rf_waddr1 == IQ_rs2_addr[i] ) )
           || ( rf_wen2 && ( rf_waddr2 != '0 ) && ( rf_waddr2 == IQ_rs2_addr[i] ) );
        end

        entry_ready[i]
          = ( !IQ_rs1_valid[i]
              || !scoreboard_busy[IQ_rs1_addr[i]]
              || rs1_bypass_hit[i] )
         && ( !IQ_rs2_valid[i]
              || !scoreboard_busy[IQ_rs2_addr[i]]
              || rs2_bypass_hit[i] );
      end
    end
  end

  //----------------------------------------------------------------------
  // Dispatch select
  //----------------------------------------------------------------------

  always_comb begin : dispatch_select
    int   i;
    logic stop_search;
    logic seen_mem;

    dispatch_val      = 1'b0;
    dispatch_inst     = '0;
    dispatch_rob_tag  = '0;
    dispatch_rs1_addr = '0;
    dispatch_rs2_addr = '0;
    dispatch_rd_addr  = '0;
    dispatch_rd_valid = 1'b0;
    
    issue_found       = 1'b0;
    issue_idx         = '0;
    stop_search       = 1'b0;
    seen_mem          = 1'b0;

    for ( i = 0; i < p_num_entries; i = i + 1 ) begin
      if ( !stop_search && IQ_valid[i] ) begin

        // CSR remains a full barrier:
        // it can only issue from the head, and blocks all younger insts.

        if ( IQ_is_csr[i] ) begin
          stop_search = 1'b1; 
          if ( ( i == 0 ) && entry_ready[i] ) begin
            issue_found = 1'b1;
            issue_idx   = i[c_idx_nbits-1:0];
          end
        end

        // MEM is only ordered with respect to other MEM instructions:
        // the oldest MEM may issue when ready and MemUnit can accept it.
        // Younger MEM cannot issue before it, but younger ALU/MUL
        // instructions may still be selected.

        else if ( IQ_is_mem[i] ) begin
          if ( !seen_mem ) begin
            seen_mem = 1'b1;

            if ( entry_ready[i] && mem_issue_rdy ) begin
              issue_found = 1'b1;
              issue_idx   = i[c_idx_nbits-1:0];
              stop_search = 1'b1;
            end
          end
        end

        // Normal ALU/MUL instruction:
        // can issue out of order when ready.

        else if ( entry_ready[i] ) begin
          issue_found = 1'b1;
          issue_idx   = i[c_idx_nbits-1:0];
          stop_search = 1'b1;
        end

      end
    end

    if ( issue_found ) begin
      dispatch_val      = 1'b1;
      dispatch_inst     = IQ_insts[issue_idx];
      dispatch_rob_tag  = IQ_rob_tag[issue_idx];
      dispatch_rs1_addr = IQ_rs1_addr[issue_idx];
      dispatch_rs2_addr = IQ_rs2_addr[issue_idx];
      dispatch_rd_addr  = IQ_rd_addr[issue_idx];
      dispatch_rd_valid = IQ_rd_valid[issue_idx];
    end
  end

  //----------------------------------------------------------------------
  // Fire signals
  //----------------------------------------------------------------------
  assign issue_fire = dispatch_val && dispatch_rdy;
  assign input_rdy  = ( num_valid_entries < p_num_entries ) || issue_fire;
  assign input_fire = input_val && input_rdy;

  //----------------------------------------------------------------------
  // Next-state logic 
  //----------------------------------------------------------------------
  always_comb begin
    int i, r, w;

    for ( i = 0; i < p_num_entries; i = i + 1 ) begin
      IQ_valid_next[i]     = 1'b0;
      IQ_insts_next[i]     = '0;
      IQ_rob_tag_next[i]   = '0;
      IQ_is_csr_next[i]    = 1'b0;
      IQ_is_mem_next[i]    = 1'b0;
      IQ_rs1_addr_next[i]  = '0;
      IQ_rs1_valid_next[i] = 1'b0;
      IQ_rs2_addr_next[i]  = '0;
      IQ_rs2_valid_next[i] = 1'b0;
      IQ_rd_addr_next[i]   = '0;
      IQ_rd_valid_next[i]  = 1'b0;
    end

    w = 0;
    for ( r = 0; r < p_num_entries; r = r + 1 ) begin
      if ( IQ_valid[r] && !( issue_fire && ( r == issue_idx ) ) ) begin
        IQ_valid_next[w]     = IQ_valid[r];
        IQ_insts_next[w]     = IQ_insts[r];
        IQ_rob_tag_next[w]   = IQ_rob_tag[r];
        IQ_is_csr_next[w]    = IQ_is_csr[r];
        IQ_is_mem_next[w]    = IQ_is_mem[r];
        IQ_rs1_addr_next[w]  = IQ_rs1_addr[r];
        IQ_rs1_valid_next[w] = IQ_rs1_valid[r];
        IQ_rs2_addr_next[w]  = IQ_rs2_addr[r];
        IQ_rs2_valid_next[w] = IQ_rs2_valid[r];
        IQ_rd_addr_next[w]   = IQ_rd_addr[r];
        IQ_rd_valid_next[w]  = IQ_rd_valid[r];
        w = w + 1;
      end
    end

    if ( input_fire && ( w < p_num_entries ) ) begin
      IQ_valid_next[w]     = 1'b1;
      IQ_insts_next[w]     = input_inst;
      IQ_rob_tag_next[w]   = input_rob_tag;
      IQ_is_csr_next[w]    = input_is_csr;
      IQ_is_mem_next[w]    = input_is_mem;
      IQ_rs1_addr_next[w]  = input_rs1_addr;
      IQ_rs1_valid_next[w] = input_rs1_valid;
      IQ_rs2_addr_next[w]  = input_rs2_addr;
      IQ_rs2_valid_next[w] = input_rs2_valid;
      IQ_rd_addr_next[w]   = input_rd_addr;
      IQ_rd_valid_next[w]  = input_rd_valid;
    end

    // Scoreboard 
    scoreboard_busy_next = scoreboard_busy;

    if ( rf_wen0 && ( rf_waddr0 != '0 ) )
      scoreboard_busy_next[rf_waddr0] = 1'b0;
    if ( rf_wen1 && ( rf_waddr1 != '0 ) )
      scoreboard_busy_next[rf_waddr1] = 1'b0;
    if ( rf_wen2 && ( rf_waddr2 != '0 ) )
      scoreboard_busy_next[rf_waddr2] = 1'b0;

    if ( input_fire && input_rd_valid && ( input_rd_addr != '0 ) )
      scoreboard_busy_next[input_rd_addr] = 1'b1;

    scoreboard_busy_next[0] = 1'b0;
  end

  //----------------------------------------------------------------------
  // Sequential state update
  //----------------------------------------------------------------------
  always_ff @(posedge clk) begin
    int i;
    if ( reset ) begin
      scoreboard_busy <= '0;
      for ( i = 0; i < p_num_entries; i = i + 1 ) begin
        IQ_valid[i]     <= 1'b0;
        IQ_insts[i]     <= '0;
        IQ_rob_tag[i]   <= '0;
        IQ_is_csr[i]    <= 1'b0;
        IQ_is_mem[i]    <= 1'b0;
        IQ_rs1_addr[i]  <= '0;
        IQ_rs1_valid[i] <= 1'b0;
        IQ_rs2_addr[i]  <= '0;
        IQ_rs2_valid[i] <= 1'b0;
        IQ_rd_addr[i]   <= '0;
        IQ_rd_valid[i]  <= 1'b0;
      end
    end
    else begin
      scoreboard_busy <= scoreboard_busy_next;
      for ( i = 0; i < p_num_entries; i = i + 1 ) begin
        IQ_valid[i]     <= IQ_valid_next[i];
        IQ_insts[i]     <= IQ_insts_next[i];
        IQ_rob_tag[i]   <= IQ_rob_tag_next[i];
        IQ_is_csr[i]    <= IQ_is_csr_next[i];
        IQ_is_mem[i]    <= IQ_is_mem_next[i];
        IQ_rs1_addr[i]  <= IQ_rs1_addr_next[i];
        IQ_rs1_valid[i] <= IQ_rs1_valid_next[i];
        IQ_rs2_addr[i]  <= IQ_rs2_addr_next[i];
        IQ_rs2_valid[i] <= IQ_rs2_valid_next[i];
        IQ_rd_addr[i]   <= IQ_rd_addr_next[i];
        IQ_rd_valid[i]  <= IQ_rd_valid_next[i];
      end
    end
  end

endmodule
`endif /* PROC_PROC_IQ_V */