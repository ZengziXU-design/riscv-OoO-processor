`ifndef PROJ3_PROCOOO_CTRL_V
`define PROJ3_PROCOOO_CTRL_V

`include "vc/mem-msgs.v"
`include "proj3/tinyrv2_encoding.v"

module proj3_ProcCtrl
(
  input  logic        clk,
  input  logic        reset,

  output logic        imem_reqstream_val,
  input  logic        imem_reqstream_rdy,
  input  logic        imem_respstream_val,
  output logic        imem_respstream_rdy,
  output logic        imem_respstream_drop,

  output logic [2:0]  dmem_reqstream_msg_type,
  output logic        dmem_reqstream_val,
  input  logic        dmem_reqstream_rdy,
  input  logic        dmem_respstream_val,
  output logic        dmem_respstream_rdy,

  input  logic        mngr2proc_val,
  output logic        mngr2proc_rdy,
  output logic        proc2mngr_val,
  input  logic        proc2mngr_rdy,

  output logic        xcel_reqstream_val,
  input  logic        xcel_reqstream_rdy,
  output logic        xcel_reqstream_msg_type,
  input  logic        xcel_respstream_val,
  output logic        xcel_respstream_rdy,

  output logic        reg_en_F,
  output logic        reg_en_D,
  output logic        iq_input_val_D,
  output logic        rob_alloc_req_D,

  output logic        alu0_dispatch_rdy,
  output logic        alu1_dispatch_rdy,
  output logic        mul_dispatch_rdy,
  output logic        mem_dispatch_rdy,

  output logic [2:0]  alu0_imm_type_I,
  output logic [1:0]  alu0_op2_sel_I,
  output logic [1:0]  alu0_csrr_sel_I,
  output logic        alu0_issue_fire_I,

  output logic [2:0]  alu1_imm_type_I,
  output logic [1:0]  alu1_op2_sel_I,
  output logic        alu1_issue_fire_I,

  output logic        mul_issue_fire_I,
  output logic        mem_issue_fire_I,
  output logic [2:0]  mem_imm_type_I,
  output logic        mem_is_sw_I,

  output logic [3:0]  alu0_fn_X,
  output logic [3:0]  alu1_fn_X,

  output logic        rf_wen_alu0_W,
  output logic        rf_wen_alu1_W,
  output logic        rf_wen_mul_Y3,
  output logic        rob_fill_val_alu0_W,
  output logic        rob_fill_val_alu1_W,
  output logic        rob_fill_val_mul_Y3,

  output logic        imul_ostream_rdy_W,
  output logic        stats_en_wen_W,

  input  logic [31:0] inst_D_lane0,
  input  logic [31:0] inst_D_lane1,
  input  logic        iq_input_rdy_D,
  input  logic        rob_alloc_rdy_D,
  input  logic        rob_full_D,
  input  logic        rename_rdy_D,

  input  logic        alu0_dispatch_val,
  input  logic [31:0] alu0_dispatch_inst,
  input  logic        alu1_dispatch_val,
  input  logic [31:0] alu1_dispatch_inst,
  input  logic        mul_dispatch_val,
  input  logic [31:0] mul_dispatch_inst,
  input  logic        mem_dispatch_val,
  input  logic [31:0] mem_dispatch_inst,

  input  logic        imul_istream_rdy_I,
  input  logic        imul_ostream_val_W,
  input  logic        load_istream_rdy_I,

  input  logic        commit_val_C_lane0,
  input  logic        commit_val_C_lane1,
  output logic        commit_inst
);

  localparam n = 1'b0;
  localparam y = 1'b1;

  localparam bm_rf  = 2'd0;
  localparam bm_imm = 2'd1;
  localparam bm_csr = 2'd2;

  localparam alu_add = 4'd0;
  localparam alu_sub = 4'd1;
  localparam alu_sll = 4'd2;
  localparam alu_or  = 4'd3;
  localparam alu_lt  = 4'd4;
  localparam alu_ltu = 4'd5;
  localparam alu_and = 4'd6;
  localparam alu_xor = 4'd7;
  localparam alu_nor = 4'd8;
  localparam alu_srl = 4'd9;
  localparam alu_sra = 4'd10;
  localparam alu_cp0 = 4'd11;
  localparam alu_cp1 = 4'd12;

  localparam imm_i = 3'd0;
  localparam imm_s = 3'd1;

  logic val_F;
  logic val_D;
  logic val_alu0_X;
  logic val_alu1_X;

  logic stall_F;
  logic stall_D;
  logic stall_W;

  logic next_val_F;

  logic alu0_dispatch_fire;
  logic alu1_dispatch_fire;
  logic issue_stall_Q;

  // Reuse the existing detailed decoder for the ALU0/CSR channel.
  wire        iq_dispatch_val  = alu0_dispatch_val;
  wire [31:0] iq_dispatch_inst = alu0_dispatch_inst;

  assign imem_respstream_drop = 1'b0;

  // Dmem val/rdy/type are now driven by the datapath MemUnit path.
  // This ctrl-side type is only a dummy tie-off for the top connection.
  assign dmem_reqstream_msg_type = `VC_MEM_REQ_MSG_TYPE_READ;
  assign dmem_reqstream_val      = 1'b0;
  assign dmem_respstream_rdy     = 1'b0;

  assign xcel_reqstream_val      = 1'b0;
  assign xcel_reqstream_msg_type = 1'b0;
  assign xcel_respstream_rdy     = 1'b0;

  //----------------------------------------------------------------------
  // F stage
  //----------------------------------------------------------------------

  logic ostall_F;

  assign reg_en_F = !stall_F;

  always_ff @(posedge clk) begin
    if ( reset )
      val_F <= 1'b0;
    else if ( reg_en_F )
      val_F <= 1'b1;
  end

  assign ostall_F = val_F && !imem_respstream_val;
  assign stall_F  = ostall_F || stall_D;
  assign imem_reqstream_val  = !reset && !stall_F;
  assign imem_respstream_rdy = !stall_F;

  assign next_val_F = val_F && !stall_F;

  //----------------------------------------------------------------------
  // D stage
  //----------------------------------------------------------------------

  logic d_rdy;

  assign d_rdy    = iq_input_rdy_D && rob_alloc_rdy_D && rename_rdy_D;
  assign stall_D  = val_D && !d_rdy;
  assign reg_en_D = !stall_D;

  assign iq_input_val_D  = val_D && rob_alloc_rdy_D && rename_rdy_D;
  assign rob_alloc_req_D = val_D && rob_alloc_rdy_D && iq_input_rdy_D && rename_rdy_D;

  always_ff @(posedge clk) begin
    if ( reset )
      val_D <= 1'b0;
    else if ( reg_en_D )
      val_D <= next_val_F;
  end

  //----------------------------------------------------------------------
  // Decode on IQ dispatch instruction
  //----------------------------------------------------------------------

  logic [4:0]  inst_rd_Q;
  logic [4:0]  inst_rs1_Q;
  logic [4:0]  inst_rs2_Q;
  logic [11:0] inst_csr_Q;

  proj3_tinyrv2_encoding_InstUnpack inst_unpack_q
  (
    .inst   (iq_dispatch_inst),
    .opcode (),
    .rd     (inst_rd_Q),
    .rs1    (inst_rs1_Q),
    .rs2    (inst_rs2_Q),
    .funct3 (),
    .funct7 (),
    .csr    (inst_csr_Q)
  );

  logic       dec_inst_val_Q;
  logic [2:0] dec_imm_type_Q;
  logic       dec_rs1_en_Q;
  logic       dec_rs2_en_Q;
  logic [1:0] dec_op2_sel_Q;
  logic [3:0] dec_alu_fn_Q;
  logic       dec_rf_wen_Q;
  logic       dec_mul_Q;
  logic       dec_csrr_Q;
  logic       dec_csrw_Q;
  logic       dec_load_Q;
  logic       dec_store_Q;

  task automatic cs
  (
    input logic       cs_inst_val,
    input logic [2:0] cs_imm_type,
    input logic       cs_rs1_en,
    input logic [1:0] cs_op2_sel,
    input logic       cs_rs2_en,
    input logic [3:0] cs_alu_fn,
    input logic       cs_rf_wen,
    input logic       cs_mul,
    input logic       cs_csrr,
    input logic       cs_csrw,
    input logic       cs_load,
    input logic       cs_store
  );
  begin
    dec_inst_val_Q = cs_inst_val;
    dec_imm_type_Q = cs_imm_type;
    dec_rs1_en_Q   = cs_rs1_en;
    dec_op2_sel_Q  = cs_op2_sel;
    dec_rs2_en_Q   = cs_rs2_en;
    dec_alu_fn_Q   = cs_alu_fn;
    dec_rf_wen_Q   = cs_rf_wen;
    dec_mul_Q      = cs_mul;
    dec_csrr_Q     = cs_csrr;
    dec_csrw_Q     = cs_csrw;
    dec_load_Q     = cs_load;
    dec_store_Q    = cs_store;
  end
  endtask

  always_comb begin
    cs( n, imm_i, n, bm_rf,  n, alu_add, n, n, n, n, n, n );
    casez ( iq_dispatch_inst )

      `TINYRV2_INST_NOP  : cs( y, imm_i, n, bm_rf,  n, alu_add, n, n, n, n, n, n );

      `TINYRV2_INST_ADD  : cs( y, imm_i, y, bm_rf,  y, alu_add, y, n, n, n, n, n );
      `TINYRV2_INST_SUB  : cs( y, imm_i, y, bm_rf,  y, alu_sub, y, n, n, n, n, n );
      `TINYRV2_INST_MUL  : cs( y, imm_i, y, bm_rf,  y, alu_add, y, y, n, n, n, n );
      `TINYRV2_INST_AND  : cs( y, imm_i, y, bm_rf,  y, alu_and, y, n, n, n, n, n );
      `TINYRV2_INST_OR   : cs( y, imm_i, y, bm_rf,  y, alu_or,  y, n, n, n, n, n );
      `TINYRV2_INST_XOR  : cs( y, imm_i, y, bm_rf,  y, alu_xor, y, n, n, n, n, n );
      `TINYRV2_INST_SLT  : cs( y, imm_i, y, bm_rf,  y, alu_lt,  y, n, n, n, n, n );
      `TINYRV2_INST_SLTU : cs( y, imm_i, y, bm_rf,  y, alu_ltu, y, n, n, n, n, n );
      `TINYRV2_INST_SRA  : cs( y, imm_i, y, bm_rf,  y, alu_sra, y, n, n, n, n, n );
      `TINYRV2_INST_SRL  : cs( y, imm_i, y, bm_rf,  y, alu_srl, y, n, n, n, n, n );
      `TINYRV2_INST_SLL  : cs( y, imm_i, y, bm_rf,  y, alu_sll, y, n, n, n, n, n );

      `TINYRV2_INST_ADDI : cs( y, imm_i, y, bm_imm, n, alu_add, y, n, n, n, n, n );
      `TINYRV2_INST_ANDI : cs( y, imm_i, y, bm_imm, n, alu_and, y, n, n, n, n, n );
      `TINYRV2_INST_ORI  : cs( y, imm_i, y, bm_imm, n, alu_or,  y, n, n, n, n, n );
      `TINYRV2_INST_XORI : cs( y, imm_i, y, bm_imm, n, alu_xor, y, n, n, n, n, n );
      `TINYRV2_INST_SLTI : cs( y, imm_i, y, bm_imm, n, alu_lt,  y, n, n, n, n, n );
      `TINYRV2_INST_SLTIU: cs( y, imm_i, y, bm_imm, n, alu_ltu, y, n, n, n, n, n );
      `TINYRV2_INST_SRAI : cs( y, imm_i, y, bm_imm, n, alu_sra, y, n, n, n, n, n );
      `TINYRV2_INST_SRLI : cs( y, imm_i, y, bm_imm, n, alu_srl, y, n, n, n, n, n );
      `TINYRV2_INST_SLLI : cs( y, imm_i, y, bm_imm, n, alu_sll, y, n, n, n, n, n );

      // mem
      `TINYRV2_INST_LW   : cs( y, imm_i, y, bm_imm, n, alu_add, n, n, n, n, y, n );
      `TINYRV2_INST_SW   : cs( y, imm_s, y, bm_imm, y, alu_add, n, n, n, n, n, y );

      // csr
      `TINYRV2_INST_CSRR : cs( y, imm_i, n, bm_csr, n, alu_cp1, y, n, y, n, n, n );
      `TINYRV2_INST_CSRW : cs( y, imm_i, y, bm_imm, n, alu_cp0, n, n, n, y, n, n );

      default            : cs( n, imm_i, n, bm_rf,  n, alu_add, n, n, n, n, n, n );
    endcase
  end

  //----------------------------------------------------------------------
  // CSR decode refinement
  //----------------------------------------------------------------------

  logic       csrr_mngr2proc_Q;
  logic [1:0] csrr_sel_final_Q;
  logic       proc2mngr_Q;
  logic       stats_en_wen_Q;

  always_comb begin
    csrr_mngr2proc_Q = 1'b0;
    csrr_sel_final_Q = 2'd0;
    proc2mngr_Q      = 1'b0;
    stats_en_wen_Q   = 1'b0;

    if ( dec_csrr_Q ) begin
      if ( inst_csr_Q == `TINYRV2_CPR_MNGR2PROC ) begin
        csrr_mngr2proc_Q = 1'b1;
        csrr_sel_final_Q = 2'd0;
      end
      else if ( inst_csr_Q == `TINYRV2_CPR_NUMCORES )
        csrr_sel_final_Q = 2'd1;
      else if ( inst_csr_Q == `TINYRV2_CPR_COREID )
        csrr_sel_final_Q = 2'd2;
    end

    if ( dec_csrw_Q ) begin
      if ( inst_csr_Q == `TINYRV2_CPR_PROC2MNGR )
        proc2mngr_Q = 1'b1;
      else if ( inst_csr_Q == `TINYRV2_CPR_STATS_EN )
        stats_en_wen_Q = 1'b1;
    end
  end

  //----------------------------------------------------------------------
  // ALU1 decode (integer instructions only; CSR is restricted to ALU0)
  //----------------------------------------------------------------------

  logic [2:0] dec_alu1_imm_type_Q;
  logic [1:0] dec_alu1_op2_sel_Q;
  logic [3:0] dec_alu1_fn_Q;
  logic       dec_alu1_rf_wen_Q;

  always_comb begin
    dec_alu1_imm_type_Q = imm_i;
    dec_alu1_op2_sel_Q  = bm_rf;
    dec_alu1_fn_Q       = alu_add;
    dec_alu1_rf_wen_Q   = 1'b0;

    casez ( alu1_dispatch_inst )
      `TINYRV2_INST_NOP  : begin dec_alu1_fn_Q = alu_add; dec_alu1_rf_wen_Q = 1'b0; end
      `TINYRV2_INST_ADD  : begin dec_alu1_fn_Q = alu_add; dec_alu1_rf_wen_Q = 1'b1; end
      `TINYRV2_INST_SUB  : begin dec_alu1_fn_Q = alu_sub; dec_alu1_rf_wen_Q = 1'b1; end
      `TINYRV2_INST_AND  : begin dec_alu1_fn_Q = alu_and; dec_alu1_rf_wen_Q = 1'b1; end
      `TINYRV2_INST_OR   : begin dec_alu1_fn_Q = alu_or;  dec_alu1_rf_wen_Q = 1'b1; end
      `TINYRV2_INST_XOR  : begin dec_alu1_fn_Q = alu_xor; dec_alu1_rf_wen_Q = 1'b1; end
      `TINYRV2_INST_SLT  : begin dec_alu1_fn_Q = alu_lt;  dec_alu1_rf_wen_Q = 1'b1; end
      `TINYRV2_INST_SLTU : begin dec_alu1_fn_Q = alu_ltu; dec_alu1_rf_wen_Q = 1'b1; end
      `TINYRV2_INST_SRA  : begin dec_alu1_fn_Q = alu_sra; dec_alu1_rf_wen_Q = 1'b1; end
      `TINYRV2_INST_SRL  : begin dec_alu1_fn_Q = alu_srl; dec_alu1_rf_wen_Q = 1'b1; end
      `TINYRV2_INST_SLL  : begin dec_alu1_fn_Q = alu_sll; dec_alu1_rf_wen_Q = 1'b1; end

      `TINYRV2_INST_ADDI : begin dec_alu1_op2_sel_Q = bm_imm; dec_alu1_fn_Q = alu_add; dec_alu1_rf_wen_Q = 1'b1; end
      `TINYRV2_INST_ANDI : begin dec_alu1_op2_sel_Q = bm_imm; dec_alu1_fn_Q = alu_and; dec_alu1_rf_wen_Q = 1'b1; end
      `TINYRV2_INST_ORI  : begin dec_alu1_op2_sel_Q = bm_imm; dec_alu1_fn_Q = alu_or;  dec_alu1_rf_wen_Q = 1'b1; end
      `TINYRV2_INST_XORI : begin dec_alu1_op2_sel_Q = bm_imm; dec_alu1_fn_Q = alu_xor; dec_alu1_rf_wen_Q = 1'b1; end
      `TINYRV2_INST_SLTI : begin dec_alu1_op2_sel_Q = bm_imm; dec_alu1_fn_Q = alu_lt;  dec_alu1_rf_wen_Q = 1'b1; end
      `TINYRV2_INST_SLTIU: begin dec_alu1_op2_sel_Q = bm_imm; dec_alu1_fn_Q = alu_ltu; dec_alu1_rf_wen_Q = 1'b1; end
      `TINYRV2_INST_SRAI : begin dec_alu1_op2_sel_Q = bm_imm; dec_alu1_fn_Q = alu_sra; dec_alu1_rf_wen_Q = 1'b1; end
      `TINYRV2_INST_SRLI : begin dec_alu1_op2_sel_Q = bm_imm; dec_alu1_fn_Q = alu_srl; dec_alu1_rf_wen_Q = 1'b1; end
      `TINYRV2_INST_SLLI : begin dec_alu1_op2_sel_Q = bm_imm; dec_alu1_fn_Q = alu_sll; dec_alu1_rf_wen_Q = 1'b1; end
      default            : begin dec_alu1_fn_Q = alu_add; dec_alu1_rf_wen_Q = 1'b0; end
    endcase
  end

  //----------------------------------------------------------------------
  // Issue-side backpressure / handshake
  //----------------------------------------------------------------------

  logic ostall_mngr2proc_Q;

  assign ostall_mngr2proc_Q
    = iq_dispatch_val && csrr_mngr2proc_Q && !mngr2proc_val;

  assign issue_stall_Q = stall_W || ostall_mngr2proc_Q;

  assign alu0_dispatch_rdy = !issue_stall_Q;
  assign alu1_dispatch_rdy = !stall_W;
  assign mul_dispatch_rdy  = imul_istream_rdy_I;
  assign mem_dispatch_rdy  = load_istream_rdy_I;

  assign alu0_dispatch_fire = alu0_dispatch_val && alu0_dispatch_rdy;
  assign alu1_dispatch_fire = alu1_dispatch_val && alu1_dispatch_rdy;

  assign alu0_imm_type_I   = dec_imm_type_Q;
  assign alu0_op2_sel_I    = dec_op2_sel_Q;
  assign alu0_csrr_sel_I   = csrr_sel_final_Q;
  assign alu0_issue_fire_I = alu0_dispatch_fire;

  assign alu1_imm_type_I   = dec_alu1_imm_type_Q;
  assign alu1_op2_sel_I    = dec_alu1_op2_sel_Q;
  assign alu1_issue_fire_I = alu1_dispatch_fire;

  assign mul_issue_fire_I = mul_dispatch_val && mul_dispatch_rdy;
  assign mem_issue_fire_I = mem_dispatch_val && mem_dispatch_rdy;
  assign mem_is_sw_I      = ( mem_dispatch_inst[6:0] == 7'b0100011 );
  assign mem_imm_type_I   = mem_is_sw_I ? imm_s : imm_i;

  assign mngr2proc_rdy = alu0_dispatch_fire && csrr_mngr2proc_Q;

  //----------------------------------------------------------------------
  // X stage control pipeline
  //----------------------------------------------------------------------

  logic       rf_wen_alu0_X_r;
  logic       rf_wen_alu1_X_r;
  logic [3:0] alu0_fn_X_r;
  logic [3:0] alu1_fn_X_r;
  logic       proc2mngr_X_r;
  logic       stats_en_wen_X_r;

  logic       x_pipe_en;

  assign x_pipe_en = !stall_W;

  always_ff @(posedge clk) begin
    if ( reset ) begin
      val_alu0_X        <= 1'b0;
      val_alu1_X        <= 1'b0;
      rf_wen_alu0_X_r   <= 1'b0;
      rf_wen_alu1_X_r   <= 1'b0;
      alu0_fn_X_r       <= alu_add;
      alu1_fn_X_r       <= alu_add;
      proc2mngr_X_r    <= 1'b0;
      stats_en_wen_X_r <= 1'b0;
    end
    else if ( x_pipe_en ) begin
      val_alu0_X        <= alu0_issue_fire_I;
      val_alu1_X        <= alu1_issue_fire_I;
      rf_wen_alu0_X_r   <= alu0_issue_fire_I && dec_rf_wen_Q;
      rf_wen_alu1_X_r   <= alu1_issue_fire_I && dec_alu1_rf_wen_Q;
      alu0_fn_X_r       <= dec_alu_fn_Q;
      alu1_fn_X_r       <= dec_alu1_fn_Q;
      proc2mngr_X_r    <= alu0_issue_fire_I && proc2mngr_Q;
      stats_en_wen_X_r <= alu0_issue_fire_I && stats_en_wen_Q;
    end
  end

  assign alu0_fn_X = alu0_fn_X_r;
  assign alu1_fn_X = alu1_fn_X_r;

  //----------------------------------------------------------------------
  // Combinational writeback-side control
  //----------------------------------------------------------------------

  logic take_alu0_now;
  logic take_alu1_now;
  logic take_mul_now;
  logic       mul_valid_Y0,  mul_valid_Y1,  mul_valid_Y2,  mul_valid_Y3;
  logic [4:0] mul_rd_Y0,     mul_rd_Y1,     mul_rd_Y2,     mul_rd_Y3;
  logic       mul_rf_wen_Y0, mul_rf_wen_Y1, mul_rf_wen_Y2, mul_rf_wen_Y3;

  logic       mul_pipe_en;

  assign take_alu0_now = val_alu0_X;
  assign take_alu1_now = val_alu1_X;

  assign imul_ostream_rdy_W = 1'b1;
  assign mul_pipe_en        = imul_ostream_rdy_W;

  assign take_mul_now = mul_valid_Y3 && imul_ostream_val_W;

  assign stall_W = take_alu0_now && proc2mngr_X_r && !proc2mngr_rdy;

  assign rf_wen_alu0_W = !stall_W && take_alu0_now && rf_wen_alu0_X_r;
  assign rf_wen_alu1_W = !stall_W && take_alu1_now && rf_wen_alu1_X_r;
  assign rf_wen_mul_Y3 = take_mul_now && mul_rf_wen_Y3;

  assign rob_fill_val_alu0_W = !stall_W && take_alu0_now;
  assign rob_fill_val_alu1_W = !stall_W && take_alu1_now;
  assign rob_fill_val_mul_Y3 = take_mul_now;

  assign proc2mngr_val  = !stall_W && take_alu0_now && proc2mngr_X_r;
  assign stats_en_wen_W = !stall_W && take_alu0_now && stats_en_wen_X_r;

  //----------------------------------------------------------------------
  // MUL bookkeeping
  //----------------------------------------------------------------------

  always_ff @(posedge clk) begin
    if ( reset ) begin
      mul_valid_Y0    <= 1'b0;
      mul_valid_Y1    <= 1'b0;
      mul_valid_Y2    <= 1'b0;
      mul_valid_Y3    <= 1'b0;

      mul_rd_Y0       <= 5'd0;
      mul_rd_Y1       <= 5'd0;
      mul_rd_Y2       <= 5'd0;
      mul_rd_Y3       <= 5'd0;

      mul_rf_wen_Y0   <= 1'b0;
      mul_rf_wen_Y1   <= 1'b0;
      mul_rf_wen_Y2   <= 1'b0;
      mul_rf_wen_Y3   <= 1'b0;
    end
    else if ( mul_pipe_en ) begin
      mul_valid_Y0    <= mul_issue_fire_I;
      mul_rd_Y0       <= mul_issue_fire_I ? mul_dispatch_inst[11:7] : 5'd0;
      mul_rf_wen_Y0   <= mul_issue_fire_I;

      mul_valid_Y1    <= mul_valid_Y0;
      mul_valid_Y2    <= mul_valid_Y1;
      mul_valid_Y3    <= mul_valid_Y2;

      mul_rd_Y1       <= mul_rd_Y0;
      mul_rd_Y2       <= mul_rd_Y1;
      mul_rd_Y3       <= mul_rd_Y2;

      mul_rf_wen_Y1   <= mul_rf_wen_Y0;
      mul_rf_wen_Y2   <= mul_rf_wen_Y1;
      mul_rf_wen_Y3   <= mul_rf_wen_Y2;
    end
  end

  assign commit_inst = commit_val_C_lane0 || commit_val_C_lane1;

endmodule

`endif
