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
  output logic [31:0]  imem_reqstream_msg_addr,
  input  mem_resp_4B_t imem_respstream_msg,

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
  input  logic         iq_dispatch_rdy,

  // D stage control signals for ROB allocation
  input  logic         rob_alloc_req_D,

  // I stage decode controls for dispatch_inst
  input  logic [2:0]   imm_type_I,
  input  logic [1:0]   op2_sel_I,
  input  logic [1:0]   csrr_sel_I,
  input  logic         imul_istream_val_I,
  input  logic         is_mem_I,
  input  logic         is_sw_I,

  // X Stage Control Signals
  input  logic         reg_en_X,
  input  logic [3:0]   alu_fn_X,

  // Writeback-side control signals
  input  logic [4:0]   rf_waddr_W,
  input  logic         rf_wen_W,
  input  logic [4:0]   rf_waddr_Y3,
  input  logic         rf_wen_Y3,
  input  logic         rob_fill_val_W,
  input  logic         rob_fill_val_Y3,

  input  logic         imul_ostream_rdy_W,
  input  logic         stats_en_wen_W,

  // status signals (dpath->ctrl)
  output logic [31:0]  inst_D,
  output logic         iq_input_rdy_D,
  output logic         iq_dispatch_val,
  output logic [31:0]  iq_dispatch_inst,

  // D stage status
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

  //--------------------------------------------------------------------
  // F stage
  //--------------------------------------------------------------------

  logic [31:0] pc_F;
  logic [31:0] pc_plus4_F;

  vc_EnResetReg #(32, c_reset_vector - 32'd4) pc_reg_F
  (
    .clk    (clk),
    .reset  (reset),
    .en     (reg_en_F),
    .d      (pc_plus4_F),
    .q      (pc_F)
  );

  vc_Incrementer #(32, 4) pc_incr_F
  (
    .in   (pc_F),
    .out  (pc_plus4_F)
  );

  assign imem_reqstream_msg_addr = pc_plus4_F;

  //--------------------------------------------------------------------
  // D stage & PreDecode
  //--------------------------------------------------------------------

  vc_EnResetReg #(32, c_reset_inst) inst_D_reg
  (
    .clk    (clk),
    .reset  (reset),
    .en     (reg_en_D),
    .d      (imem_respstream_msg.data),
    .q      (inst_D)
  );

  logic [4:0] predec_rs1_addr, predec_rs2_addr, predec_rd_addr;
  logic       predec_rs1_valid, predec_rs2_valid, predec_rd_valid;
  logic       is_csr_D;
  logic       is_mem_D;

  proj3_ProcPreDecode predecode_D
  (
    .inst       (inst_D),
    .rs1_addr   (predec_rs1_addr),
    .rs2_addr   (predec_rs2_addr),
    .rd_addr    (predec_rd_addr),
    .rs1_valid  (predec_rs1_valid),
    .rs2_valid  (predec_rs2_valid),
    .rd_valid   (predec_rd_valid),
    .is_csr     (is_csr_D),
    .is_mem     (is_mem_D)
  );

  //--------------------------------------------------------------------
  // Rename Unit (D stage)
  //--------------------------------------------------------------------

  logic [c_preg_addr_nbits-1:0] rs1_paddr_D;
  logic [c_preg_addr_nbits-1:0] rs2_paddr_D;
  logic                         rs1_paddr_valid_D;
  logic                         rs2_paddr_valid_D;

  logic                         rd_rename_valid_D;
  logic [c_preg_addr_nbits-1:0] rd_paddr_old_D;
  logic [c_preg_addr_nbits-1:0] rd_paddr_new_D;

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

    .rs1_addr_D         (predec_rs1_addr),
    .rs2_addr_D         (predec_rs2_addr),
    .rd_addr_D          (predec_rd_addr),

    .rs1_valid_D        (predec_rs1_valid),
    .rs2_valid_D        (predec_rs2_valid),
    .rd_valid_D         (predec_rd_valid),

    .rs1_paddr_D        (rs1_paddr_D),
    .rs2_paddr_D        (rs2_paddr_D),
    .rs1_paddr_valid_D  (rs1_paddr_valid_D),
    .rs2_paddr_valid_D  (rs2_paddr_valid_D),

    .rd_rename_valid_D  (rd_rename_valid_D),
    .rd_paddr_old_D     (rd_paddr_old_D),
    .rd_paddr_new_D     (rd_paddr_new_D),

    .commit_rd_valid_C      (commit_rd_valid_to_rename_C),
    .commit_rd_paddr_old_C  (commit_rd_paddr_old_C)
  );

  //--------------------------------------------------------------------
  // ROB Instantiation (D / W / C stages)
  //--------------------------------------------------------------------

  logic [2:0]  alloc_tag_D;
  logic [2:0]  rob_tag_X;
  logic [2:0]  rob_tag_Y3;

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
  logic [2:0]  load_ostream_rob_idx;
  logic        load_wb_fire;
  logic        load_prf_wen;

  assign load_ostream_rdy = 1'b1;
  assign load_wb_fire     = load_ostream_val && load_ostream_rdy;
  assign load_prf_wen     = load_wb_fire && load_ostream_rf_wen;

  proj3_ProcReorderBuffer #(
    .p_num_entries     (8),
    .p_preg_addr_nbits (c_preg_addr_nbits)
  ) rob
  (
    .clk                (clk),
    .reset              (reset),

    .alloc_req          (rob_alloc_req_D),
    .alloc_has_rd       (rd_rename_valid_D),
    .alloc_rd_addr      (predec_rd_addr),
    .alloc_rd_paddr_old (rd_paddr_old_D),
    .alloc_tag          (alloc_tag_D),
    .rob_full           (rob_full_D),

    .wb0_req            (rob_fill_val_W),
    .wb0_tag            (rob_tag_X),

    .wb1_req            (rob_fill_val_Y3),
    .wb1_tag            (rob_tag_Y3),

    .wb2_req            (load_wb_fire),
    .wb2_tag            (load_ostream_rob_idx),

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
  logic [2:0]                   iq_dispatch_rob_tag;

  logic [c_preg_addr_nbits-1:0] rd_paddr_X;
  logic [c_preg_addr_nbits-1:0] rd_paddr_Y3;

  logic                         mem_issue_rdy;

  proj3_ProcIssueQueue #(
    .p_num_entries    (4),
    .p_prf_addr_nbits (c_preg_addr_nbits),
    .p_rob_tag_nbits  (3)
  ) iq
  (
    .clk               (clk),
    .reset             (reset),

    .input_val         (iq_input_val_D),
    .input_rdy         (iq_input_rdy_D),

    .input_inst        (inst_D),
    .input_rob_tag     (alloc_tag_D),
    .input_is_csr      (is_csr_D),
    .input_is_mem      (is_mem_D),

    .input_rs1_addr    (rs1_paddr_D),
    .input_rs1_valid   (rs1_paddr_valid_D),
    .input_rs2_addr    (rs2_paddr_D),
    .input_rs2_valid   (rs2_paddr_valid_D),
    .input_rd_addr     (rd_paddr_new_D),
    .input_rd_valid    (rd_rename_valid_D),

    .dispatch_val      (iq_dispatch_val),
    .dispatch_rdy      (iq_dispatch_rdy),

    .mem_issue_rdy      (mem_issue_rdy),

    .dispatch_inst     (iq_dispatch_inst),
    .dispatch_rob_tag  (iq_dispatch_rob_tag),
    .dispatch_rs1_addr (iq_dispatch_rs1_addr),
    .dispatch_rs2_addr (iq_dispatch_rs2_addr),
    .dispatch_rd_addr  (iq_dispatch_rd_addr),
    .dispatch_rd_valid (iq_dispatch_rd_valid),

    .rf_wen0           (rf_wen_W),
    .rf_waddr0         (rd_paddr_X),
    .rf_wen1           (rf_wen_Y3),
    .rf_waddr1         (rd_paddr_Y3),
    .rf_wen2           (load_prf_wen),
    .rf_waddr2         (load_ostream_rd_paddr)
  );

  //--------------------------------------------------------------------
  // Issue stage (RR merged into Issue)
  //--------------------------------------------------------------------

  logic        iq_dispatch_fire;
  logic        issue_to_x_fire;
  logic        load_issue_fire;
  logic [31:0] dispatch_imm_I;

  logic [31:0] prf_rdata0_I;
  logic [31:0] prf_rdata1_I;

  logic [31:0] op1_issue;
  logic [31:0] op2_issue;
  logic [31:0] csrr_data_I;
  logic [31:0] num_cores;

  assign iq_dispatch_fire = iq_dispatch_val && iq_dispatch_rdy;
  assign issue_to_x_fire  = iq_dispatch_fire && !imul_istream_val_I && !is_mem_I;
  assign load_issue_fire  = iq_dispatch_fire && is_mem_I;

  assign num_cores        = p_num_cores;

  proj3_ProcDpathImmGen imm_gen_I
  (
    .imm_type (imm_type_I),
    .inst     (iq_dispatch_inst),
    .imm      (dispatch_imm_I)
  );

  //--------------------------------------------------------------------
  // Physical Register File (PRF) 
  //--------------------------------------------------------------------

  logic [31:0] alu_result_X;
  logic [31:0] imul_ostream_msg_W;

  proj3_ProcPregfile prf
  (
    .clk      (clk),
    .reset    (reset),

    .rd_addr0 (iq_dispatch_rs1_addr),
    .rd_data0 (prf_rdata0_I),
    .rd_addr1 (iq_dispatch_rs2_addr),
    .rd_data1 (prf_rdata1_I),

    .wr_en0   (rf_wen_W),
    .wr_addr0 (rd_paddr_X),
    .wr_data0 (alu_result_X),

    .wr_en1   (rf_wen_Y3),
    .wr_addr1 (rd_paddr_Y3),
    .wr_data1 (imul_ostream_msg_W),

    .wr_en2   (load_prf_wen),
    .wr_addr2 (load_ostream_rd_paddr),
    .wr_data2 (load_ostream_data)
  );

  assign op1_issue = prf_rdata0_I;

  vc_Mux3 #(32) csrr_sel_mux_I
  (
    .in0  (mngr2proc_data),
    .in1  (num_cores),
    .in2  (core_id),
    .sel  (csrr_sel_I),
    .out  (csrr_data_I)
  );

  vc_Mux3 #(32) op2_sel_mux_I
  (
    .in0  (prf_rdata1_I),
    .in1  (dispatch_imm_I),
    .in2  (csrr_data_I),
    .sel  (op2_sel_I),
    .out  (op2_issue)
  );

  //--------------------------------------------------------------------
  // Execute Stage
  //--------------------------------------------------------------------

  logic [31:0] op1_X;
  logic [31:0] op2_X;

  vc_EnResetReg #(32, 0) op1_reg_X
  (
    .clk   (clk),
    .reset (reset),
    .en    (issue_to_x_fire),
    .d     (op1_issue),
    .q     (op1_X)
  );

  vc_EnResetReg #(32, 0) op2_reg_X
  (
    .clk   (clk),
    .reset (reset),
    .en    (issue_to_x_fire),
    .d     (op2_issue),
    .q     (op2_X)
  );

  vc_EnResetReg #(3, 0) rob_tag_reg_X
  (
    .clk   (clk),
    .reset (reset),
    .en    (issue_to_x_fire),
    .d     (iq_dispatch_rob_tag),
    .q     (rob_tag_X)
  );

  vc_EnResetReg #(c_preg_addr_nbits, 0) rd_paddr_reg_X
  (
    .clk   (clk),
    .reset (reset),
    .en    (issue_to_x_fire),
    .d     (iq_dispatch_rd_addr),
    .q     (rd_paddr_X)
  );

  proj3_ProcDpathAlu alu
  (
    .in0     (op1_X),
    .in1     (op2_X),
    .fn      (alu_fn_X),
    .out     (alu_result_X),
    .ops_eq  (),
    .ops_lt  (),
    .ops_ltu ()
  );

  //--------------------------------------------------------------------
  // MUL bookkeeping
  //--------------------------------------------------------------------

  logic [2:0] mul_tag_Y0, mul_tag_Y1, mul_tag_Y2, mul_tag_Y3;
  logic [c_preg_addr_nbits-1:0] mul_pdst_Y0, mul_pdst_Y1, mul_pdst_Y2, mul_pdst_Y3;

  logic                         mul_issue_fire;
  assign mul_issue_fire = iq_dispatch_fire && imul_istream_val_I && imul_istream_rdy_I;

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
      if ( mul_issue_fire ) begin
        mul_tag_Y0  <= iq_dispatch_rob_tag;
        mul_pdst_Y0 <= iq_dispatch_rd_addr;
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
    .istream_val (imul_istream_val_I),
    .istream_rdy (imul_istream_rdy_I),
    .istream_msg ({op1_issue, op2_issue}),
    .ostream_val (imul_ostream_val_W),
    .ostream_rdy (imul_ostream_rdy_W),
    .ostream_msg (imul_ostream_msg_W)
  );

  //--------------------------------------------------------------------
  // Memory Unit
  //--------------------------------------------------------------------

  proj3_MemUnit #(
    .p_paddr_nbits (c_preg_addr_nbits),
    .p_rob_nbits   (3)
  ) mem_unit
  (
    .clk                      (clk),
    .reset                    (reset),

    .mem_issue_rdy             (mem_issue_rdy),

    .istream_val              (load_issue_fire),
    .istream_rdy              (load_istream_rdy_I),
    .istream_base             (prf_rdata0_I),
    .istream_imm              (dispatch_imm_I),
    .istream_rd_paddr         (iq_dispatch_rd_addr),
    .istream_rob_idx          (iq_dispatch_rob_tag),

    .istream_is_sw            (is_sw_I),
    .istream_sw_data          (prf_rdata1_I),

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

  assign proc2mngr_data = alu_result_X;

  logic [31:0] stats_en_W;
  assign stats_en = |stats_en_W;

  vc_EnResetReg #(32, 0) stats_en_reg_W
  (
    .clk    (clk),
    .reset  (reset),
    .en     (stats_en_wen_W),
    .d      (alu_result_X),
    .q      (stats_en_W)
  );

  assign xcel_reqstream_msg_addr = op2_X[4:0];
  assign xcel_reqstream_msg_data = op1_X;

endmodule

`endif /* PROC_PROC_DPATH_V */