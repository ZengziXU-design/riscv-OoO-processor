`ifndef PROC_PROC_PREDECODE_V
`define PROC_PROC_PREDECODE_V

`include "proj3/tinyrv2_encoding.v"

module proj3_ProcPreDecode (
  input  logic [31:0] inst,

  // unpacked register addresses
  output logic [4:0]  rs1_addr,
  output logic [4:0]  rs2_addr,
  output logic [4:0]  rd_addr,

  // valid bits indicating whether the instruction actually uses the corresponding register
  output logic        rs1_valid,
  output logic        rs2_valid,
  output logic        rd_valid,
  output logic        is_csr,
  output logic        is_mem
);

  //----------------------------------------------------------------------
  // Unpack
  //----------------------------------------------------------------------
  proj3_tinyrv2_encoding_InstUnpack inst_unpack
  (
    .inst   ( inst     ),
    .opcode (          ),
    .rd     ( rd_addr  ),
    .rs1    ( rs1_addr ),
    .rs2    ( rs2_addr ),
    .funct3 (          ),
    .funct7 (          ),
    .csr    (          )
  );

  //----------------------------------------------------------------------
  // Decode Valid Bits
  //----------------------------------------------------------------------
  always_comb begin
    rs1_valid = 1'b0;
    rs2_valid = 1'b0;
    rd_valid  = 1'b0;

    casez ( inst )

      // NOP
      `TINYRV2_INST_NOP: begin
        rs1_valid = 1'b0; rs2_valid = 1'b0; rd_valid = 1'b0;
      end

      // R-Type (register-register): read 2, write 1
      `TINYRV2_INST_ADD,  `TINYRV2_INST_SUB,  `TINYRV2_INST_MUL,
      `TINYRV2_INST_AND,  `TINYRV2_INST_OR,   `TINYRV2_INST_XOR,
      `TINYRV2_INST_SLT,  `TINYRV2_INST_SLTU,
      `TINYRV2_INST_SRA,  `TINYRV2_INST_SRL,  `TINYRV2_INST_SLL: begin
        rs1_valid = 1'b1; rs2_valid = 1'b1; rd_valid = 1'b1;
      end

      // I-Type (register-immediate): read 1, write 1
      `TINYRV2_INST_ADDI, `TINYRV2_INST_ANDI, `TINYRV2_INST_ORI,
      `TINYRV2_INST_XORI, `TINYRV2_INST_SLTI, `TINYRV2_INST_SLTIU,
      `TINYRV2_INST_SRAI, `TINYRV2_INST_SRLI, `TINYRV2_INST_SLLI: begin
        rs1_valid = 1'b1; rs2_valid = 1'b0; rd_valid = 1'b1;
      end

      // CSR instructions (CSRR / CSRW): CSRR reads 0, writes 1; CSRW reads 1, writes 0
      `TINYRV2_INST_CSRR: begin
        rs1_valid = 1'b0; rs2_valid = 1'b0; rd_valid = 1'b1;
      end
      `TINYRV2_INST_CSRW: begin
        rs1_valid = 1'b1; rs2_valid = 1'b0; rd_valid = 1'b0;
      end

      // Memory instructions (Load/Store)
      `TINYRV2_INST_LW: begin
        rs1_valid = 1'b1; rs2_valid = 1'b0; rd_valid = 1'b1;
      end
      `TINYRV2_INST_SW: begin
        rs1_valid = 1'b1; rs2_valid = 1'b1; rd_valid = 1'b0;
      end

      // Branch and Jump instructions
      `TINYRV2_INST_JAL: begin
        rs1_valid = 1'b0; rs2_valid = 1'b0; rd_valid = 1'b1;
      end
      `TINYRV2_INST_JALR: begin
        rs1_valid = 1'b1; rs2_valid = 1'b0; rd_valid = 1'b1;
      end
      `TINYRV2_INST_BEQ,  `TINYRV2_INST_BNE,
      `TINYRV2_INST_BLT,  `TINYRV2_INST_BGE,
      `TINYRV2_INST_BLTU, `TINYRV2_INST_BGEU: begin
        rs1_valid = 1'b1; rs2_valid = 1'b1; rd_valid = 1'b0;
      end

      // U-Type (LUI / AUIPC)
      `TINYRV2_INST_LUI, `TINYRV2_INST_AUIPC: begin
        rs1_valid = 1'b0; rs2_valid = 1'b0; rd_valid = 1'b1;
      end

    endcase
  end

  // CSR opcode = 7'b1110011
  assign is_csr = (inst[6:0] == 7'b1110011);

  // Memory opcodes:
  //   LW (load)  -> opcode = 7'b0000011
  //   SW (store) -> opcode = 7'b0100011
  // The IQ uses is_mem to enforce in-order issue between mem instructions
  // and to apply in-flight=1 backpressure through mem_pipe_busy.
  assign is_mem = (inst[6:0] == 7'b0000011) || (inst[6:0] == 7'b0100011);

endmodule

`endif /* PROC_PROC_PREDECODE_V */