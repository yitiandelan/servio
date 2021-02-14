// Copyright (c) 2021 TIANLAN.tech
// SPDX-License-Identifier: Apache-2.0

// Language: Verilog 2001

`timescale 1ps / 1ps

module servio_mux #(
    parameter DATA_DEPTH = 1024
)(
    input wire [31:0]   wb_s0_adr,
    input wire          wb_s0_cyc,
    output reg [31:0]   wb_s0_rdt,
    output reg          wb_s0_ack,

    input wire [31:0]   wb_s1_adr,
    input wire          wb_s1_cyc,
    output reg [31:0]   wb_s1_rdt,
    output reg          wb_s1_ack,

    input wire [31:0]   wb_s2_adr,
    input wire          wb_s2_cyc,
    output reg [31:0]   wb_s2_rdt,
    output reg          wb_s2_ack,

    input wire [31:0]   wb_s3_adr,
    input wire          wb_s3_cyc,
    output reg [31:0]   wb_s3_rdt,
    output reg          wb_s3_ack,

    output reg [aw-1:0] avm_s4_address,
    output reg          avm_s4_read,
    input wire [7:0]    avm_s4_readdata,
    input wire          avm_s4_readdatavalid,

    input wire          clk,
    input wire          reset
);

    localparam aw = $clog2(DATA_DEPTH);
    localparam dw = (8);

    reg  [31:0] rdata;
    reg         rdatavalid;
    reg  [ 3:0] tsel;
    reg  [ 5:0] bsel;

    always @(*) begin
        tsel         = (reset || (|bsel[5:4])) ? 0 :
                       (bsel[3:2] == 0) ? 1 :
                       (bsel[3:2] == 1) ? 2 :
                       (bsel[3:2] == 2) ? 4 : 8;
        rdata[31:24] = (avm_s4_readdata);
        rdatavalid   = (avm_s4_readdatavalid & (bsel[1:0] == 3));
    end

    always @(*) begin
        avm_s4_address[aw-1:2] = ({aw-2{tsel[0]}} & wb_s0_adr[aw-1:2]) |
                                 ({aw-2{tsel[1]}} & wb_s1_adr[aw-1:2]) |
                                 ({aw-2{tsel[2]}} & wb_s2_adr[aw-1:2]) | {aw-2{tsel[3]}} & wb_s3_adr[aw-1:2];
        avm_s4_address[1:0]    = (bsel[1:0]);
        avm_s4_read            = (tsel[0] & wb_s0_cyc) |
                                 (tsel[1] & wb_s1_cyc) |
                                 (tsel[2] & wb_s2_cyc) | (tsel[3] & wb_s3_cyc);

        wb_s0_rdt = (rdata);
        wb_s1_rdt = (rdata);
        wb_s2_rdt = (rdata);
        wb_s3_rdt = (rdata);
    end

    always @(posedge clk) begin
        wb_s0_ack <= (rdatavalid & tsel[0]);
        wb_s1_ack <= (rdatavalid & tsel[1]);
        wb_s2_ack <= (rdatavalid & tsel[2]);
        wb_s3_ack <= (rdatavalid & tsel[3]);

        if (avm_s4_readdatavalid) begin
            if (bsel[1:0] == 3) rdata[23:16] <= (avm_s4_readdata);
            if (bsel[1:0] == 2) rdata[15: 8] <= (avm_s4_readdata);
            if (bsel[1:0] == 1) rdata[ 7: 0] <= (avm_s4_readdata);
        end

        if (reset) begin
            bsel <= 0;
        end
        else if (bsel == (40-1)) begin
            bsel <= 0;
        end
        else begin
            bsel <= (bsel + 1);
        end

    end

    // simulation
    `ifdef SERVIO_MUX_SIM
    initial begin
        $dumpfile ("waveform.vcd");
        $dumpvars (0);
    end
    `endif

endmodule