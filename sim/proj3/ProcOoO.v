`ifndef PROJ3_PROCOOO_V
`define PROJ3_PROCOOO_V

`include "vc/mem-msgs.v"
`include "vc/xcel-msgs.v"
`include "vc/queues.v"
`include "vc/trace.v"

`include "proj3/tinyrv2_encoding.v"
`include "proj3/ProcOoOCtrl.v"
`include "proj3/ProcOoODpath.v"
`include "proj3/DropUnit.v"
`include "proj3/ProcOoO_linetrace_helper.v"

module proj3_ProcOoO
#(
  parameter p_num_cores = 1
)
(
  input  logic         clk,
  input  logic         reset,

  input  logic [31:0]  mngr2proc_msg,
  input  logic         mngr2proc_val,
  output logic         mngr2proc_rdy,

  output logic [31:0]  proc2mngr_msg,
  output logic         proc2mngr_val,
  input  logic         proc2mngr_rdy,

  output xcel_req_t    xcel_reqstream_msg,
  output logic         xcel_reqstream_val,
  input  logic         xcel_reqstream_rdy,

  input  xcel_resp_t   xcel_respstream_msg,
  input  logic         xcel_respstream_val,
  output logic         xcel_respstream_rdy,

  output mem_req_8B_t  imem_reqstream_msg,
  output logic         imem_reqstream_val,
  input  logic         imem_reqstream_rdy,

  input  mem_resp_8B_t imem_respstream_msg,
  input  logic         imem_respstream_val,
  output logic         imem_respstream_rdy,

  output mem_req_4B_t  dmem_reqstream_msg,
  output logic         dmem_reqstream_val,
  input  logic         dmem_reqstream_rdy,

  input  mem_resp_4B_t dmem_respstream_msg,
  input  logic         dmem_respstream_val,
  output logic         dmem_respstream_rdy,

  input  logic [31:0]  core_id,
  output logic         commit_inst,
  output logic         stats_en
);

  //======================================================================
  // Instruction Memory Request Bypass Queue
  //======================================================================

  logic [1:0]  imem_queue_num_free_entries;
  mem_req_8B_t imem_reqstream_enq_msg;
  logic        imem_reqstream_enq_val;
  logic        imem_reqstream_enq_rdy;
  logic [31:0] imem_req_addr_lane0;
  logic [31:0] imem_req_addr_lane1;

  assign imem_reqstream_enq_msg.type_  = `VC_MEM_REQ_MSG_TYPE_READ;
  assign imem_reqstream_enq_msg.opaque = 8'b0;
  assign imem_reqstream_enq_msg.addr   = imem_req_addr_lane0;
  assign imem_reqstream_enq_msg.len    = 3'd0;
  assign imem_reqstream_enq_msg.data   = 64'd0;

  mem_req_8B_t imem_reqstream_msg_4state_fix;
  vc_Queue#(`VC_QUEUE_BYPASS,$bits(mem_req_8B_t),2) imem_queue
  (
    .clk              (clk),
    .reset            (reset),
    .num_free_entries (imem_queue_num_free_entries),

    .enq_msg          (imem_reqstream_enq_msg),
    .enq_val          (imem_reqstream_enq_val),
    .enq_rdy          (imem_reqstream_enq_rdy),

    .deq_msg          (imem_reqstream_msg_4state_fix),
    .deq_val          (imem_reqstream_val),
    .deq_rdy          (imem_reqstream_rdy)
  );
  
  assign imem_reqstream_msg
    = imem_reqstream_msg_4state_fix & {$bits(mem_req_8B_t){imem_reqstream_val}};

  //======================================================================
  // Imem Drop Unit
  //======================================================================

  logic         imem_respstream_drop;
  mem_resp_8B_t imem_respstream_drop_msg;
  logic         imem_respstream_drop_val;
  logic         imem_respstream_drop_rdy;
  logic [31:0]  imem_resp_inst_lane0;
  logic [31:0]  imem_resp_inst_lane1;
  
  proj3_DropUnit #($bits(mem_resp_8B_t)) imem_respstream_drop_unit
  (
    .clk         (clk),
    .reset       (reset),

    .drop        (imem_respstream_drop),

    .istream_msg (imem_respstream_msg),
    .istream_val (imem_respstream_val),
    .istream_rdy (imem_respstream_rdy),

    .ostream_msg (imem_respstream_drop_msg),
    .ostream_val (imem_respstream_drop_val),
    .ostream_rdy (imem_respstream_drop_rdy)
  );

  assign imem_resp_inst_lane0 = imem_respstream_drop_msg.data[31:0];
  assign imem_resp_inst_lane1 = imem_respstream_drop_msg.data[63:32];
  
  //======================================================================
  // Data Memory Request Bypass Queue
  //======================================================================

  logic        dmem_queue_num_free_entries;
  mem_req_4B_t dmem_reqstream_enq_msg;
  logic        dmem_reqstream_enq_val;
  logic        dmem_reqstream_enq_rdy;
  logic [2:0]  dmem_reqstream_enq_msg_type;
  logic [31:0] dmem_reqstream_enq_msg_addr;
  logic [31:0] dmem_reqstream_enq_msg_data;

  assign dmem_reqstream_enq_msg.type_  = dmem_reqstream_enq_msg_type;
  assign dmem_reqstream_enq_msg.opaque = 8'b0;
  assign dmem_reqstream_enq_msg.addr   = dmem_reqstream_enq_msg_addr;
  assign dmem_reqstream_enq_msg.len    = 2'd0;
  assign dmem_reqstream_enq_msg.data   = dmem_reqstream_enq_msg_data;
  
  mem_req_4B_t dmem_reqstream_msg_4state_fix;

  vc_Queue#(`VC_QUEUE_BYPASS,$bits(mem_req_4B_t),1) dmem_queue
  (
    .clk              (clk),
    .reset            (reset),
    .num_free_entries (dmem_queue_num_free_entries),

    .enq_msg          (dmem_reqstream_enq_msg),
    .enq_val          (dmem_reqstream_enq_val),
    .enq_rdy          (dmem_reqstream_enq_rdy),

    .deq_msg          (dmem_reqstream_msg_4state_fix),
    .deq_val          (dmem_reqstream_val),
    .deq_rdy          (dmem_reqstream_rdy)
  );
  
  always_comb begin
    dmem_reqstream_msg = '0;
    if ( dmem_reqstream_val ) begin
      dmem_reqstream_msg = dmem_reqstream_msg_4state_fix;
      if ( dmem_reqstream_msg.type_ == `VC_MEM_REQ_MSG_TYPE_READ )
        dmem_reqstream_msg.data = '0;
    end
  end

  //======================================================================
  // proc2mngr Bypass Queue
  //======================================================================

  logic        proc2mngr_queue_num_free_entries;
  logic [31:0] proc2mngr_enq_msg;
  logic        proc2mngr_enq_val;
  logic        proc2mngr_enq_rdy;

  logic [31:0] proc2mngr_msg_4state_fix;
  
  vc_Queue#(`VC_QUEUE_BYPASS,32,1) proc2mngr_queue
  (
    .clk              (clk),
    .reset            (reset),
    .num_free_entries (proc2mngr_queue_num_free_entries),

    .enq_msg          (proc2mngr_enq_msg),
    .enq_val          (proc2mngr_enq_val),
    .enq_rdy          (proc2mngr_enq_rdy),

    .deq_msg          (proc2mngr_msg_4state_fix),
    .deq_val          (proc2mngr_val),
    .deq_rdy          (proc2mngr_rdy)
  );
  
  assign proc2mngr_msg = proc2mngr_msg_4state_fix & {32{proc2mngr_val}};

  //======================================================================
  // xcelreq Bypass Queue
  //======================================================================

  logic      xcel_queue_num_free_entries;
  xcel_req_t xcel_reqstream_enq_msg;
  logic      xcel_reqstream_enq_val;
  logic      xcel_reqstream_enq_rdy;

  xcel_req_t xcel_reqstream_msg_4state_fix;
  
  vc_Queue#(`VC_QUEUE_BYPASS,$bits(xcel_req_t),1) xcel_queue
  (
    .clk              (clk),
    .reset            (reset),
    .num_free_entries (xcel_queue_num_free_entries),

    .enq_msg          (xcel_reqstream_enq_msg),
    .enq_val          (xcel_reqstream_enq_val),
    .enq_rdy          (xcel_reqstream_enq_rdy),

    .deq_msg          (xcel_reqstream_msg_4state_fix),
    .deq_val          (xcel_reqstream_val),
    .deq_rdy          (xcel_reqstream_rdy)
  );
  
  assign xcel_reqstream_msg = xcel_reqstream_msg_4state_fix & {$bits(xcel_req_t){xcel_reqstream_val}};

  //======================================================================
  // Control/Status Signals
  //======================================================================

  // ctrl -> dpath
  logic        reg_en_F;
  logic        reg_en_D;
  logic        iq_input_val_D;
  logic        iq_dispatch_rdy;

  // ROB allocation control (ctrl -> dpath)
  logic        rob_alloc_req_D;
  logic [2:0]  imm_type_I;
  logic [1:0]  op2_sel_I;
  logic [1:0]  csrr_sel_I;
  logic        alu_issue_fire_I;
  logic        mul_issue_fire_I;
  logic        mem_issue_fire_I;
  logic        is_sw_I;

  logic [3:0]  alu_fn_X;

  logic        imul_ostream_rdy_W;

  logic [4:0]  rf_waddr_W;
  logic        rf_wen_W;

  logic        rob_fill_val_W;
  logic        rob_fill_val_Y3;

  logic [4:0]  rf_waddr_Y3;
  logic        rf_wen_Y3;

  logic        stats_en_wen_W;
  
  // dpath -> ctrl
  logic [31:0] inst_D_lane0;
  logic [31:0] inst_D_lane1;
  logic        iq_input_rdy_D;
  logic        iq_dispatch_val;
  logic [31:0] iq_dispatch_inst;
  
  // ROB / Rename status feedback
  logic        rob_alloc_rdy_D;
  logic        rob_full_D;
  logic        rename_rdy_D;

  // ROB commit signal
  logic        commit_val_C;
  logic        imul_istream_rdy_I;
  logic        imul_ostream_val_W;
  logic        load_istream_rdy_I;

  // Dummy ctrl-side dmem val/rdy wires. The LoadUnit in dpath drives the
  // actual dmem request/response handshake.
  logic [2:0]  ctrl_dmem_reqstream_msg_type;
  logic        ctrl_dmem_reqstream_val;
  logic        ctrl_dmem_respstream_rdy;
  
  //======================================================================
  // Control Unit
  //======================================================================

  proj3_ProcCtrl ctrl
  (
    .clk                     (clk),
    .reset                   (reset),

    // Instruction Memory Port
    .imem_reqstream_val      (imem_reqstream_enq_val),
    .imem_reqstream_rdy      (imem_reqstream_enq_rdy),
    .imem_respstream_val     (imem_respstream_drop_val),
    .imem_respstream_rdy     (imem_respstream_drop_rdy),
    .imem_respstream_drop    (imem_respstream_drop),

    // Data Memory Port
    .dmem_reqstream_msg_type (ctrl_dmem_reqstream_msg_type),
    .dmem_reqstream_val      (ctrl_dmem_reqstream_val),
    .dmem_reqstream_rdy      (dmem_reqstream_enq_rdy),
    .dmem_respstream_val     (dmem_respstream_val),
    .dmem_respstream_rdy     (ctrl_dmem_respstream_rdy),

    // mngr communication ports
    .mngr2proc_val           (mngr2proc_val),
    .mngr2proc_rdy           (mngr2proc_rdy),
    .proc2mngr_val           (proc2mngr_enq_val),
    .proc2mngr_rdy           (proc2mngr_enq_rdy),

    // xcel ports
    .xcel_reqstream_val      (xcel_reqstream_enq_val),
    .xcel_reqstream_rdy      (xcel_reqstream_enq_rdy),
    .xcel_reqstream_msg_type (xcel_reqstream_enq_msg.type_),
    .xcel_respstream_val     (xcel_respstream_val),
    .xcel_respstream_rdy     (xcel_respstream_rdy),

    // ctrl -> dpath
    .reg_en_F                (reg_en_F),
    .reg_en_D                (reg_en_D),
    .iq_input_val_D          (iq_input_val_D),
    .iq_dispatch_rdy         (iq_dispatch_rdy),
    .rob_alloc_req_D         (rob_alloc_req_D),

    .imm_type_I              (imm_type_I),
    .op2_sel_I               (op2_sel_I),
    .csrr_sel_I              (csrr_sel_I),
    .alu_issue_fire_I        (alu_issue_fire_I),
    .mul_issue_fire_I        (mul_issue_fire_I),
    .mem_issue_fire_I        (mem_issue_fire_I),
    .is_sw_I                 (is_sw_I),

    .alu_fn_X                (alu_fn_X),

    .rf_waddr_W              (rf_waddr_W),
    .rf_wen_W                (rf_wen_W),
    .rf_waddr_Y3             (rf_waddr_Y3),
    .rf_wen_Y3               (rf_wen_Y3),
    .rob_fill_val_W          (rob_fill_val_W),
    .rob_fill_val_Y3         (rob_fill_val_Y3),

    .imul_ostream_rdy_W      (imul_ostream_rdy_W),
    .stats_en_wen_W          (stats_en_wen_W),

    // dpath -> ctrl
    .inst_D_lane0            (inst_D_lane0),
    .inst_D_lane1            (inst_D_lane1),
    .iq_input_rdy_D          (iq_input_rdy_D),
    .rob_alloc_rdy_D         (rob_alloc_rdy_D),
    .rob_full_D              (rob_full_D),
    .rename_rdy_D            (rename_rdy_D),

    .iq_dispatch_val         (iq_dispatch_val),
    .iq_dispatch_inst        (iq_dispatch_inst),
    .imul_istream_rdy_I      (imul_istream_rdy_I),
    .imul_ostream_val_W      (imul_ostream_val_W),
    .load_istream_rdy_I      (load_istream_rdy_I),

    .commit_val_C            (commit_val_C),
    .commit_inst             (commit_inst)
  );

  //======================================================================
  // Datapath
  //======================================================================

  proj3_ProcDpath
  #(
    .p_num_cores (p_num_cores)
  )
  dpath
  (
    .clk                      (clk),
    .reset                    (reset),

    // Instruction Memory Port
    .imem_req_addr_lane0     (imem_req_addr_lane0),
    .imem_req_addr_lane1     (imem_req_addr_lane1),
    .imem_resp_inst_lane0    (imem_resp_inst_lane0),
    .imem_resp_inst_lane1    (imem_resp_inst_lane1),

    // Data Memory Port
    .dmem_reqstream_val       (dmem_reqstream_enq_val),
    .dmem_reqstream_rdy       (dmem_reqstream_enq_rdy),
    .dmem_reqstream_msg_type  (dmem_reqstream_enq_msg_type),
    .dmem_reqstream_msg_addr  (dmem_reqstream_enq_msg_addr),
    .dmem_reqstream_msg_data  (dmem_reqstream_enq_msg_data),

    .dmem_respstream_val      (dmem_respstream_val),
    .dmem_respstream_rdy      (dmem_respstream_rdy),
    .dmem_respstream_msg_data (dmem_respstream_msg.data),

    // mngr communication ports
    .mngr2proc_data           (mngr2proc_msg),
    .proc2mngr_data           (proc2mngr_enq_msg),

    // xcel communication ports
    .xcel_reqstream_msg_addr  (xcel_reqstream_enq_msg.addr),
    .xcel_reqstream_msg_data  (xcel_reqstream_enq_msg.data),
    .xcel_respstream_msg_data (xcel_respstream_msg.data),

    // ctrl -> dpath
    .reg_en_F                 (reg_en_F),
    .reg_en_D                 (reg_en_D),
    .iq_input_val_D           (iq_input_val_D),
    .iq_dispatch_rdy          (iq_dispatch_rdy),
    .rob_alloc_req_D          (rob_alloc_req_D),

    .imm_type_I               (imm_type_I),
    .op2_sel_I                (op2_sel_I),
    .csrr_sel_I               (csrr_sel_I),
    .alu_issue_fire_I         (alu_issue_fire_I),
    .mul_issue_fire_I         (mul_issue_fire_I),
    .mem_issue_fire_I         (mem_issue_fire_I),
    .is_sw_I                  (is_sw_I),

    .alu_fn_X                 (alu_fn_X),

    .rf_waddr_W               (rf_waddr_W),
    .rf_wen_W                 (rf_wen_W),
    .rf_waddr_Y3              (rf_waddr_Y3),
    .rf_wen_Y3                (rf_wen_Y3),
    .rob_fill_val_W           (rob_fill_val_W),
    .rob_fill_val_Y3          (rob_fill_val_Y3),

    .imul_ostream_rdy_W       (imul_ostream_rdy_W),
    .stats_en_wen_W           (stats_en_wen_W),

    // dpath -> ctrl
    .inst_D_lane0             (inst_D_lane0),
    .inst_D_lane1             (inst_D_lane1),
    .iq_input_rdy_D           (iq_input_rdy_D),
    .iq_dispatch_val          (iq_dispatch_val),
    .iq_dispatch_inst         (iq_dispatch_inst),

    .rob_alloc_rdy_D          (rob_alloc_rdy_D),
    .rob_full_D               (rob_full_D),
    .rename_rdy_D             (rename_rdy_D),
    .commit_val_C             (commit_val_C),

    .imul_istream_rdy_I       (imul_istream_rdy_I),
    .imul_ostream_val_W       (imul_ostream_val_W),
    .load_istream_rdy_I       (load_istream_rdy_I),

    // misc
    .core_id                  (core_id),
    .stats_en                 (stats_en)
  );

  //======================================================================
  // Line tracing
  //======================================================================

  `ifndef SYNTHESIS

    proj3_tinyrv2_encoding_InstTasks tinyrv2();
    proj3_OoO_linetrace_InstTasks ooo_trace();
    logic [`VC_TRACE_NBITS-1:0] str;
    
    `VC_TRACE_BEGIN
    begin

      // 1. F stage (Fetch)

      if ( !ctrl.val_F )
        vc_trace.append_chars( trace_str, " ", 8 );
      else if ( ctrl.stall_F ) begin
        vc_trace.append_str( trace_str, "#" );
        vc_trace.append_chars( trace_str, " ", 7 );
      end
      else begin
        $sformat( str, "%x", dpath.pc_F );
        vc_trace.append_str( trace_str, str );
      end
      vc_trace.append_str( trace_str, "|" );
      
      // 2. D stage (Decode / Rename / Allocate)

      if ( !ctrl.val_D )
        vc_trace.append_chars( trace_str, " ", 51 );
      else if ( ctrl.stall_D ) begin
        vc_trace.append_str( trace_str, "#" );
        vc_trace.append_chars( trace_str, " ", 50 );
      end
      else begin
        $sformat( str, "%0d:", dpath.alloc_tag_D_lane0 );
        vc_trace.append_str( trace_str, str );
        vc_trace.append_str( trace_str, {3896'b0, tinyrv2.disasm( inst_D_lane0 )} );
        vc_trace.append_str( trace_str, "," );
        $sformat( str, "%0d:", dpath.alloc_tag_D_lane1 );
        vc_trace.append_str( trace_str, str );
        vc_trace.append_str( trace_str, {3896'b0, tinyrv2.disasm( inst_D_lane1 )} );
      end
        
      vc_trace.append_str( trace_str, "|" );

      // 3. IS stage (Issue / IQ Dispatch)

      if ( !iq_dispatch_val )
        vc_trace.append_chars( trace_str, " ", 25 );
      else begin
        $sformat( str, "%0d:", dpath.iq_dispatch_rob_tag );
        vc_trace.append_str( trace_str, str );
        vc_trace.append_str( trace_str,
          {3896'b0, ooo_trace.disasm_phy(
            iq_dispatch_inst,
            dpath.iq_dispatch_rs1_addr,
            dpath.iq_dispatch_rs2_addr,
            dpath.iq_dispatch_rd_addr
          )}
        );
      end
      vc_trace.append_str( trace_str, "|" );
      
      // 4. WB event (writeback to PRF from ALU or MUL)

      if ( dpath.rf_wen_W || dpath.rf_wen_Y3 || dpath.load_prf_wen )
        vc_trace.append_str( trace_str,
          {3888'b0, ooo_trace.wb_preg_trace(
            dpath.rf_wen_W,
            dpath.rd_paddr_X,
            dpath.rf_wen_Y3,
            dpath.rd_paddr_Y3,
            dpath.load_prf_wen,
            dpath.load_ostream_rd_paddr
          )}
        );
      else
        vc_trace.append_chars( trace_str, " ", 22 );
        
      vc_trace.append_str( trace_str, "|" );

      // 5. C stage (Commit)

      if ( commit_inst ) begin
        vc_trace.append_str( trace_str,
          {3736'b0, ooo_trace.commit_trace(
            dpath.commit_has_rd,
            dpath.rob.head,
            dpath.commit_rd_addr,
            dpath.commit_rd_paddr_old_C
          )}
        );
      end
      else begin
        vc_trace.append_chars( trace_str, " ", 20 );
      end

    end
    `VC_TRACE_END

    vc_MemReqMsg4BTrace dmem_reqstream_trace
    (
      .clk   (clk),
      .reset (reset),
      .val   (dmem_reqstream_val),
      .rdy   (dmem_reqstream_rdy),
      .msg   (dmem_reqstream_msg)
    );

    vc_MemRespMsg4BTrace dmem_respstream_trace
    (
      .clk   (clk),
      .reset (reset),
      .val   (dmem_respstream_val),
      .rdy   (dmem_respstream_rdy),
      .msg   (dmem_respstream_msg)
    );

  `endif /* SYNTHESIS */

endmodule

`endif
