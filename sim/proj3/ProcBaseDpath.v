//=========================================================================
// 5-Stage Fully Bypassed Pipelined Processor Datapath
//=========================================================================

`ifndef PROJ3_PROCBASE_DPATH_V
`define PROJ3_PROCBASE_DPATH_V

`include "vc/arithmetic.v"
`include "vc/mem-msgs.v"
`include "vc/muxes.v"
`include "vc/regs.v"
`include "vc/regfiles.v"

`include "proj3/tinyrv2_encoding.v"
`include "proj3/ProcDpathImmGen.v"
`include "proj3/ProcDpathAlu.v"
`include "proj3/IntMul4cycle.v"

module proj3_ProcBaseDpath
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

  output logic [31:0]  dmem_reqstream_msg_addr,
  output logic [31:0]  dmem_reqstream_msg_data,
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
  input  logic [1:0]   pc_sel_F,

  input  logic         reg_en_D,
  input  logic [1:0]   op1_byp_sel_D,
  input  logic [1:0]   op2_byp_sel_D,
  input  logic         op1_sel_D,
  input  logic [1:0]   op2_sel_D,
  input  logic [1:0]   csrr_sel_D,
  input  logic [2:0]   imm_type_D,
  input  logic         imul_istream_val_D,

  input  logic         reg_en_X,
  input  logic [3:0]   alu_fn_X,
  input  logic [1:0]   ex_result_sel_X,
  input  logic         imul_ostream_rdy_X,

  input  logic         reg_en_M,
  input  logic [1:0]   wb_result_sel_M,

  input  logic         reg_en_W,
  input  logic [4:0]   rf_waddr_W,
  input  logic         rf_wen_W,
  input  logic         stats_en_wen_W,

  // status signals (dpath->ctrl)

  output logic [31:0]  inst_D,
  output logic         imul_istream_rdy_D,

  output logic         imul_ostream_val_X,
  output logic         br_cond_eq_X,
  output logic         br_cond_lt_X,
  output logic         br_cond_ltu_X,

  // extra ports

  input  logic [31:0]  core_id,
  output logic         stats_en

);

  localparam c_reset_vector = 32'h200;
  localparam c_reset_inst   = 32'h00000000;

  //--------------------------------------------------------------------
  // F stage
  //--------------------------------------------------------------------

  logic [31:0] pc_F;
  logic [31:0] pc_next_F;
  logic [31:0] pc_plus4_F;
  logic [31:0] br_target_X;
  logic [31:0] jal_target_D;
  logic [31:0] jalr_target_X;

  vc_EnResetReg #(32, c_reset_vector - 32'd4) pc_reg_F
  (
    .clk    (clk),
    .reset  (reset),
    .en     (reg_en_F),
    .d      (pc_next_F),
    .q      (pc_F)
  );

  vc_Incrementer #(32, 4) pc_incr_F
  (
    .in   (pc_F),
    .out  (pc_plus4_F)
  );

  vc_Mux4 #(32) pc_sel_mux_F
  (
    .in0  (pc_plus4_F),
    .in1  (br_target_X),
    .in2  (jal_target_D),
    .in3  (jalr_target_X),
    .sel  (pc_sel_F),
    .out  (pc_next_F)
  );

  // Fetch address

  assign imem_reqstream_msg_addr = pc_next_F;

  //--------------------------------------------------------------------
  // D stage
  //--------------------------------------------------------------------

  logic  [31:0] pc_D;
  logic   [4:0] inst_rd_D;
  logic   [4:0] inst_rs1_D;
  logic   [4:0] inst_rs2_D;
  logic  [31:0] imm_D;

  vc_EnResetReg #(32) pc_reg_D
  (
    .clk    (clk),
    .reset  (reset),
    .en     (reg_en_D),
    .d      (pc_F),
    .q      (pc_D)
  );

  vc_EnResetReg #(32, c_reset_inst) inst_D_reg
  (
    .clk    (clk),
    .reset  (reset),
    .en     (reg_en_D),
    .d      (imem_respstream_msg.data),
    .q      (inst_D)
  );

  proj3_tinyrv2_encoding_InstUnpack inst_unpack
  (
    .opcode   (),
    .inst     (inst_D),
    .rs1      (inst_rs1_D),
    .rs2      (inst_rs2_D),
    .rd       (inst_rd_D),
    .funct3   (),
    .funct7   (),
    .csr      ()
  );

  proj3_ProcDpathImmGen imm_gen_D
  (
    .imm_type (imm_type_D),
    .inst     (inst_D),
    .imm      (imm_D)
  );

  logic [31:0] rf_rdata0_D;
  logic [31:0] rf_rdata1_D;

  logic [31:0] rf_wdata_W;

  vc_Regfile_2r1w_zero rf
  (
    .clk      (clk),
    .reset    (reset),
    .rd_addr0 (inst_rs1_D),
    .rd_data0 (rf_rdata0_D),
    .rd_addr1 (inst_rs2_D),
    .rd_data1 (rf_rdata1_D),
    .wr_en    (rf_wen_W),
    .wr_addr  (rf_waddr_W),
    .wr_data  (rf_wdata_W)
  );

  logic [31:0] byp_data_X;
  logic [31:0] byp_data_M;
  logic [31:0] byp_data_W;

  logic [31:0] op1_byp_D;
  logic [31:0] op1_D;

  // op1 bypass mux
  vc_Mux4 #(32) op1_byp_mux_D
  (
    .in0  (rf_rdata0_D),
    .in1  (byp_data_X),
    .in2  (byp_data_M),
    .in3  (byp_data_W),
    .sel  (op1_byp_sel_D),
    .out  (op1_byp_D)
  );

  // op1 select mux
  vc_Mux2 #(32) op1_sel_mux_D
  (
    .in0  (op1_byp_D),
    .in1  (pc_D),
    .sel  (op1_sel_D),
    .out  (op1_D)
  );

  logic [31:0] op2_byp_D;

  // op2 bypass mux
  vc_Mux4 #(32) op2_byp_mux_D
  (
    .in0  (rf_rdata1_D),
    .in1  (byp_data_X),
    .in2  (byp_data_M),
    .in3  (byp_data_W),
    .sel  (op2_byp_sel_D),
    .out  (op2_byp_D)
  );

  logic [31:0] op2_D;

  logic [31:0] csrr_data_D;

  logic [31:0] num_cores;
  assign num_cores = p_num_cores;

  // csrr data select mux
  vc_Mux3 #(32) csrr_sel_mux_D
  (
   .in0  (mngr2proc_data),
   .in1  (num_cores),
   .in2  (core_id),
   .sel  (csrr_sel_D),
   .out  (csrr_data_D)
  );

  // op2 select mux
  // This mux chooses among RS2, imm, and the output of the above csrr
  // csrr sel mux. Basically we are using two muxes here for pedagogy.
  vc_Mux3 #(32) op2_sel_mux_D
  (
    .in0  (op2_byp_D),
    .in1  (imm_D),
    .in2  (csrr_data_D),
    .sel  (op2_sel_D),
    .out  (op2_D)
  );

  vc_Adder #(32) pc_plus_imm_D
  (
    .in0      (pc_D),
    .in1      (imm_D),
    .cin      (1'b0),
    .out      (jal_target_D),
    .cout     ()
  );

  logic [63:0] imul_istream_msg_D;
  assign imul_istream_msg_D = {op1_D, op2_D};

  logic [31:0] imul_ostream_msg_tmp_X;
  logic        imul_ostream_val_tmp_X;
  logic        imul_ostream_rdy_tmp_X;

  proj3_IntMul4cycle imul
  (
    .clk         (clk),
    .reset       (reset),

    .istream_val (imul_istream_val_D),
    .istream_rdy (imul_istream_rdy_D),
    .istream_msg (imul_istream_msg_D),

    .ostream_val (imul_ostream_val_tmp_X),
    .ostream_rdy (imul_ostream_rdy_tmp_X),
    .ostream_msg (imul_ostream_msg_tmp_X)
  );

  // We need this bypass queue to break a val/rdy loop. With the
  // iterative multiplier there is no combinational path from the
  // ostream_rdy to the istream_rdy, but there _is_ such a combinational
  // path in the single cycle multiplier which is what causes the
  // problem. Technically we might be able to get rid of it, but we would
  // need to rewrite the stall logic in D and X to make sure there is no
  // dependencies between the imul val/rdy signals. -cbatten

  logic        imulresp_q_num_free_entries;
  logic [31:0] imul_ostream_msg_X;

  vc_Queue#(`VC_QUEUE_BYPASS,32,1) imulresp_q
  (
    .clk       (clk),
    .reset     (reset),

    .num_free_entries (imulresp_q_num_free_entries),

    .enq_val   (imul_ostream_val_tmp_X),
    .enq_rdy   (imul_ostream_rdy_tmp_X),
    .enq_msg   (imul_ostream_msg_tmp_X),

    .deq_val   (imul_ostream_val_X),
    .deq_rdy   (imul_ostream_rdy_X),
    .deq_msg   (imul_ostream_msg_X)
  );

  //--------------------------------------------------------------------
  // X stage
  //--------------------------------------------------------------------

  logic [31:0] pc_X;
  vc_EnResetReg #(32) pc_reg_X
  (
    .clk    (clk),
    .reset  (reset),
    .en     (reg_en_X),
    .d      (pc_D),
    .q      (pc_X)
  );

  logic [31:0] op1_X;
  logic [31:0] op2_X;

  vc_EnResetReg #(32, 0) op1_reg_X
  (
    .clk    (clk),
    .reset  (reset),
    .en     (reg_en_X),
    .d      (op1_D),
    .q      (op1_X)
  );

  vc_EnResetReg #(32, 0) op2_reg_X
  (
    .clk    (clk),
    .reset  (reset),
    .en     (reg_en_X),
    .d      (op2_D),
    .q      (op2_X)
  );

  vc_EnResetReg #(32, 0) br_target_reg_X
  (
    .clk    (clk),
    .reset  (reset),
    .en     (reg_en_X),
    .d      (jal_target_D),
    .q      (br_target_X)
  );

  vc_EnResetReg #(32, 0) dmem_write_data_reg_X
  (
    .clk    (clk),
    .reset  (reset),
    .en     (reg_en_X),
    .d      (op2_byp_D),
    .q      (dmem_reqstream_msg_data)
  );

  assign xcel_reqstream_msg_addr = op2_X[4:0];
  assign xcel_reqstream_msg_data = op1_X;

  logic [31:0] alu_result_X;
  logic [31:0] ex_result_X;

  proj3_ProcDpathAlu alu
  (
    .in0     (op1_X),
    .in1     (op2_X),
    .fn      (alu_fn_X),
    .out     (alu_result_X),
    .ops_eq  (br_cond_eq_X),
    .ops_lt  (br_cond_lt_X),
    .ops_ltu (br_cond_ltu_X)
  );

  assign jalr_target_X = alu_result_X;

  // PC+4 Incrementer, used for jalr instruction
  logic [31:0] pc_plus4_X;
  vc_Incrementer #(32, 4) pc_incr_X
  (
    .in    (pc_X),
    .out   (pc_plus4_X)
  );

  // Select the output of the X stage
  vc_Mux3 #(32) ex_result_sel_mux_X
  (
    .in0   (alu_result_X),
    .in1   (imul_ostream_msg_X),
    .in2   (pc_plus4_X),
    .sel   (ex_result_sel_X),
    .out   (ex_result_X)
  );

  assign byp_data_X = ex_result_X;

  assign dmem_reqstream_msg_addr = alu_result_X;

  //--------------------------------------------------------------------
  // M stage
  //--------------------------------------------------------------------

  logic [31:0] ex_result_M;

  vc_EnResetReg #(32, 0) ex_result_reg_M
  (
    .clk   (clk),
    .reset (reset),
    .en    (reg_en_M),
    .d     (ex_result_X),
    .q     (ex_result_M)
  );

  logic [31:0] dmem_result_M;
  logic [31:0] wb_result_M;

  assign dmem_result_M = dmem_respstream_msg_data;

  vc_Mux3 #(32) wb_result_sel_mux_M
  (
    .in0   (ex_result_M),
    .in1   (dmem_result_M),
    .in2   (xcel_respstream_msg_data),
    .sel   (wb_result_sel_M),
    .out   (wb_result_M)
  );

  assign byp_data_M = wb_result_M;

  //--------------------------------------------------------------------
  // W stage
  //--------------------------------------------------------------------

  logic [31:0] wb_result_W;

  vc_EnResetReg #(32, 0) wb_result_reg_W
  (
    .clk   (clk),
    .reset (reset),
    .en    (reg_en_W),
    .d     (wb_result_M),
    .q     (wb_result_W)
  );

  assign proc2mngr_data = wb_result_W;

  assign rf_wdata_W = wb_result_W;

  assign byp_data_W = wb_result_W;

  // stats output; note the stats en is full 32-bit here but the outside
  // port is one bit.

  logic [31:0] stats_en_W;

  assign stats_en = | stats_en_W;

  vc_EnResetReg #(32, 0) stats_en_reg_W
  (
   .clk    (clk),
   .reset  (reset),
   .en     (stats_en_wen_W),
   .d      (wb_result_W),
   .q      (stats_en_W)
  );

endmodule

`endif /* PROC_PROC_DPATH_V */