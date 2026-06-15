// ===========================================================================
// Two-wide issue queue for the out-of-order processor
// ---------------------------------------------------------------------------
// Dataflow: [Input] Store instructions and mark destinations busy
// ===> [Wakeup] Query scoreboard and writeback bypasses
// ===> [Select] Select up to two oldest ready instructions
// ===> [Dispatch] Route them to ALU0, ALU1, MUL, or MEM
// ===> [Compress] Remove only entries that complete a val/rdy handshake.
// ===========================================================================
`ifndef PROC_PROC_IQ_V
`define PROC_PROC_IQ_V

module proj3_ProcIssueQueue #(
  parameter p_num_entries    = 8,
  parameter p_prf_addr_nbits = 6,
  parameter p_rob_tag_nbits  = 4
)(
  input  logic        clk,
  input  logic        reset,

  // Upstream: two-wide enqueue
  input  logic        input_val_lane0,
  input  logic        input_val_lane1,
  output logic        input_rdy,

  input  logic [31:0]                  input_inst_lane0,
  input  logic [p_rob_tag_nbits-1:0]   input_rob_tag_lane0,
  input  logic                         input_is_csr_lane0,
  input  logic                         input_is_mem_lane0,
  input  logic                         input_is_mul_lane0,

  input  logic [31:0]                  input_inst_lane1,
  input  logic [p_rob_tag_nbits-1:0]   input_rob_tag_lane1,
  input  logic                         input_is_csr_lane1,
  input  logic                         input_is_mem_lane1,
  input  logic                         input_is_mul_lane1,

  input  logic [p_prf_addr_nbits-1:0]  input_rs1_addr_lane0,
  input  logic                         input_rs1_valid_lane0,
  input  logic [p_prf_addr_nbits-1:0]  input_rs2_addr_lane0,
  input  logic                         input_rs2_valid_lane0,
  input  logic [p_prf_addr_nbits-1:0]  input_rd_addr_lane0,
  input  logic                         input_rd_valid_lane0,

  input  logic [p_prf_addr_nbits-1:0]  input_rs1_addr_lane1,
  input  logic                         input_rs1_valid_lane1,
  input  logic [p_prf_addr_nbits-1:0]  input_rs2_addr_lane1,
  input  logic                         input_rs2_valid_lane1,
  input  logic [p_prf_addr_nbits-1:0]  input_rd_addr_lane1,
  input  logic                         input_rd_valid_lane1,

  // ALU0 dispatch channel
  output logic                         alu0_dispatch_val,
  input  logic                         alu0_dispatch_rdy,
  output logic [31:0]                  alu0_dispatch_inst,
  output logic [p_rob_tag_nbits-1:0]   alu0_dispatch_rob_tag,
  output logic [p_prf_addr_nbits-1:0]  alu0_dispatch_rs1_addr,
  output logic [p_prf_addr_nbits-1:0]  alu0_dispatch_rs2_addr,
  output logic [p_prf_addr_nbits-1:0]  alu0_dispatch_rd_addr,
  output logic                         alu0_dispatch_rd_valid,

  // ALU1 dispatch channel
  output logic                         alu1_dispatch_val,
  input  logic                         alu1_dispatch_rdy,
  output logic [31:0]                  alu1_dispatch_inst,
  output logic [p_rob_tag_nbits-1:0]   alu1_dispatch_rob_tag,
  output logic [p_prf_addr_nbits-1:0]  alu1_dispatch_rs1_addr,
  output logic [p_prf_addr_nbits-1:0]  alu1_dispatch_rs2_addr,
  output logic [p_prf_addr_nbits-1:0]  alu1_dispatch_rd_addr,
  output logic                         alu1_dispatch_rd_valid,

  // MUL dispatch channel
  output logic                         mul_dispatch_val,
  input  logic                         mul_dispatch_rdy,
  output logic [31:0]                  mul_dispatch_inst,
  output logic [p_rob_tag_nbits-1:0]   mul_dispatch_rob_tag,
  output logic [p_prf_addr_nbits-1:0]  mul_dispatch_rs1_addr,
  output logic [p_prf_addr_nbits-1:0]  mul_dispatch_rs2_addr,
  output logic [p_prf_addr_nbits-1:0]  mul_dispatch_rd_addr,
  output logic                         mul_dispatch_rd_valid,

  // MEM dispatch channel
  output logic                         mem_dispatch_val,
  input  logic                         mem_dispatch_rdy,
  output logic [31:0]                  mem_dispatch_inst,
  output logic [p_rob_tag_nbits-1:0]   mem_dispatch_rob_tag,
  output logic [p_prf_addr_nbits-1:0]  mem_dispatch_rs1_addr,
  output logic [p_prf_addr_nbits-1:0]  mem_dispatch_rs2_addr,
  output logic [p_prf_addr_nbits-1:0]  mem_dispatch_rd_addr,
  output logic                         mem_dispatch_rd_valid,

  // Writeback feedback
  input  logic                         rf_wen_alu0,
  input  logic [p_prf_addr_nbits-1:0]  rf_waddr_alu0,
  input  logic                         rf_wen_alu1,
  input  logic [p_prf_addr_nbits-1:0]  rf_waddr_alu1,
  input  logic                         rf_wen_mul,
  input  logic [p_prf_addr_nbits-1:0]  rf_waddr_mul,
  input  logic                         rf_wen_mem,
  input  logic [p_prf_addr_nbits-1:0]  rf_waddr_mem
);

  localparam int c_idx_nbits = ( p_num_entries > 1 ) ? $clog2( p_num_entries ) : 1;
  localparam int c_cnt_nbits = $clog2( p_num_entries + 1 );
  localparam int c_num_prf   = 1 << p_prf_addr_nbits;

  logic                              IQ_valid      [0:p_num_entries-1];
  logic [31:0]                       IQ_insts      [0:p_num_entries-1];
  logic [p_rob_tag_nbits-1:0]        IQ_rob_tag    [0:p_num_entries-1];
  logic                              IQ_is_csr     [0:p_num_entries-1];
  logic                              IQ_is_mem     [0:p_num_entries-1];
  logic                              IQ_is_mul     [0:p_num_entries-1];
  logic [p_prf_addr_nbits-1:0]       IQ_rs1_addr   [0:p_num_entries-1];
  logic                              IQ_rs1_valid  [0:p_num_entries-1];
  logic [p_prf_addr_nbits-1:0]       IQ_rs2_addr   [0:p_num_entries-1];
  logic                              IQ_rs2_valid  [0:p_num_entries-1];
  logic [p_prf_addr_nbits-1:0]       IQ_rd_addr    [0:p_num_entries-1];
  logic                              IQ_rd_valid   [0:p_num_entries-1];

  logic                              IQ_valid_next      [0:p_num_entries-1];
  logic [31:0]                       IQ_insts_next      [0:p_num_entries-1];
  logic [p_rob_tag_nbits-1:0]        IQ_rob_tag_next    [0:p_num_entries-1];
  logic                              IQ_is_csr_next     [0:p_num_entries-1];
  logic                              IQ_is_mem_next     [0:p_num_entries-1];
  logic                              IQ_is_mul_next     [0:p_num_entries-1];
  logic [p_prf_addr_nbits-1:0]       IQ_rs1_addr_next   [0:p_num_entries-1];
  logic                              IQ_rs1_valid_next  [0:p_num_entries-1];
  logic [p_prf_addr_nbits-1:0]       IQ_rs2_addr_next   [0:p_num_entries-1];
  logic                              IQ_rs2_valid_next  [0:p_num_entries-1];
  logic [p_prf_addr_nbits-1:0]       IQ_rd_addr_next    [0:p_num_entries-1];
  logic                              IQ_rd_valid_next   [0:p_num_entries-1];

  logic [c_num_prf-1:0] scoreboard_busy;
  logic [c_num_prf-1:0] scoreboard_busy_next;

  logic [c_cnt_nbits-1:0] num_valid_entries;
  logic [c_cnt_nbits-1:0] num_free_entries;
  logic [1:0]             input_count;
  logic [2:0]             issue_fire_count;
  logic                   entry_ready [0:p_num_entries-1];
  logic                   rs1_bypass_hit [0:p_num_entries-1];
  logic                   rs2_bypass_hit [0:p_num_entries-1];
  logic                   input_fire_lane0;
  logic                   input_fire_lane1;

  logic                   alu0_selected;
  logic                   alu1_selected;
  logic                   mul_selected;
  logic                   mem_selected;
  logic [c_idx_nbits-1:0] alu0_idx;
  logic [c_idx_nbits-1:0] alu1_idx;
  logic [c_idx_nbits-1:0] mul_idx;
  logic [c_idx_nbits-1:0] mem_idx;

  logic alu0_issue_fire;
  logic alu1_issue_fire;
  logic mul_issue_fire;
  logic mem_issue_fire;

  always_comb begin
    int i;
    num_valid_entries = '0;
    for ( i = 0; i < p_num_entries; i = i + 1 )
      if ( IQ_valid[i] )
        num_valid_entries = num_valid_entries + 1'b1;
  end

  always_comb begin
    int i;
    for ( i = 0; i < p_num_entries; i = i + 1 ) begin
      rs1_bypass_hit[i] = 1'b0;
      rs2_bypass_hit[i] = 1'b0;
      entry_ready[i]    = 1'b0;

      if ( IQ_valid[i] ) begin
        if ( IQ_rs1_valid[i] ) begin
          rs1_bypass_hit[i]
            = ( rf_wen_alu0 && ( rf_waddr_alu0 != '0 ) && ( rf_waddr_alu0 == IQ_rs1_addr[i] ) )
           || ( rf_wen_alu1 && ( rf_waddr_alu1 != '0 ) && ( rf_waddr_alu1 == IQ_rs1_addr[i] ) )
           || ( rf_wen_mul  && ( rf_waddr_mul  != '0 ) && ( rf_waddr_mul  == IQ_rs1_addr[i] ) )
           || ( rf_wen_mem  && ( rf_waddr_mem  != '0 ) && ( rf_waddr_mem  == IQ_rs1_addr[i] ) );
        end

        if ( IQ_rs2_valid[i] ) begin
          rs2_bypass_hit[i]
            = ( rf_wen_alu0 && ( rf_waddr_alu0 != '0 ) && ( rf_waddr_alu0 == IQ_rs2_addr[i] ) )
           || ( rf_wen_alu1 && ( rf_waddr_alu1 != '0 ) && ( rf_waddr_alu1 == IQ_rs2_addr[i] ) )
           || ( rf_wen_mul  && ( rf_waddr_mul  != '0 ) && ( rf_waddr_mul  == IQ_rs2_addr[i] ) )
           || ( rf_wen_mem  && ( rf_waddr_mem  != '0 ) && ( rf_waddr_mem  == IQ_rs2_addr[i] ) );
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

  // Age-priority select. CSR is a head-only exclusive barrier. Only the
  // oldest memory instruction is eligible, while younger non-memory work
  // may bypass a blocked memory instruction.
  always_comb begin : dispatch_select
    int i;
    logic stop_search;
    logic seen_mem;
    logic [1:0] select_count;

    alu0_selected = 1'b0;
    alu1_selected = 1'b0;
    mul_selected  = 1'b0;
    mem_selected  = 1'b0;
    alu0_idx       = '0;
    alu1_idx       = '0;
    mul_idx        = '0;
    mem_idx        = '0;
    stop_search    = 1'b0;
    seen_mem       = 1'b0;
    select_count   = 2'd0;

    for ( i = 0; i < p_num_entries; i = i + 1 ) begin
      if ( !stop_search && IQ_valid[i] ) begin
        if ( IQ_is_csr[i] ) begin
          stop_search = 1'b1;
          if ( ( i == 0 ) && entry_ready[i] ) begin
            alu0_selected = 1'b1;
            alu0_idx      = i[c_idx_nbits-1:0];
            select_count  = 2'd1;
          end
        end
        else if ( select_count < 2 ) begin
          if ( IQ_is_mem[i] ) begin
            if ( !seen_mem ) begin
              seen_mem = 1'b1;
              if ( entry_ready[i] && !mem_selected ) begin
                mem_selected = 1'b1;
                mem_idx      = i[c_idx_nbits-1:0];
                select_count = select_count + 1'b1;
              end
            end
          end
          else if ( IQ_is_mul[i] ) begin
            if ( entry_ready[i] && !mul_selected ) begin
              mul_selected  = 1'b1;
              mul_idx       = i[c_idx_nbits-1:0];
              select_count  = select_count + 1'b1;
            end
          end
          else if ( entry_ready[i] ) begin
            if ( !alu0_selected ) begin
              alu0_selected = 1'b1;
              alu0_idx      = i[c_idx_nbits-1:0];
              select_count  = select_count + 1'b1;
            end
            else if ( !alu1_selected ) begin
              alu1_selected = 1'b1;
              alu1_idx      = i[c_idx_nbits-1:0];
              select_count  = select_count + 1'b1;
            end
          end
        end
      end
    end
  end

  always_comb begin
    alu0_dispatch_val      = alu0_selected;
    alu0_dispatch_inst     = alu0_selected ? IQ_insts[alu0_idx]     : '0;
    alu0_dispatch_rob_tag  = alu0_selected ? IQ_rob_tag[alu0_idx]   : '0;
    alu0_dispatch_rs1_addr = alu0_selected ? IQ_rs1_addr[alu0_idx]  : '0;
    alu0_dispatch_rs2_addr = alu0_selected ? IQ_rs2_addr[alu0_idx]  : '0;
    alu0_dispatch_rd_addr  = alu0_selected ? IQ_rd_addr[alu0_idx]   : '0;
    alu0_dispatch_rd_valid = alu0_selected ? IQ_rd_valid[alu0_idx]  : 1'b0;

    alu1_dispatch_val      = alu1_selected;
    alu1_dispatch_inst     = alu1_selected ? IQ_insts[alu1_idx]     : '0;
    alu1_dispatch_rob_tag  = alu1_selected ? IQ_rob_tag[alu1_idx]   : '0;
    alu1_dispatch_rs1_addr = alu1_selected ? IQ_rs1_addr[alu1_idx]  : '0;
    alu1_dispatch_rs2_addr = alu1_selected ? IQ_rs2_addr[alu1_idx]  : '0;
    alu1_dispatch_rd_addr  = alu1_selected ? IQ_rd_addr[alu1_idx]   : '0;
    alu1_dispatch_rd_valid = alu1_selected ? IQ_rd_valid[alu1_idx]  : 1'b0;

    mul_dispatch_val      = mul_selected;
    mul_dispatch_inst     = mul_selected ? IQ_insts[mul_idx]     : '0;
    mul_dispatch_rob_tag  = mul_selected ? IQ_rob_tag[mul_idx]   : '0;
    mul_dispatch_rs1_addr = mul_selected ? IQ_rs1_addr[mul_idx]  : '0;
    mul_dispatch_rs2_addr = mul_selected ? IQ_rs2_addr[mul_idx]  : '0;
    mul_dispatch_rd_addr  = mul_selected ? IQ_rd_addr[mul_idx]   : '0;
    mul_dispatch_rd_valid = mul_selected ? IQ_rd_valid[mul_idx]  : 1'b0;

    mem_dispatch_val      = mem_selected;
    mem_dispatch_inst     = mem_selected ? IQ_insts[mem_idx]     : '0;
    mem_dispatch_rob_tag  = mem_selected ? IQ_rob_tag[mem_idx]   : '0;
    mem_dispatch_rs1_addr = mem_selected ? IQ_rs1_addr[mem_idx]  : '0;
    mem_dispatch_rs2_addr = mem_selected ? IQ_rs2_addr[mem_idx]  : '0;
    mem_dispatch_rd_addr  = mem_selected ? IQ_rd_addr[mem_idx]   : '0;
    mem_dispatch_rd_valid = mem_selected ? IQ_rd_valid[mem_idx]  : 1'b0;
  end

  assign alu0_issue_fire = alu0_dispatch_val && alu0_dispatch_rdy;
  assign alu1_issue_fire = alu1_dispatch_val && alu1_dispatch_rdy;
  assign mul_issue_fire  = mul_dispatch_val  && mul_dispatch_rdy;
  assign mem_issue_fire  = mem_dispatch_val  && mem_dispatch_rdy;

  assign issue_fire_count = { 2'b0, alu0_issue_fire }
                          + { 2'b0, alu1_issue_fire }
                          + { 2'b0, mul_issue_fire  }
                          + { 2'b0, mem_issue_fire  };

  assign input_count = { 1'b0, input_val_lane0 }
                     + { 1'b0, input_val_lane1 };
  assign num_free_entries = p_num_entries - num_valid_entries
                          + issue_fire_count;
  assign input_rdy = ( input_count <= num_free_entries );
  assign input_fire_lane0 = input_val_lane0 && input_rdy;
  assign input_fire_lane1 = input_val_lane1 && input_rdy;

  always_comb begin
    int i, r, w;

    for ( i = 0; i < p_num_entries; i = i + 1 ) begin
      IQ_valid_next[i]     = 1'b0;
      IQ_insts_next[i]     = '0;
      IQ_rob_tag_next[i]   = '0;
      IQ_is_csr_next[i]    = 1'b0;
      IQ_is_mem_next[i]    = 1'b0;
      IQ_is_mul_next[i]    = 1'b0;
      IQ_rs1_addr_next[i]  = '0;
      IQ_rs1_valid_next[i] = 1'b0;
      IQ_rs2_addr_next[i]  = '0;
      IQ_rs2_valid_next[i] = 1'b0;
      IQ_rd_addr_next[i]   = '0;
      IQ_rd_valid_next[i]  = 1'b0;
    end

    w = 0;
    for ( r = 0; r < p_num_entries; r = r + 1 ) begin
      if ( IQ_valid[r]
        && !( alu0_issue_fire && ( r == alu0_idx ) )
        && !( alu1_issue_fire && ( r == alu1_idx ) )
        && !( mul_issue_fire  && ( r == mul_idx  ) )
        && !( mem_issue_fire  && ( r == mem_idx  ) ) ) begin
        IQ_valid_next[w]     = IQ_valid[r];
        IQ_insts_next[w]     = IQ_insts[r];
        IQ_rob_tag_next[w]   = IQ_rob_tag[r];
        IQ_is_csr_next[w]    = IQ_is_csr[r];
        IQ_is_mem_next[w]    = IQ_is_mem[r];
        IQ_is_mul_next[w]    = IQ_is_mul[r];
        IQ_rs1_addr_next[w]  = IQ_rs1_addr[r];
        IQ_rs1_valid_next[w] = IQ_rs1_valid[r];
        IQ_rs2_addr_next[w]  = IQ_rs2_addr[r];
        IQ_rs2_valid_next[w] = IQ_rs2_valid[r];
        IQ_rd_addr_next[w]   = IQ_rd_addr[r];
        IQ_rd_valid_next[w]  = IQ_rd_valid[r];
        w = w + 1;
      end
    end

    if ( input_fire_lane0 && ( w < p_num_entries ) ) begin
      IQ_valid_next[w]     = 1'b1;
      IQ_insts_next[w]     = input_inst_lane0;
      IQ_rob_tag_next[w]   = input_rob_tag_lane0;
      IQ_is_csr_next[w]    = input_is_csr_lane0;
      IQ_is_mem_next[w]    = input_is_mem_lane0;
      IQ_is_mul_next[w]    = input_is_mul_lane0;
      IQ_rs1_addr_next[w]  = input_rs1_addr_lane0;
      IQ_rs1_valid_next[w] = input_rs1_valid_lane0;
      IQ_rs2_addr_next[w]  = input_rs2_addr_lane0;
      IQ_rs2_valid_next[w] = input_rs2_valid_lane0;
      IQ_rd_addr_next[w]   = input_rd_addr_lane0;
      IQ_rd_valid_next[w]  = input_rd_valid_lane0;
      w = w + 1;
    end

    if ( input_fire_lane1 && ( w < p_num_entries ) ) begin
      IQ_valid_next[w]     = 1'b1;
      IQ_insts_next[w]     = input_inst_lane1;
      IQ_rob_tag_next[w]   = input_rob_tag_lane1;
      IQ_is_csr_next[w]    = input_is_csr_lane1;
      IQ_is_mem_next[w]    = input_is_mem_lane1;
      IQ_is_mul_next[w]    = input_is_mul_lane1;
      IQ_rs1_addr_next[w]  = input_rs1_addr_lane1;
      IQ_rs1_valid_next[w] = input_rs1_valid_lane1;
      IQ_rs2_addr_next[w]  = input_rs2_addr_lane1;
      IQ_rs2_valid_next[w] = input_rs2_valid_lane1;
      IQ_rd_addr_next[w]   = input_rd_addr_lane1;
      IQ_rd_valid_next[w]  = input_rd_valid_lane1;
    end

    scoreboard_busy_next = scoreboard_busy;

    if ( rf_wen_alu0 && ( rf_waddr_alu0 != '0 ) )
      scoreboard_busy_next[rf_waddr_alu0] = 1'b0;
    if ( rf_wen_alu1 && ( rf_waddr_alu1 != '0 ) )
      scoreboard_busy_next[rf_waddr_alu1] = 1'b0;
    if ( rf_wen_mul && ( rf_waddr_mul != '0 ) )
      scoreboard_busy_next[rf_waddr_mul] = 1'b0;
    if ( rf_wen_mem && ( rf_waddr_mem != '0 ) )
      scoreboard_busy_next[rf_waddr_mem] = 1'b0;

    if ( input_fire_lane0 && input_rd_valid_lane0 && ( input_rd_addr_lane0 != '0 ) )
      scoreboard_busy_next[input_rd_addr_lane0] = 1'b1;
    if ( input_fire_lane1 && input_rd_valid_lane1 && ( input_rd_addr_lane1 != '0 ) )
      scoreboard_busy_next[input_rd_addr_lane1] = 1'b1;

    scoreboard_busy_next[0] = 1'b0;
  end

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
        IQ_is_mul[i]    <= 1'b0;
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
        IQ_is_mul[i]    <= IQ_is_mul_next[i];
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
