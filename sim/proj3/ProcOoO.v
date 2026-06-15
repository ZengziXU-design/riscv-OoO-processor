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
  output logic [1:0]   commit_count,
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

  // ROB allocation control (ctrl -> dpath)
  logic        rob_alloc_req_D;
  logic        alu0_dispatch_rdy;
  logic        alu1_dispatch_rdy;
  logic        mul_dispatch_rdy;
  logic        mem_dispatch_rdy;

  logic [2:0]  alu0_imm_type_I;
  logic [1:0]  alu0_op2_sel_I;
  logic [1:0]  alu0_csrr_sel_I;
  logic        alu0_issue_fire_I;

  logic [2:0]  alu1_imm_type_I;
  logic [1:0]  alu1_op2_sel_I;
  logic        alu1_issue_fire_I;

  logic        mul_issue_fire_I;
  logic        mem_issue_fire_I;
  logic [2:0]  mem_imm_type_I;
  logic        mem_is_sw_I;

  logic [3:0]  alu0_fn_X;
  logic [3:0]  alu1_fn_X;

  logic        imul_ostream_rdy_W;

  logic        rf_wen_alu0_W;
  logic        rf_wen_alu1_W;
  logic        rf_wen_mul_Y3;
  logic        rob_fill_val_alu0_W;
  logic        rob_fill_val_alu1_W;
  logic        rob_fill_val_mul_Y3;

  logic        stats_en_wen_W;
  
  // dpath -> ctrl
  logic [31:0] inst_D_lane0;
  logic [31:0] inst_D_lane1;
  logic        iq_input_rdy_D;
  logic        alu0_dispatch_val;
  logic [31:0] alu0_dispatch_inst;
  logic        alu1_dispatch_val;
  logic [31:0] alu1_dispatch_inst;
  logic        mul_dispatch_val;
  logic [31:0] mul_dispatch_inst;
  logic        mem_dispatch_val;
  logic [31:0] mem_dispatch_inst;
  
  // ROB / Rename status feedback
  logic        rob_alloc_rdy_D;
  logic        rob_full_D;
  logic        rename_rdy_D;

  // ROB commit signal
  logic        commit_val_C_lane0;
  logic        commit_val_C_lane1;
  logic        imul_istream_rdy_I;
  logic        imul_ostream_val_W;
  logic        load_istream_rdy_I;

  assign commit_count = { 1'b0, commit_val_C_lane0 }
                      + { 1'b0, commit_val_C_lane1 };

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
    .rob_alloc_req_D         (rob_alloc_req_D),

    .alu0_dispatch_rdy       (alu0_dispatch_rdy),
    .alu1_dispatch_rdy       (alu1_dispatch_rdy),
    .mul_dispatch_rdy        (mul_dispatch_rdy),
    .mem_dispatch_rdy        (mem_dispatch_rdy),

    .alu0_imm_type_I         (alu0_imm_type_I),
    .alu0_op2_sel_I          (alu0_op2_sel_I),
    .alu0_csrr_sel_I         (alu0_csrr_sel_I),
    .alu0_issue_fire_I       (alu0_issue_fire_I),

    .alu1_imm_type_I         (alu1_imm_type_I),
    .alu1_op2_sel_I          (alu1_op2_sel_I),
    .alu1_issue_fire_I       (alu1_issue_fire_I),

    .mul_issue_fire_I        (mul_issue_fire_I),
    .mem_issue_fire_I        (mem_issue_fire_I),
    .mem_imm_type_I          (mem_imm_type_I),
    .mem_is_sw_I             (mem_is_sw_I),

    .alu0_fn_X               (alu0_fn_X),
    .alu1_fn_X               (alu1_fn_X),

    .rf_wen_alu0_W           (rf_wen_alu0_W),
    .rf_wen_alu1_W           (rf_wen_alu1_W),
    .rf_wen_mul_Y3           (rf_wen_mul_Y3),
    .rob_fill_val_alu0_W     (rob_fill_val_alu0_W),
    .rob_fill_val_alu1_W     (rob_fill_val_alu1_W),
    .rob_fill_val_mul_Y3     (rob_fill_val_mul_Y3),

    .imul_ostream_rdy_W      (imul_ostream_rdy_W),
    .stats_en_wen_W          (stats_en_wen_W),

    // dpath -> ctrl
    .inst_D_lane0            (inst_D_lane0),
    .inst_D_lane1            (inst_D_lane1),
    .iq_input_rdy_D          (iq_input_rdy_D),
    .rob_alloc_rdy_D         (rob_alloc_rdy_D),
    .rob_full_D              (rob_full_D),
    .rename_rdy_D            (rename_rdy_D),

    .alu0_dispatch_val       (alu0_dispatch_val),
    .alu0_dispatch_inst      (alu0_dispatch_inst),
    .alu1_dispatch_val       (alu1_dispatch_val),
    .alu1_dispatch_inst      (alu1_dispatch_inst),
    .mul_dispatch_val        (mul_dispatch_val),
    .mul_dispatch_inst       (mul_dispatch_inst),
    .mem_dispatch_val        (mem_dispatch_val),
    .mem_dispatch_inst       (mem_dispatch_inst),
    .imul_istream_rdy_I      (imul_istream_rdy_I),
    .imul_ostream_val_W      (imul_ostream_val_W),
    .load_istream_rdy_I      (load_istream_rdy_I),

    .commit_val_C_lane0      (commit_val_C_lane0),
    .commit_val_C_lane1      (commit_val_C_lane1),
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
    .rob_alloc_req_D          (rob_alloc_req_D),

    .alu0_dispatch_rdy        (alu0_dispatch_rdy),
    .alu1_dispatch_rdy        (alu1_dispatch_rdy),
    .mul_dispatch_rdy         (mul_dispatch_rdy),
    .mem_dispatch_rdy         (mem_dispatch_rdy),

    .alu0_imm_type_I          (alu0_imm_type_I),
    .alu0_op2_sel_I           (alu0_op2_sel_I),
    .alu0_csrr_sel_I          (alu0_csrr_sel_I),
    .alu0_issue_fire_I        (alu0_issue_fire_I),

    .alu1_imm_type_I          (alu1_imm_type_I),
    .alu1_op2_sel_I           (alu1_op2_sel_I),
    .alu1_issue_fire_I        (alu1_issue_fire_I),

    .mul_issue_fire_I         (mul_issue_fire_I),
    .mem_issue_fire_I         (mem_issue_fire_I),
    .mem_imm_type_I           (mem_imm_type_I),
    .mem_is_sw_I              (mem_is_sw_I),

    .alu0_fn_X                (alu0_fn_X),
    .alu1_fn_X                (alu1_fn_X),

    .rf_wen_alu0_W            (rf_wen_alu0_W),
    .rf_wen_alu1_W            (rf_wen_alu1_W),
    .rf_wen_mul_Y3            (rf_wen_mul_Y3),
    .rob_fill_val_alu0_W      (rob_fill_val_alu0_W),
    .rob_fill_val_alu1_W      (rob_fill_val_alu1_W),
    .rob_fill_val_mul_Y3      (rob_fill_val_mul_Y3),

    .imul_ostream_rdy_W       (imul_ostream_rdy_W),
    .stats_en_wen_W           (stats_en_wen_W),

    // dpath -> ctrl
    .inst_D_lane0             (inst_D_lane0),
    .inst_D_lane1             (inst_D_lane1),
    .iq_input_rdy_D           (iq_input_rdy_D),
    .alu0_dispatch_val        (alu0_dispatch_val),
    .alu0_dispatch_inst       (alu0_dispatch_inst),
    .alu1_dispatch_val        (alu1_dispatch_val),
    .alu1_dispatch_inst       (alu1_dispatch_inst),
    .mul_dispatch_val         (mul_dispatch_val),
    .mul_dispatch_inst        (mul_dispatch_inst),
    .mem_dispatch_val         (mem_dispatch_val),
    .mem_dispatch_inst        (mem_dispatch_inst),
    .rob_alloc_rdy_D          (rob_alloc_rdy_D),
    .rob_full_D               (rob_full_D),
    .rename_rdy_D             (rename_rdy_D),
    .commit_val_C_lane0       (commit_val_C_lane0),
    .commit_val_C_lane1       (commit_val_C_lane1),

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
    logic issue_fire_trace_alu0;
    logic issue_fire_trace_alu1;
    logic issue_fire_trace_mul;
    logic issue_fire_trace_mem;
    logic [2:0] issue_trace_count;

    assign issue_fire_trace_alu0 = alu0_dispatch_val && alu0_dispatch_rdy;
    assign issue_fire_trace_alu1 = alu1_dispatch_val && alu1_dispatch_rdy;
    assign issue_fire_trace_mul  = mul_dispatch_val  && mul_dispatch_rdy;
    assign issue_fire_trace_mem  = mem_dispatch_val  && mem_dispatch_rdy;

    assign issue_trace_count = { 2'b0, issue_fire_trace_alu0 }
                             + { 2'b0, issue_fire_trace_alu1 }
                             + { 2'b0, issue_fire_trace_mul  }
                             + { 2'b0, issue_fire_trace_mem  };
    
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
        $sformat( str, "%08x", dpath.pc_F );
        vc_trace.append_str( trace_str, str );
      end
      vc_trace.append_str( trace_str, "|" );
      
      // 2. D stage (Decode / Rename / Allocate)

      if ( !ctrl.val_D )
        vc_trace.append_chars( trace_str, " ", 53 );
      else if ( ctrl.stall_D ) begin
        vc_trace.append_str( trace_str, "#" );
        vc_trace.append_chars( trace_str, " ", 52 );
      end
      else begin
        $sformat( str, "%02d:", dpath.alloc_tag_D_lane0 );
        vc_trace.append_str( trace_str, str );
        vc_trace.append_str( trace_str, {3896'b0, tinyrv2.disasm( inst_D_lane0 )} );
        vc_trace.append_str( trace_str, "," );
        $sformat( str, "%02d:", dpath.alloc_tag_D_lane1 );
        vc_trace.append_str( trace_str, str );
        vc_trace.append_str( trace_str, {3896'b0, tinyrv2.disasm( inst_D_lane1 )} );
      end
        
      vc_trace.append_str( trace_str, "|" );

      // 3. IS stage (Issue / IQ Dispatch)

      if ( issue_trace_count == 0 )
        vc_trace.append_chars( trace_str, " ", 63 );
      else begin
        vc_trace.append_str( trace_str,
          {3592'b0, ooo_trace.dual_issue_trace(
            issue_fire_trace_alu0,
            dpath.alu0_dispatch_rob_tag,
            alu0_dispatch_inst,
            dpath.alu0_dispatch_rs1_addr,
            dpath.alu0_dispatch_rs2_addr,
            dpath.alu0_dispatch_rd_addr,

            issue_fire_trace_alu1,
            dpath.alu1_dispatch_rob_tag,
            alu1_dispatch_inst,
            dpath.alu1_dispatch_rs1_addr,
            dpath.alu1_dispatch_rs2_addr,
            dpath.alu1_dispatch_rd_addr,

            issue_fire_trace_mul,
            dpath.mul_dispatch_rob_tag,
            mul_dispatch_inst,
            dpath.mul_dispatch_rs1_addr,
            dpath.mul_dispatch_rs2_addr,
            dpath.mul_dispatch_rd_addr,

            issue_fire_trace_mem,
            dpath.mem_dispatch_rob_tag,
            mem_dispatch_inst,
            dpath.mem_dispatch_rs1_addr,
            dpath.mem_dispatch_rs2_addr,
            dpath.mem_dispatch_rd_addr
          )}
        );

        if ( issue_trace_count == 1 )
          vc_trace.append_chars( trace_str, " ", 32 );
      end
      vc_trace.append_str( trace_str, "|" );
      
      // 4. WB event (writeback to PRF)

      if ( dpath.rf_wen_alu0_W || dpath.rf_wen_alu1_W
        || dpath.rf_wen_mul_Y3 || dpath.load_prf_wen )
        vc_trace.append_str( trace_str,
          {3864'b0, ooo_trace.wb_preg_trace(
            dpath.rf_wen_alu0_W,
            dpath.rd_paddr_alu0_X,
            dpath.rf_wen_alu1_W,
            dpath.rd_paddr_alu1_X,
            dpath.rf_wen_mul_Y3,
            dpath.rd_paddr_Y3,
            dpath.load_prf_wen,
            dpath.load_ostream_rd_paddr
          )}
        );
      else
        vc_trace.append_chars( trace_str, " ", 29 );
        
      vc_trace.append_str( trace_str, "|" );

      // 5. C stage (Commit)

      if ( commit_val_C_lane0 ) begin
        vc_trace.append_str( trace_str,
          {3928'b0, ooo_trace.commit_trace(
            dpath.commit_has_rd_lane0,
            dpath.rob.head,
            dpath.commit_rd_addr_lane0,
            dpath.commit_rd_paddr_old_C_lane0
          )}
        );

        if ( commit_val_C_lane1 ) begin
          vc_trace.append_str( trace_str, "," );
          vc_trace.append_str( trace_str,
            {3928'b0, ooo_trace.commit_trace(
              dpath.commit_has_rd_lane1,
              dpath.rob.head_plus1,
              dpath.commit_rd_addr_lane1,
              dpath.commit_rd_paddr_old_C_lane1
            )}
          );
        end
        else begin
          vc_trace.append_chars( trace_str, " ", 22 );
        end
      end
      else begin
        vc_trace.append_chars( trace_str, " ", 43 );
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
