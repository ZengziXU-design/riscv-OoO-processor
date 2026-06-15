`ifndef PROJ3_PROCOOO_DPATH_V
`define PROJ3_PROCOOO_DPATH_V

`include "vc/arithmetic.v"
`include "vc/mem-msgs.v"
`include "vc/muxes.v"
`include "vc/regs.v"
`include "vc/regfiles.v"

`include "proj3/IntMul4cycle.v"
`include "proj3/tinyrv2_encoding.v"
`include "proj3/ProcDpathImmGen.v"
`include "proj3/ProcDpathAlu.v"
`include "proj3/ProcIssueQueue.v"
`include "proj3/ProcPreDecode.v"
`include "proj3/ProcReorderBuffer.v"
`include "proj3/ProcRenameUnit.v"
`include "proj3/ProcPregfile.v"
`include "proj3/ProcMemunit.v"

module proj3_ProcDpath
#(
  parameter p_num_cores = 1
)
(
  input  logic        clk,
  input  logic        reset,

  // Instruction Memory Port
  output logic [31:0]  imem_req_addr_lane0,
  output logic [31:0]  imem_req_addr_lane1,
  input  logic [31:0]  imem_resp_inst_lane0,
  input  logic [31:0]  imem_resp_inst_lane1,

  // Data Memory Port
  output logic         dmem_reqstream_val,
  input  logic         dmem_reqstream_rdy,
  output logic [2:0]   dmem_reqstream_msg_type,
  output logic [31:0]  dmem_reqstream_msg_addr,
  output logic [31:0]  dmem_reqstream_msg_data,

  input  logic         dmem_respstream_val,
  output logic         dmem_respstream_rdy,
  input  logic [31:0]  dmem_respstream_msg_data,

  // mngr communication ports
  input  logic [31:0]  mngr2proc_data,
  output logic [31:0]  proc2mngr_data,

  // xcel communication ports
  output logic [4:0]   xcel_reqstream_msg_addr,
  output logic [31:0]  xcel_reqstream_msg_data,
  input  logic [31:0]  xcel_respstream_msg_data,

  // control signals (ctrl->dpath)
  input  logic         reg_en_F,
  input  logic         reg_en_D,
  input  logic         iq_input_val_D,

  // D stage control signals for ROB allocation
  input  logic         rob_alloc_req_D,

  // Dispatch handshakes
  input  logic         alu0_dispatch_rdy,
  input  logic         alu1_dispatch_rdy,
  input  logic         mul_dispatch_rdy,
  input  logic         mem_dispatch_rdy,

  // ALU0 issue/decode controls
  input  logic [2:0]   alu0_imm_type_I,
  input  logic [1:0]   alu0_op2_sel_I,
  input  logic [1:0]   alu0_csrr_sel_I,
  input  logic         alu0_issue_fire_I,

  // ALU1 issue/decode controls
  input  logic [2:0]   alu1_imm_type_I,
  input  logic [1:0]   alu1_op2_sel_I,
  input  logic         alu1_issue_fire_I,

  // MUL/MEM issue controls
  input  logic         mul_issue_fire_I,
  input  logic         mem_issue_fire_I,
  input  logic [2:0]   mem_imm_type_I,
  input  logic         mem_is_sw_I,

  // X stage ALU controls
  input  logic [3:0]   alu0_fn_X,
  input  logic [3:0]   alu1_fn_X,

  // Writeback-side control signals
  input  logic         rf_wen_alu0_W,
  input  logic         rf_wen_alu1_W,
  input  logic         rf_wen_mul_Y3,
  input  logic         rob_fill_val_alu0_W,
  input  logic         rob_fill_val_alu1_W,
  input  logic         rob_fill_val_mul_Y3,

  input  logic         imul_ostream_rdy_W,
  input  logic         stats_en_wen_W,

  // status signals (dpath->ctrl)
  output logic [31:0]  inst_D_lane0,
  output logic [31:0]  inst_D_lane1,
  output logic         iq_input_rdy_D,

  output logic         alu0_dispatch_val,
  output logic [31:0]  alu0_dispatch_inst,
  output logic         alu1_dispatch_val,
  output logic [31:0]  alu1_dispatch_inst,
  output logic         mul_dispatch_val,
  output logic [31:0]  mul_dispatch_inst,
  output logic         mem_dispatch_val,
  output logic [31:0]  mem_dispatch_inst,

  // Compatibility/debug view used by the current line trace.
  output logic         iq_dispatch_val,
  output logic [31:0]  iq_dispatch_inst,

  // D stage status
  output logic         rob_alloc_rdy_D,
  output logic         rob_full_D,
  output logic         rename_rdy_D,

  // ROB commit status
  output logic         commit_val_C,

  output logic         imul_istream_rdy_I,
  output logic         imul_ostream_val_W,
  output logic         load_istream_rdy_I,

  // extra ports
  input  logic [31:0]  core_id,
  output logic         stats_en
);
  localparam c_reset_vector     = 32'h200;
  localparam c_reset_inst       = 32'h00000000;
  localparam c_preg_addr_nbits  = 6;
  localparam c_rob_entries      = 16;
  localparam c_rob_tag_nbits    = $clog2(c_rob_entries);

  //--------------------------------------------------------------------
  // F stage
  //--------------------------------------------------------------------

  logic [31:0] pc_F;
  logic [31:0] pc_plus8_F;

  vc_EnResetReg #(32, c_reset_vector - 32'd8) pc_reg_F
  (
    .clk    (clk),
    .reset  (reset),
    .en     (reg_en_F),
    .d      (pc_plus8_F),
    .q      (pc_F)
  );

  vc_Incrementer #(32, 8) pc_incr_F
  (
    .in   (pc_F),
    .out  (pc_plus8_F)
  );

  assign imem_req_addr_lane0 = pc_plus8_F;
  assign imem_req_addr_lane1 = pc_plus8_F + 32'd4;

  //--------------------------------------------------------------------
  // D stage & PreDecode
  //--------------------------------------------------------------------

  vc_EnResetReg #(32, c_reset_inst) inst_D_lane0_reg
  (
    .clk    (clk),
    .reset  (reset),
    .en     (reg_en_D),
    .d      (imem_resp_inst_lane0),
    .q      (inst_D_lane0)
  );

  vc_EnResetReg #(32, c_reset_inst) inst_D_lane1_reg
  (
    .clk    (clk),
    .reset  (reset),
    .en     (reg_en_D),
    .d      (imem_resp_inst_lane1),
    .q      (inst_D_lane1)
  );

  logic [4:0] predec_rs1_addr_lane0, predec_rs2_addr_lane0, predec_rd_addr_lane0;
  logic       predec_rs1_valid_lane0, predec_rs2_valid_lane0, predec_rd_valid_lane0;
  logic       is_csr_D_lane0;
  logic       is_mem_D_lane0;
  logic       is_mul_D_lane0;

  logic [4:0] predec_rs1_addr_lane1, predec_rs2_addr_lane1, predec_rd_addr_lane1;
  logic       predec_rs1_valid_lane1, predec_rs2_valid_lane1, predec_rd_valid_lane1;
  logic       is_csr_D_lane1;
  logic       is_mem_D_lane1;
  logic       is_mul_D_lane1;

  proj3_ProcPreDecode predecode_D_lane0
  (
    .inst       (inst_D_lane0),
    .rs1_addr   (predec_rs1_addr_lane0),
    .rs2_addr   (predec_rs2_addr_lane0),
    .rd_addr    (predec_rd_addr_lane0),
    .rs1_valid  (predec_rs1_valid_lane0),
    .rs2_valid  (predec_rs2_valid_lane0),
    .rd_valid   (predec_rd_valid_lane0),
    .is_csr     (is_csr_D_lane0),
    .is_mem     (is_mem_D_lane0),
    .is_mul     (is_mul_D_lane0)
  );

  proj3_ProcPreDecode predecode_D_lane1
  (
    .inst       (inst_D_lane1),
    .rs1_addr   (predec_rs1_addr_lane1),
    .rs2_addr   (predec_rs2_addr_lane1),
    .rd_addr    (predec_rd_addr_lane1),
    .rs1_valid  (predec_rs1_valid_lane1),
    .rs2_valid  (predec_rs2_valid_lane1),
    .rd_valid   (predec_rd_valid_lane1),
    .is_csr     (is_csr_D_lane1),
    .is_mem     (is_mem_D_lane1),
    .is_mul     (is_mul_D_lane1)
  );

  //--------------------------------------------------------------------
  // Rename Unit (D stage)
  //--------------------------------------------------------------------

  logic [c_preg_addr_nbits-1:0] rs1_paddr_D_lane0;
  logic [c_preg_addr_nbits-1:0] rs2_paddr_D_lane0;
  logic                         rs1_paddr_valid_D_lane0;
  logic                         rs2_paddr_valid_D_lane0;

  logic [c_preg_addr_nbits-1:0] rs1_paddr_D_lane1;
  logic [c_preg_addr_nbits-1:0] rs2_paddr_D_lane1;
  logic                         rs1_paddr_valid_D_lane1;
  logic                         rs2_paddr_valid_D_lane1;

  logic                         rd_rename_valid_D_lane0;
  logic [c_preg_addr_nbits-1:0] rd_paddr_old_D_lane0;
  logic [c_preg_addr_nbits-1:0] rd_paddr_new_D_lane0;

  logic                         rd_rename_valid_D_lane1;
  logic [c_preg_addr_nbits-1:0] rd_paddr_old_D_lane1;
  logic [c_preg_addr_nbits-1:0] rd_paddr_new_D_lane1;

  logic                         commit_rd_valid_to_rename_C;
  logic [c_preg_addr_nbits-1:0] commit_rd_paddr_old_C;

  proj3_ProcRenameUnit #(
    .p_preg_addr_nbits (c_preg_addr_nbits)
  ) rename_unit
  (
    .clk                (clk),
    .reset              (reset),

    .rename_en_D        (rob_alloc_req_D),
    .rename_rdy_D       (rename_rdy_D),

    .rs1_addr_D_lane0         (predec_rs1_addr_lane0),
    .rs2_addr_D_lane0         (predec_rs2_addr_lane0),
    .rd_addr_D_lane0          (predec_rd_addr_lane0),

    .rs1_valid_D_lane0        (predec_rs1_valid_lane0),
    .rs2_valid_D_lane0        (predec_rs2_valid_lane0),
    .rd_valid_D_lane0         (predec_rd_valid_lane0),

    .rs1_addr_D_lane1         (predec_rs1_addr_lane1),
    .rs2_addr_D_lane1         (predec_rs2_addr_lane1),
    .rd_addr_D_lane1          (predec_rd_addr_lane1),

    .rs1_valid_D_lane1        (predec_rs1_valid_lane1),
    .rs2_valid_D_lane1        (predec_rs2_valid_lane1),
    .rd_valid_D_lane1         (predec_rd_valid_lane1),

    .rs1_paddr_D_lane0        (rs1_paddr_D_lane0),
    .rs2_paddr_D_lane0        (rs2_paddr_D_lane0),
    .rs1_paddr_valid_D_lane0  (rs1_paddr_valid_D_lane0),
    .rs2_paddr_valid_D_lane0  (rs2_paddr_valid_D_lane0),

    .rs1_paddr_D_lane1        (rs1_paddr_D_lane1),
    .rs2_paddr_D_lane1        (rs2_paddr_D_lane1),
    .rs1_paddr_valid_D_lane1  (rs1_paddr_valid_D_lane1),
    .rs2_paddr_valid_D_lane1  (rs2_paddr_valid_D_lane1),

    .rd_rename_valid_D_lane0  (rd_rename_valid_D_lane0),
    .rd_paddr_old_D_lane0     (rd_paddr_old_D_lane0),
    .rd_paddr_new_D_lane0     (rd_paddr_new_D_lane0),

    .rd_rename_valid_D_lane1  (rd_rename_valid_D_lane1),
    .rd_paddr_old_D_lane1     (rd_paddr_old_D_lane1),
    .rd_paddr_new_D_lane1     (rd_paddr_new_D_lane1),

    .commit_rd_valid_C      (commit_rd_valid_to_rename_C),
    .commit_rd_paddr_old_C  (commit_rd_paddr_old_C)
  );

  //--------------------------------------------------------------------
  // ROB Instantiation (D / W / C stages)
  //--------------------------------------------------------------------

  logic [c_rob_tag_nbits-1:0] alloc_tag_D_lane0;
  logic [c_rob_tag_nbits-1:0] alloc_tag_D_lane1;
  logic [c_rob_tag_nbits-1:0] rob_tag_alu0_X;
  logic [c_rob_tag_nbits-1:0] rob_tag_alu1_X;
  logic [c_rob_tag_nbits-1:0] rob_tag_Y3;

  logic        commit_val;
  logic        commit_has_rd;
  logic [4:0]  commit_rd_addr;
  
  assign commit_val_C                 = commit_val;
  assign commit_rd_valid_to_rename_C  = commit_val && commit_has_rd;

  //--------------------------------------------------------------------
  // Memory writeback wires
  //--------------------------------------------------------------------

  logic        load_ostream_val;
  logic        load_ostream_rdy;
  logic        load_ostream_rf_wen;
  logic [31:0] load_ostream_data;
  logic [c_preg_addr_nbits-1:0] load_ostream_rd_paddr;
  logic [c_rob_tag_nbits-1:0] load_ostream_rob_idx;
  logic        load_wb_fire;
  logic        load_prf_wen;

  assign load_ostream_rdy = 1'b1;
  assign load_wb_fire     = load_ostream_val && load_ostream_rdy;
  assign load_prf_wen     = load_wb_fire && load_ostream_rf_wen;

  proj3_ProcReorderBuffer #(
    .p_num_entries     (c_rob_entries),
    .p_preg_addr_nbits (c_preg_addr_nbits)
  ) rob
  (
    .clk                (clk),
    .reset              (reset),

    .alloc_req_lane0          (rob_alloc_req_D),
    .alloc_has_rd_lane0       (rd_rename_valid_D_lane0),
    .alloc_rd_addr_lane0      (predec_rd_addr_lane0),
    .alloc_rd_paddr_old_lane0 (rd_paddr_old_D_lane0),

    .alloc_req_lane1          (rob_alloc_req_D),
    .alloc_has_rd_lane1       (rd_rename_valid_D_lane1),
    .alloc_rd_addr_lane1      (predec_rd_addr_lane1),
    .alloc_rd_paddr_old_lane1 (rd_paddr_old_D_lane1),

    .alloc_tag_lane0          (alloc_tag_D_lane0),
    .alloc_tag_lane1          (alloc_tag_D_lane1),
    .rob_alloc_rdy_D          (rob_alloc_rdy_D),
    .rob_full                 (rob_full_D),

    .wb_req_alu0        (rob_fill_val_alu0_W),
    .wb_tag_alu0        (rob_tag_alu0_X),

    .wb_req_alu1        (rob_fill_val_alu1_W),
    .wb_tag_alu1        (rob_tag_alu1_X),

    .wb_req_mul         (rob_fill_val_mul_Y3),
    .wb_tag_mul         (rob_tag_Y3),

    .wb_req_mem         (load_wb_fire),
    .wb_tag_mem         (load_ostream_rob_idx),

    .commit_val         (commit_val),
    .commit_has_rd      (commit_has_rd),
    .commit_rd_addr     (commit_rd_addr),
    .commit_rd_paddr_old(commit_rd_paddr_old_C)
  );

  //--------------------------------------------------------------------
  // Issue Queue
  //--------------------------------------------------------------------

  logic [c_preg_addr_nbits-1:0] iq_dispatch_rs1_addr;
  logic [c_preg_addr_nbits-1:0] iq_dispatch_rs2_addr;
  logic [c_preg_addr_nbits-1:0] iq_dispatch_rd_addr;
  logic                         iq_dispatch_rd_valid;
  logic [c_rob_tag_nbits-1:0]   iq_dispatch_rob_tag;

  logic [c_rob_tag_nbits-1:0]   alu0_dispatch_rob_tag;
  logic [c_preg_addr_nbits-1:0] alu0_dispatch_rs1_addr;
  logic [c_preg_addr_nbits-1:0] alu0_dispatch_rs2_addr;
  logic [c_preg_addr_nbits-1:0] alu0_dispatch_rd_addr;
  logic                         alu0_dispatch_rd_valid;

  logic [c_rob_tag_nbits-1:0]   alu1_dispatch_rob_tag;
  logic [c_preg_addr_nbits-1:0] alu1_dispatch_rs1_addr;
  logic [c_preg_addr_nbits-1:0] alu1_dispatch_rs2_addr;
  logic [c_preg_addr_nbits-1:0] alu1_dispatch_rd_addr;
  logic                         alu1_dispatch_rd_valid;

  logic [c_rob_tag_nbits-1:0]   mul_dispatch_rob_tag;
  logic [c_preg_addr_nbits-1:0] mul_dispatch_rs1_addr;
  logic [c_preg_addr_nbits-1:0] mul_dispatch_rs2_addr;
  logic [c_preg_addr_nbits-1:0] mul_dispatch_rd_addr;
  logic                         mul_dispatch_rd_valid;

  logic [c_rob_tag_nbits-1:0]   mem_dispatch_rob_tag;
  logic [c_preg_addr_nbits-1:0] mem_dispatch_rs1_addr;
  logic [c_preg_addr_nbits-1:0] mem_dispatch_rs2_addr;
  logic [c_preg_addr_nbits-1:0] mem_dispatch_rd_addr;
  logic                         mem_dispatch_rd_valid;

  logic [c_preg_addr_nbits-1:0] rd_paddr_alu0_X;
  logic [c_preg_addr_nbits-1:0] rd_paddr_alu1_X;
  logic [c_preg_addr_nbits-1:0] rd_paddr_Y3;

  logic                         mem_issue_rdy;

  proj3_ProcIssueQueue #(
    .p_num_entries    (8),
    .p_prf_addr_nbits (c_preg_addr_nbits),
    .p_rob_tag_nbits  (c_rob_tag_nbits)
  ) iq
  (
    .clk               (clk),
    .reset             (reset),

    .input_val_lane0   (iq_input_val_D),
    .input_val_lane1   (iq_input_val_D),
    .input_rdy         (iq_input_rdy_D),

    .input_inst_lane0        (inst_D_lane0),
    .input_rob_tag_lane0     (alloc_tag_D_lane0),
    .input_is_csr_lane0      (is_csr_D_lane0),
    .input_is_mem_lane0      (is_mem_D_lane0),
    .input_is_mul_lane0      (is_mul_D_lane0),

    .input_inst_lane1        (inst_D_lane1),
    .input_rob_tag_lane1     (alloc_tag_D_lane1),
    .input_is_csr_lane1      (is_csr_D_lane1),
    .input_is_mem_lane1      (is_mem_D_lane1),
    .input_is_mul_lane1      (is_mul_D_lane1),

    .input_rs1_addr_lane0    (rs1_paddr_D_lane0),
    .input_rs1_valid_lane0   (rs1_paddr_valid_D_lane0),
    .input_rs2_addr_lane0    (rs2_paddr_D_lane0),
    .input_rs2_valid_lane0   (rs2_paddr_valid_D_lane0),
    .input_rd_addr_lane0     (rd_paddr_new_D_lane0),
    .input_rd_valid_lane0    (rd_rename_valid_D_lane0),

    .input_rs1_addr_lane1    (rs1_paddr_D_lane1),
    .input_rs1_valid_lane1   (rs1_paddr_valid_D_lane1),
    .input_rs2_addr_lane1    (rs2_paddr_D_lane1),
    .input_rs2_valid_lane1   (rs2_paddr_valid_D_lane1),
    .input_rd_addr_lane1     (rd_paddr_new_D_lane1),
    .input_rd_valid_lane1    (rd_rename_valid_D_lane1),

    .alu0_dispatch_val      (alu0_dispatch_val),
    .alu0_dispatch_rdy      (alu0_dispatch_rdy),
    .alu0_dispatch_inst     (alu0_dispatch_inst),
    .alu0_dispatch_rob_tag  (alu0_dispatch_rob_tag),
    .alu0_dispatch_rs1_addr (alu0_dispatch_rs1_addr),
    .alu0_dispatch_rs2_addr (alu0_dispatch_rs2_addr),
    .alu0_dispatch_rd_addr  (alu0_dispatch_rd_addr),
    .alu0_dispatch_rd_valid (alu0_dispatch_rd_valid),

    .alu1_dispatch_val      (alu1_dispatch_val),
    .alu1_dispatch_rdy      (alu1_dispatch_rdy),
    .alu1_dispatch_inst     (alu1_dispatch_inst),
    .alu1_dispatch_rob_tag  (alu1_dispatch_rob_tag),
    .alu1_dispatch_rs1_addr (alu1_dispatch_rs1_addr),
    .alu1_dispatch_rs2_addr (alu1_dispatch_rs2_addr),
    .alu1_dispatch_rd_addr  (alu1_dispatch_rd_addr),
    .alu1_dispatch_rd_valid (alu1_dispatch_rd_valid),

    .mul_dispatch_val      (mul_dispatch_val),
    .mul_dispatch_rdy      (mul_dispatch_rdy),
    .mul_dispatch_inst     (mul_dispatch_inst),
    .mul_dispatch_rob_tag  (mul_dispatch_rob_tag),
    .mul_dispatch_rs1_addr (mul_dispatch_rs1_addr),
    .mul_dispatch_rs2_addr (mul_dispatch_rs2_addr),
    .mul_dispatch_rd_addr  (mul_dispatch_rd_addr),
    .mul_dispatch_rd_valid (mul_dispatch_rd_valid),

    .mem_dispatch_val      (mem_dispatch_val),
    .mem_dispatch_rdy      (mem_dispatch_rdy),
    .mem_dispatch_inst     (mem_dispatch_inst),
    .mem_dispatch_rob_tag  (mem_dispatch_rob_tag),
    .mem_dispatch_rs1_addr (mem_dispatch_rs1_addr),
    .mem_dispatch_rs2_addr (mem_dispatch_rs2_addr),
    .mem_dispatch_rd_addr  (mem_dispatch_rd_addr),
    .mem_dispatch_rd_valid (mem_dispatch_rd_valid),

    .rf_wen_alu0   (rf_wen_alu0_W),
    .rf_waddr_alu0 (rd_paddr_alu0_X),
    .rf_wen_alu1   (rf_wen_alu1_W),
    .rf_waddr_alu1 (rd_paddr_alu1_X),
    .rf_wen_mul    (rf_wen_mul_Y3),
    .rf_waddr_mul  (rd_paddr_Y3),
    .rf_wen_mem    (load_prf_wen),
    .rf_waddr_mem  (load_ostream_rd_paddr)
  );

  // Debug view for the existing single-instruction line trace.
  always_comb begin
    iq_dispatch_val      = 1'b0;
    iq_dispatch_inst     = '0;
    iq_dispatch_rob_tag  = '0;
    iq_dispatch_rs1_addr = '0;
    iq_dispatch_rs2_addr = '0;
    iq_dispatch_rd_addr  = '0;
    iq_dispatch_rd_valid = 1'b0;

    if ( alu0_dispatch_val ) begin
      iq_dispatch_val      = alu0_dispatch_val;
      iq_dispatch_inst     = alu0_dispatch_inst;
      iq_dispatch_rob_tag  = alu0_dispatch_rob_tag;
      iq_dispatch_rs1_addr = alu0_dispatch_rs1_addr;
      iq_dispatch_rs2_addr = alu0_dispatch_rs2_addr;
      iq_dispatch_rd_addr  = alu0_dispatch_rd_addr;
      iq_dispatch_rd_valid = alu0_dispatch_rd_valid;
    end
    else if ( alu1_dispatch_val ) begin
      iq_dispatch_val      = alu1_dispatch_val;
      iq_dispatch_inst     = alu1_dispatch_inst;
      iq_dispatch_rob_tag  = alu1_dispatch_rob_tag;
      iq_dispatch_rs1_addr = alu1_dispatch_rs1_addr;
      iq_dispatch_rs2_addr = alu1_dispatch_rs2_addr;
      iq_dispatch_rd_addr  = alu1_dispatch_rd_addr;
      iq_dispatch_rd_valid = alu1_dispatch_rd_valid;
    end
    else if ( mul_dispatch_val ) begin
      iq_dispatch_val      = mul_dispatch_val;
      iq_dispatch_inst     = mul_dispatch_inst;
      iq_dispatch_rob_tag  = mul_dispatch_rob_tag;
      iq_dispatch_rs1_addr = mul_dispatch_rs1_addr;
      iq_dispatch_rs2_addr = mul_dispatch_rs2_addr;
      iq_dispatch_rd_addr  = mul_dispatch_rd_addr;
      iq_dispatch_rd_valid = mul_dispatch_rd_valid;
    end
    else if ( mem_dispatch_val ) begin
      iq_dispatch_val      = mem_dispatch_val;
      iq_dispatch_inst     = mem_dispatch_inst;
      iq_dispatch_rob_tag  = mem_dispatch_rob_tag;
      iq_dispatch_rs1_addr = mem_dispatch_rs1_addr;
      iq_dispatch_rs2_addr = mem_dispatch_rs2_addr;
      iq_dispatch_rd_addr  = mem_dispatch_rd_addr;
      iq_dispatch_rd_valid = mem_dispatch_rd_valid;
    end
  end

  //--------------------------------------------------------------------
  // Map the four dispatch channels onto two PRF read slots
  //--------------------------------------------------------------------

  logic [c_preg_addr_nbits-1:0] prf_raddr_issue0_rs1;
  logic [c_preg_addr_nbits-1:0] prf_raddr_issue0_rs2;
  logic [c_preg_addr_nbits-1:0] prf_raddr_issue1_rs1;
  logic [c_preg_addr_nbits-1:0] prf_raddr_issue1_rs2;

  logic alu0_uses_issue0, alu0_uses_issue1;
  logic alu1_uses_issue0, alu1_uses_issue1;
  logic mul_uses_issue0,  mul_uses_issue1;
  logic mem_uses_issue0,  mem_uses_issue1;

  always_comb begin : map_prf_read_slots
    logic issue0_used;
    logic issue1_used;

    prf_raddr_issue0_rs1 = '0;
    prf_raddr_issue0_rs2 = '0;
    prf_raddr_issue1_rs1 = '0;
    prf_raddr_issue1_rs2 = '0;

    alu0_uses_issue0 = 1'b0;
    alu0_uses_issue1 = 1'b0;
    alu1_uses_issue0 = 1'b0;
    alu1_uses_issue1 = 1'b0;
    mul_uses_issue0  = 1'b0;
    mul_uses_issue1  = 1'b0;
    mem_uses_issue0  = 1'b0;
    mem_uses_issue1  = 1'b0;

    issue0_used = 1'b0;
    issue1_used = 1'b0;

    if ( alu0_dispatch_val ) begin
      prf_raddr_issue0_rs1 = alu0_dispatch_rs1_addr;
      prf_raddr_issue0_rs2 = alu0_dispatch_rs2_addr;
      alu0_uses_issue0     = 1'b1;
      issue0_used          = 1'b1;
    end

    if ( alu1_dispatch_val ) begin
      if ( !issue0_used ) begin
        prf_raddr_issue0_rs1 = alu1_dispatch_rs1_addr;
        prf_raddr_issue0_rs2 = alu1_dispatch_rs2_addr;
        alu1_uses_issue0     = 1'b1;
        issue0_used          = 1'b1;
      end
      else begin
        prf_raddr_issue1_rs1 = alu1_dispatch_rs1_addr;
        prf_raddr_issue1_rs2 = alu1_dispatch_rs2_addr;
        alu1_uses_issue1     = 1'b1;
        issue1_used          = 1'b1;
      end
    end

    if ( mul_dispatch_val ) begin
      if ( !issue0_used ) begin
        prf_raddr_issue0_rs1 = mul_dispatch_rs1_addr;
        prf_raddr_issue0_rs2 = mul_dispatch_rs2_addr;
        mul_uses_issue0      = 1'b1;
        issue0_used          = 1'b1;
      end
      else if ( !issue1_used ) begin
        prf_raddr_issue1_rs1 = mul_dispatch_rs1_addr;
        prf_raddr_issue1_rs2 = mul_dispatch_rs2_addr;
        mul_uses_issue1      = 1'b1;
        issue1_used          = 1'b1;
      end
    end

    if ( mem_dispatch_val ) begin
      if ( !issue0_used ) begin
        prf_raddr_issue0_rs1 = mem_dispatch_rs1_addr;
        prf_raddr_issue0_rs2 = mem_dispatch_rs2_addr;
        mem_uses_issue0      = 1'b1;
      end
      else if ( !issue1_used ) begin
        prf_raddr_issue1_rs1 = mem_dispatch_rs1_addr;
        prf_raddr_issue1_rs2 = mem_dispatch_rs2_addr;
        mem_uses_issue1      = 1'b1;
      end
    end
  end

  //--------------------------------------------------------------------
  // Issue stage (RR merged into Issue)
  //--------------------------------------------------------------------

  logic [31:0] alu0_imm_I;
  logic [31:0] alu1_imm_I;
  logic [31:0] mem_imm_I;

  logic [31:0] prf_rdata_issue0_rs1_I;
  logic [31:0] prf_rdata_issue0_rs2_I;
  logic [31:0] prf_rdata_issue1_rs1_I;
  logic [31:0] prf_rdata_issue1_rs2_I;

  logic [31:0] alu0_rs1_data_I;
  logic [31:0] alu0_rs2_data_I;
  logic [31:0] alu1_rs1_data_I;
  logic [31:0] alu1_rs2_data_I;
  logic [31:0] mul_rs1_data_I;
  logic [31:0] mul_rs2_data_I;
  logic [31:0] mem_rs1_data_I;
  logic [31:0] mem_rs2_data_I;

  logic [31:0] alu0_op1_I;
  logic [31:0] alu0_op2_I;
  logic [31:0] alu1_op1_I;
  logic [31:0] alu1_op2_I;
  logic [31:0] alu0_csrr_data_I;
  logic [31:0] num_cores;

  assign num_cores = p_num_cores;

  proj3_ProcDpathImmGen alu0_imm_gen_I
  (
    .imm_type (alu0_imm_type_I),
    .inst     (alu0_dispatch_inst),
    .imm      (alu0_imm_I)
  );

  proj3_ProcDpathImmGen alu1_imm_gen_I
  (
    .imm_type (alu1_imm_type_I),
    .inst     (alu1_dispatch_inst),
    .imm      (alu1_imm_I)
  );

  proj3_ProcDpathImmGen mem_imm_gen_I
  (
    .imm_type (mem_imm_type_I),
    .inst     (mem_dispatch_inst),
    .imm      (mem_imm_I)
  );

  //--------------------------------------------------------------------
  // Physical Register File (PRF) 
  //--------------------------------------------------------------------

  logic [31:0] alu0_result_X;
  logic [31:0] alu1_result_X;
  logic [31:0] imul_ostream_msg_W;

  proj3_ProcPregfile prf
  (
    .clk      (clk),
    .reset    (reset),

    .rd_addr_issue0_rs1 (prf_raddr_issue0_rs1),
    .rd_data_issue0_rs1 (prf_rdata_issue0_rs1_I),
    .rd_addr_issue0_rs2 (prf_raddr_issue0_rs2),
    .rd_data_issue0_rs2 (prf_rdata_issue0_rs2_I),

    .rd_addr_issue1_rs1 (prf_raddr_issue1_rs1),
    .rd_data_issue1_rs1 (prf_rdata_issue1_rs1_I),
    .rd_addr_issue1_rs2 (prf_raddr_issue1_rs2),
    .rd_data_issue1_rs2 (prf_rdata_issue1_rs2_I),

    .wr_en_alu0   (rf_wen_alu0_W),
    .wr_addr_alu0 (rd_paddr_alu0_X),
    .wr_data_alu0 (alu0_result_X),

    .wr_en_alu1   (rf_wen_alu1_W),
    .wr_addr_alu1 (rd_paddr_alu1_X),
    .wr_data_alu1 (alu1_result_X),

    .wr_en_mul   (rf_wen_mul_Y3),
    .wr_addr_mul (rd_paddr_Y3),
    .wr_data_mul (imul_ostream_msg_W),

    .wr_en_mem   (load_prf_wen),
    .wr_addr_mem (load_ostream_rd_paddr),
    .wr_data_mem (load_ostream_data)
  );

  assign alu0_rs1_data_I = alu0_uses_issue0 ? prf_rdata_issue0_rs1_I
                           : alu0_uses_issue1 ? prf_rdata_issue1_rs1_I : 32'd0;
  assign alu0_rs2_data_I = alu0_uses_issue0 ? prf_rdata_issue0_rs2_I
                           : alu0_uses_issue1 ? prf_rdata_issue1_rs2_I : 32'd0;
  assign alu1_rs1_data_I = alu1_uses_issue0 ? prf_rdata_issue0_rs1_I
                           : alu1_uses_issue1 ? prf_rdata_issue1_rs1_I : 32'd0;
  assign alu1_rs2_data_I = alu1_uses_issue0 ? prf_rdata_issue0_rs2_I
                           : alu1_uses_issue1 ? prf_rdata_issue1_rs2_I : 32'd0;
  assign mul_rs1_data_I  = mul_uses_issue0 ? prf_rdata_issue0_rs1_I
                           : mul_uses_issue1 ? prf_rdata_issue1_rs1_I : 32'd0;
  assign mul_rs2_data_I  = mul_uses_issue0 ? prf_rdata_issue0_rs2_I
                           : mul_uses_issue1 ? prf_rdata_issue1_rs2_I : 32'd0;
  assign mem_rs1_data_I  = mem_uses_issue0 ? prf_rdata_issue0_rs1_I
                           : mem_uses_issue1 ? prf_rdata_issue1_rs1_I : 32'd0;
  assign mem_rs2_data_I  = mem_uses_issue0 ? prf_rdata_issue0_rs2_I
                           : mem_uses_issue1 ? prf_rdata_issue1_rs2_I : 32'd0;

  assign alu0_op1_I = alu0_rs1_data_I;
  assign alu1_op1_I = alu1_rs1_data_I;

  vc_Mux3 #(32) alu0_csrr_sel_mux_I
  (
    .in0  (mngr2proc_data),
    .in1  (num_cores),
    .in2  (core_id),
    .sel  (alu0_csrr_sel_I),
    .out  (alu0_csrr_data_I)
  );

  vc_Mux3 #(32) alu0_op2_sel_mux_I
  (
    .in0  (alu0_rs2_data_I),
    .in1  (alu0_imm_I),
    .in2  (alu0_csrr_data_I),
    .sel  (alu0_op2_sel_I),
    .out  (alu0_op2_I)
  );

  vc_Mux3 #(32) alu1_op2_sel_mux_I
  (
    .in0  (alu1_rs2_data_I),
    .in1  (alu1_imm_I),
    .in2  (32'd0),
    .sel  (alu1_op2_sel_I),
    .out  (alu1_op2_I)
  );

  //--------------------------------------------------------------------
  // Execute Stage
  //--------------------------------------------------------------------

  logic [31:0] alu0_op1_X;
  logic [31:0] alu0_op2_X;
  logic [31:0] alu1_op1_X;
  logic [31:0] alu1_op2_X;

  vc_EnResetReg #(32, 0) alu0_op1_reg_X
  (
    .clk   (clk),
    .reset (reset),
    .en    (alu0_issue_fire_I),
    .d     (alu0_op1_I),
    .q     (alu0_op1_X)
  );

  vc_EnResetReg #(32, 0) alu0_op2_reg_X
  (
    .clk   (clk),
    .reset (reset),
    .en    (alu0_issue_fire_I),
    .d     (alu0_op2_I),
    .q     (alu0_op2_X)
  );

  vc_EnResetReg #(c_rob_tag_nbits, 0) alu0_rob_tag_reg_X
  (
    .clk   (clk),
    .reset (reset),
    .en    (alu0_issue_fire_I),
    .d     (alu0_dispatch_rob_tag),
    .q     (rob_tag_alu0_X)
  );

  vc_EnResetReg #(c_preg_addr_nbits, 0) alu0_rd_paddr_reg_X
  (
    .clk   (clk),
    .reset (reset),
    .en    (alu0_issue_fire_I),
    .d     (alu0_dispatch_rd_addr),
    .q     (rd_paddr_alu0_X)
  );

  proj3_ProcDpathAlu alu0
  (
    .in0     (alu0_op1_X),
    .in1     (alu0_op2_X),
    .fn      (alu0_fn_X),
    .out     (alu0_result_X),
    .ops_eq  (),
    .ops_lt  (),
    .ops_ltu ()
  );

  vc_EnResetReg #(32, 0) alu1_op1_reg_X
  (
    .clk   (clk),
    .reset (reset),
    .en    (alu1_issue_fire_I),
    .d     (alu1_op1_I),
    .q     (alu1_op1_X)
  );

  vc_EnResetReg #(32, 0) alu1_op2_reg_X
  (
    .clk   (clk),
    .reset (reset),
    .en    (alu1_issue_fire_I),
    .d     (alu1_op2_I),
    .q     (alu1_op2_X)
  );

  vc_EnResetReg #(c_rob_tag_nbits, 0) alu1_rob_tag_reg_X
  (
    .clk   (clk),
    .reset (reset),
    .en    (alu1_issue_fire_I),
    .d     (alu1_dispatch_rob_tag),
    .q     (rob_tag_alu1_X)
  );

  vc_EnResetReg #(c_preg_addr_nbits, 0) alu1_rd_paddr_reg_X
  (
    .clk   (clk),
    .reset (reset),
    .en    (alu1_issue_fire_I),
    .d     (alu1_dispatch_rd_addr),
    .q     (rd_paddr_alu1_X)
  );

  proj3_ProcDpathAlu alu1
  (
    .in0     (alu1_op1_X),
    .in1     (alu1_op2_X),
    .fn      (alu1_fn_X),
    .out     (alu1_result_X),
    .ops_eq  (),
    .ops_lt  (),
    .ops_ltu ()
  );

  //--------------------------------------------------------------------
  // MUL bookkeeping
  //--------------------------------------------------------------------

  logic [c_rob_tag_nbits-1:0] mul_tag_Y0, mul_tag_Y1, mul_tag_Y2, mul_tag_Y3;
  logic [c_preg_addr_nbits-1:0] mul_pdst_Y0, mul_pdst_Y1, mul_pdst_Y2, mul_pdst_Y3;

  always_ff @(posedge clk) begin
    if ( reset ) begin
      mul_tag_Y0  <= '0;
      mul_tag_Y1  <= '0;
      mul_tag_Y2  <= '0;
      mul_tag_Y3  <= '0;

      mul_pdst_Y0 <= '0;
      mul_pdst_Y1 <= '0;
      mul_pdst_Y2 <= '0;
      mul_pdst_Y3 <= '0;
    end
    else begin
      if ( mul_issue_fire_I ) begin
        mul_tag_Y0  <= mul_dispatch_rob_tag;
        mul_pdst_Y0 <= mul_dispatch_rd_addr;
      end

      mul_tag_Y1  <= mul_tag_Y0;
      mul_tag_Y2  <= mul_tag_Y1;
      mul_tag_Y3  <= mul_tag_Y2;

      mul_pdst_Y1 <= mul_pdst_Y0;
      mul_pdst_Y2 <= mul_pdst_Y1;
      mul_pdst_Y3 <= mul_pdst_Y2;
    end
  end

  assign rob_tag_Y3  = mul_tag_Y3;
  assign rd_paddr_Y3 = mul_pdst_Y3;

  proj3_IntMul4cycle imul
  (
    .clk         (clk),
    .reset       (reset),
    .istream_val (mul_issue_fire_I),
    .istream_rdy (imul_istream_rdy_I),
    .istream_msg ({mul_rs1_data_I, mul_rs2_data_I}),
    .ostream_val (imul_ostream_val_W),
    .ostream_rdy (imul_ostream_rdy_W),
    .ostream_msg (imul_ostream_msg_W)
  );

  //--------------------------------------------------------------------
  // Memory Unit
  //--------------------------------------------------------------------

  proj3_MemUnit #(
    .p_paddr_nbits (c_preg_addr_nbits),
    .p_rob_nbits   (c_rob_tag_nbits)
  ) mem_unit
  (
    .clk                      (clk),
    .reset                    (reset),

    .mem_issue_rdy             (mem_issue_rdy),

    .istream_val              (mem_issue_fire_I),
    .istream_rdy              (load_istream_rdy_I),
    .istream_base             (mem_rs1_data_I),
    .istream_imm              (mem_imm_I),
    .istream_rd_paddr         (mem_dispatch_rd_addr),
    .istream_rob_idx          (mem_dispatch_rob_tag),

    .istream_is_sw            (mem_is_sw_I),
    .istream_sw_data          (mem_rs2_data_I),

    .dmem_reqstream_val       (dmem_reqstream_val),
    .dmem_reqstream_rdy       (dmem_reqstream_rdy),
    .dmem_reqstream_msg_type  (dmem_reqstream_msg_type),
    .dmem_reqstream_msg_addr  (dmem_reqstream_msg_addr),
    .dmem_reqstream_msg_data  (dmem_reqstream_msg_data),

    .dmem_respstream_val      (dmem_respstream_val),
    .dmem_respstream_rdy      (dmem_respstream_rdy),
    .dmem_respstream_msg_data (dmem_respstream_msg_data),

    .ostream_val              (load_ostream_val),
    .ostream_rdy              (load_ostream_rdy),
    .ostream_rf_wen           (load_ostream_rf_wen),
    .ostream_data             (load_ostream_data),
    .ostream_rd_paddr         (load_ostream_rd_paddr),
    .ostream_rob_idx          (load_ostream_rob_idx)
  );

  //--------------------------------------------------------------------
  // Writeback side & Status
  //--------------------------------------------------------------------

  assign proc2mngr_data = alu0_result_X;

  logic [31:0] stats_en_W;
  assign stats_en = |stats_en_W;

  vc_EnResetReg #(32, 0) stats_en_reg_W
  (
    .clk    (clk),
    .reset  (reset),
    .en     (stats_en_wen_W),
    .d      (alu0_result_X),
    .q      (stats_en_W)
  );

  assign xcel_reqstream_msg_addr = alu0_op2_X[4:0];
  assign xcel_reqstream_msg_data = alu0_op1_X;

endmodule

`endif /* PROC_PROC_DPATH_V */
