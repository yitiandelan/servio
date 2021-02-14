// Copyright (c) 2021 TIANLAN.tech
// SPDX-License-Identifier: Apache-2.0

// Language: Verilog 2001

`timescale 1ps / 1ps

module servio_rom #(
    parameter DATA_DEPTH = 1024,
    parameter DATA_WIDTH = 8
)(
    input wire [aw-1:0] avs_s0_address,
    input wire          avs_s0_read,
    output reg [dw-1:0] avs_s0_readdata,
    output reg          avs_s0_readdatavalid,

    input wire [aw-1:0] avs_s1_address,
    input wire          avs_s1_write,
    input wire [dw-1:0] avs_s1_writedata,

    input wire          clk,
    input wire          reset
);

    localparam aw = $clog2(DATA_DEPTH);
    localparam dw = (DATA_WIDTH);

    reg  [7:0] mem [0:DATA_DEPTH-1];
    reg  [aw-1:0] raddr, waddr;

    always @(*) begin
        raddr = avs_s0_address;
        waddr = avs_s1_address;
    end

    always @(posedge clk) begin
        if (avs_s0_read) begin
            avs_s0_readdata      <= mem[raddr];
            avs_s0_readdatavalid <= 1;
        end
        else begin
            avs_s0_readdatavalid <= 0;
        end

        if (avs_s1_write) begin
            mem[waddr] <= avs_s1_writedata;
        end
    end

    // simulation
    `ifdef SERVIO_ROM_SIM
    initial begin
        $dumpfile ("waveform.vcd");
        $dumpvars (0);
    end
    `endif

endmodule