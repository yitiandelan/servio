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

    input wire [5:0]    asi_cyc_data,
    input wire          asi_cyc_valid,

    output reg [5:0]    aso_cyc_data,
    output reg          aso_cyc_valid,

    input wire          clk,
    input wire          reset
);

    localparam aw = $clog2(DATA_DEPTH);
    localparam dw = (8);

    reg  [aw-1-2:0] rom_ra;
    reg         rom_rr;
    reg  [31:0] rom_rd;
    reg  [ 3:0] rom_rv;

    reg  [ 3:0] tsel;
    reg  [ 5:0] bsel;
    reg         flag;

    always @(*) begin
        bsel = (asi_cyc_data);
        flag = (asi_cyc_valid);

        if (reset | (!flag) | (|bsel[5:4])) begin
            tsel   = 0;
            rom_rr = 0;
            rom_ra = 0;
        end
        else if (bsel[3:2] == 0) begin
            tsel   = 1;
            rom_rr = wb_s0_cyc;
            rom_ra = wb_s0_adr[aw-1:2];
        end
        else if (bsel[3:2] == 1) begin
            tsel   = 2;
            rom_rr = wb_s1_cyc;
            rom_ra = wb_s1_adr[aw-1:2];
        end
        else if (bsel[3:2] == 2) begin
            tsel   = 4;
            rom_rr = wb_s2_cyc;
            rom_ra = wb_s2_adr[aw-1:2];
        end
        else begin
            tsel   = 8;
            rom_rr = wb_s3_cyc;
            rom_ra = wb_s3_adr[aw-1:2];
        end

        avm_s4_address = {rom_ra, bsel[1:0]};
        avm_s4_read    = rom_rr;
        aso_cyc_data   = asi_cyc_data;
        aso_cyc_valid  = asi_cyc_valid;
        rom_rd[31:24]  = avm_s4_readdata;

        wb_s0_rdt = rom_rd;
        wb_s0_ack = rom_rv[0];
        wb_s1_rdt = rom_rd;
        wb_s1_ack = rom_rv[1];
        wb_s2_rdt = rom_rd;
        wb_s2_ack = rom_rv[2];
        wb_s3_rdt = rom_rd;
        wb_s3_ack = rom_rv[3];
    end

    always @(posedge clk) begin
        if (bsel[1:0] != 3) begin
            rom_rv <= 0;
        end
        else begin
            rom_rv <= (tsel & {wb_s3_cyc, wb_s2_cyc, wb_s1_cyc, wb_s0_cyc});
        end

        if (bsel[1:0] != 0) begin
            rom_rd[23:0] <= rom_rd[31:8];
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