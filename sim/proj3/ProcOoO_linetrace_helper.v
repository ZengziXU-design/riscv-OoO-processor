//========================================================================
// OoO_linetrace_helper.v
//========================================================================

`ifndef PROC_OOO_LINETRACE_HELPER_V
`define PROC_OOO_LINETRACE_HELPER_V

`include "proj3/tinyrv2_encoding.v"

module proj3_OoO_linetrace_InstTasks();

  reg [3*8-1:0] prs1_str;
  reg [3*8-1:0] prs2_str;
  reg [3*8-1:0] prd_str;
  reg [9*8-1:0] csr_str;
  reg [2*8-1:0] funct_str;

  logic [`TINYRV2_INST_CSR_NBITS-1:0]    csr;
  logic [`TINYRV2_INST_FUNCT7_NBITS-1:0] funct;

  function [25*8-1:0] disasm_phy
  (
    input [`TINYRV2_INST_NBITS-1:0] inst,
    input [5:0] rs1_paddr,
    input [5:0] rs2_paddr,
    input [5:0] rd_paddr
  );
  begin
    csr   = inst[`TINYRV2_INST_CSR];
    funct = inst[`TINYRV2_INST_FUNCT7];

    // Create fixed-width physical register specifiers

    if ( rs1_paddr <= 9 )
      $sformat( prs1_str, "p0%0d", rs1_paddr );
    else
      $sformat( prs1_str, "p%0d",  rs1_paddr );

    if ( rs2_paddr <= 9 )
      $sformat( prs2_str, "p0%0d", rs2_paddr );
    else
      $sformat( prs2_str, "p%0d",  rs2_paddr );

    if ( rd_paddr <= 9 )
      $sformat( prd_str, "p0%0d", rd_paddr );
    else
      $sformat( prd_str, "p%0d",  rd_paddr );

    if ( csr == `TINYRV2_CPR_PROC2MNGR )
      $sformat( csr_str, "proc2mngr" );
    else if ( csr == `TINYRV2_CPR_MNGR2PROC )
      $sformat( csr_str, "mngr2proc" );
    else if ( csr == `TINYRV2_CPR_COREID )
      $sformat( csr_str, "coreid   " );
    else if ( csr == `TINYRV2_CPR_NUMCORES )
      $sformat( csr_str, "numcores " );
    else if ( csr == `TINYRV2_CPR_STATS_EN )
      $sformat( csr_str, "stats_en " );
    else
      $sformat( csr_str, "    0x%x", csr );

    $sformat( funct_str, "%x", funct[1:0] );

    // Actual disassembly with physical regs

    casez ( inst )
      `TINYRV2_INST_CSRR  : $sformat( disasm_phy, "csrr   %s, %s  ",        prd_str,  csr_str );
      `TINYRV2_INST_CSRW  : $sformat( disasm_phy, "csrw   %s, %s  ",        csr_str,  prs1_str );
      `TINYRV2_INST_NOP   : $sformat( disasm_phy, "nop                    " );
      `TINYRV2_ZERO       : $sformat( disasm_phy, "                       " );

      `TINYRV2_INST_ADD   : $sformat( disasm_phy, "add    %s, %s, %s   ",   prd_str,  prs1_str, prs2_str );
      `TINYRV2_INST_SUB   : $sformat( disasm_phy, "sub    %s, %s, %s   ",   prd_str,  prs1_str, prs2_str );
      `TINYRV2_INST_AND   : $sformat( disasm_phy, "and    %s, %s, %s   ",   prd_str,  prs1_str, prs2_str );
      `TINYRV2_INST_OR    : $sformat( disasm_phy, "or     %s, %s, %s   ",   prd_str,  prs1_str, prs2_str );
      `TINYRV2_INST_XOR   : $sformat( disasm_phy, "xor    %s, %s, %s   ",   prd_str,  prs1_str, prs2_str );
      `TINYRV2_INST_SLT   : $sformat( disasm_phy, "slt    %s, %s, %s   ",   prd_str,  prs1_str, prs2_str );
      `TINYRV2_INST_SLTU  : $sformat( disasm_phy, "sltu   %s, %s, %s   ",   prd_str,  prs1_str, prs2_str );
      `TINYRV2_INST_MUL   : $sformat( disasm_phy, "mul    %s, %s, %s   ",   prd_str,  prs1_str, prs2_str );

      `TINYRV2_INST_ADDI  : $sformat( disasm_phy, "addi   %s, %s, 0x%x ",   prd_str,  prs1_str, imm_i(inst) );
      `TINYRV2_INST_ANDI  : $sformat( disasm_phy, "andi   %s, %s, 0x%x ",   prd_str,  prs1_str, imm_i(inst) );
      `TINYRV2_INST_ORI   : $sformat( disasm_phy, "ori    %s, %s, 0x%x ",   prd_str,  prs1_str, imm_i(inst) );
      `TINYRV2_INST_XORI  : $sformat( disasm_phy, "xori   %s, %s, 0x%x ",   prd_str,  prs1_str, imm_i(inst) );
      `TINYRV2_INST_SLTI  : $sformat( disasm_phy, "slti   %s, %s, 0x%x ",   prd_str,  prs1_str, imm_i(inst) );
      `TINYRV2_INST_SLTIU : $sformat( disasm_phy, "sltiu  %s, %s, 0x%x ",   prd_str,  prs1_str, imm_i(inst) );

      `TINYRV2_INST_SRA   : $sformat( disasm_phy, "sra    %s, %s, 0x%x  ",  prd_str,  prs1_str, imm_shamt(inst) );
      `TINYRV2_INST_SRL   : $sformat( disasm_phy, "srl    %s, %s, 0x%x  ",  prd_str,  prs1_str, imm_shamt(inst) );
      `TINYRV2_INST_SLL   : $sformat( disasm_phy, "sll    %s, %s, 0x%x  ",  prd_str,  prs1_str, imm_shamt(inst) );
      `TINYRV2_INST_SRAI  : $sformat( disasm_phy, "srai   %s, %s, 0x%x  ",  prd_str,  prs1_str, imm_shamt(inst) );
      `TINYRV2_INST_SRLI  : $sformat( disasm_phy, "srli   %s, %s, 0x%x  ",  prd_str,  prs1_str, imm_shamt(inst) );
      `TINYRV2_INST_SLLI  : $sformat( disasm_phy, "slli   %s, %s, 0x%x  ",  prd_str,  prs1_str, imm_shamt(inst) );

      `TINYRV2_INST_LUI   : $sformat( disasm_phy, "lui    %s, 0x%x    ",    prd_str,  imm_u_sh12(inst) );
      `TINYRV2_INST_AUIPC : $sformat( disasm_phy, "auipc  %s, 0x%x    ",    prd_str,  imm_u_sh12(inst) );

      `TINYRV2_INST_LW    : $sformat( disasm_phy, "lw     %s, 0x%x(%s) ",   prd_str,  imm_i(inst), prs1_str );
      `TINYRV2_INST_SW    : $sformat( disasm_phy, "sw     %s, 0x%x(%s) ",   prs2_str, imm_s(inst), prs1_str );

      `TINYRV2_INST_JAL   : $sformat( disasm_phy, "jal    %s, 0x%x   ",     prd_str, imm_j(inst) );
      `TINYRV2_INST_JALR  : $sformat( disasm_phy, "jalr   %s, %s, 0x%x ",   prd_str, prs1_str, imm_i(inst) );

      `TINYRV2_INST_BEQ   : $sformat( disasm_phy, "beq    %s, %s, 0x%x",    prs1_str, prs2_str, imm_b(inst) );
      `TINYRV2_INST_BNE   : $sformat( disasm_phy, "bne    %s, %s, 0x%x",    prs1_str, prs2_str, imm_b(inst) );
      `TINYRV2_INST_BLT   : $sformat( disasm_phy, "blt    %s, %s, 0x%x",    prs1_str, prs2_str, imm_b(inst) );
      `TINYRV2_INST_BGE   : $sformat( disasm_phy, "bge    %s, %s, 0x%x",    prs1_str, prs2_str, imm_b(inst) );
      `TINYRV2_INST_BLTU  : $sformat( disasm_phy, "bltu   %s, %s, 0x%x",    prs1_str, prs2_str, imm_b(inst) );
      `TINYRV2_INST_BGEU  : $sformat( disasm_phy, "bgeu   %s, %s, 0x%x",    prs1_str, prs2_str, imm_b(inst) );

      `TINYRV2_INST_CUST0 : $sformat( disasm_phy, "cust0 %s, %s, %s, %s",   prd_str, prs1_str, prs2_str, funct_str );
      default             : $sformat( disasm_phy, "illegal inst           " );
    endcase

  end
  endfunction

  //----------------------------------------------------------------------
  // Immediate decoding -- only outputs signals at the width required for
  // line tracing
  //----------------------------------------------------------------------
  function [11:0] imm_i( input [`TINYRV2_INST_NBITS-1:0] inst );
  begin
    // I-type immediate
    imm_i = { inst[31], inst[30:25], inst[24:21], inst[20] };
  end
  endfunction

  function [4:0] imm_shamt( input [`TINYRV2_INST_NBITS-1:0] inst );
  begin
    // I-type immediate, specialized for shift amounts
    imm_shamt = { inst[24:21], inst[20] };
  end
  endfunction

  function [11:0] imm_s( input [`TINYRV2_INST_NBITS-1:0] inst );
  begin
    // S-type immediate
    imm_s = { inst[31], inst[30:25], inst[11:8], inst[7] };
  end
  endfunction

  function [12:0] imm_b( input [`TINYRV2_INST_NBITS-1:0] inst );
  begin
    // B-type immediate
    imm_b = { inst[31], inst[7], inst[30:25], inst[11:8], 1'b0 };
  end
  endfunction

  function [19:0] imm_u_sh12( input [`TINYRV2_INST_NBITS-1:0] inst );
  begin
    // U-type immediate, shifted right by 12
    imm_u_sh12 = { inst[31], inst[30:20], inst[19:12] };
  end
  endfunction

  function [20:0] imm_j( input [`TINYRV2_INST_NBITS-1:0] inst );
  begin
    // J-type immediate
    imm_j = { inst[31], inst[19:12], inst[20], inst[30:25], inst[24:21], 1'b0 };
  end
  endfunction

    //------------------------------------------------------------------------
    // Writeback physical register trace
    //------------------------------------------------------------------------

    reg [3*8-1:0] wb0_str;
    reg [3*8-1:0] wb1_str;
    reg [3*8-1:0] wb2_str;
    reg [3*8-1:0] wb3_str;

    function [29*8-1:0] wb_preg_trace
    (
      input logic       wen0,
      input logic [5:0] addr0,
      input logic       wen1,
      input logic [5:0] addr1,
      input logic       wen2,
      input logic [5:0] addr2,
      input logic       wen3,
      input logic [5:0] addr3
    );
    begin

      if ( !wen0 )
        $sformat( wb0_str, "---" );
      else if ( addr0 <= 9 )
        $sformat( wb0_str, "p0%0d", addr0 );
      else
        $sformat( wb0_str, "p%0d",  addr0 );

      if ( !wen1 )
        $sformat( wb1_str, "---" );
      else if ( addr1 <= 9 )
        $sformat( wb1_str, "p0%0d", addr1 );
      else
        $sformat( wb1_str, "p%0d",  addr1 );

      if ( !wen2 )
        $sformat( wb2_str, "---" );
      else if ( addr2 <= 9 )
        $sformat( wb2_str, "p0%0d", addr2 );
      else
        $sformat( wb2_str, "p%0d",  addr2 );

      if ( !wen3 )
        $sformat( wb3_str, "---" );
      else if ( addr3 <= 9 )
        $sformat( wb3_str, "p0%0d", addr3 );
      else
        $sformat( wb3_str, "p%0d",  addr3 );

      $sformat( wb_preg_trace, "a0:%s a1:%s mul:%s mem:%s",
                wb0_str, wb1_str, wb2_str, wb3_str );

    end
    endfunction

//------------------------------------------------------------------------
// Commit trace
//------------------------------------------------------------------------

reg [2*8-1:0] c_rob_tag_str;
reg [3*8-1:0] c_old_preg_str;
reg [3*8-1:0] c_areg_str;

function [21*8-1:0] commit_trace
(
  input logic       has_rd,
  input logic [3:0] rob_tag,
  input logic [4:0] aaddr,
  input logic [5:0] old_paddr
);
begin

  // ROB tag, 0-15
  $sformat( c_rob_tag_str, "%0d", rob_tag );

  // Old physical destination to free
  if ( old_paddr <= 9 )
    $sformat( c_old_preg_str, "p0%0d", old_paddr );
  else
    $sformat( c_old_preg_str, "p%0d",  old_paddr );

  // Architectural destination
  if ( aaddr <= 9 )
    $sformat( c_areg_str, "x0%0d", aaddr );
  else
    $sformat( c_areg_str, "x%0d",  aaddr );

  // Fixed-width commit trace string for Unified PRF
  // "15: cmt x05, free:p10"
  if ( has_rd && ( aaddr != 0 ) )
    $sformat( commit_trace, "%s: cmt %s, free:%s", c_rob_tag_str, c_areg_str, c_old_preg_str );
  else
    $sformat( commit_trace, "%s:                  ", c_rob_tag_str );

end
endfunction

endmodule

`endif
