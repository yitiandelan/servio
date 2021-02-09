`timescale 1ps / 1ps

module servio_rom #(
    parameter DATA_DEPTH = 1024,
    parameter DATA_WIDTH = 8
)(
    input wire [aw-1:0] wb_s0_adr,
    input wire          wb_s0_cyc,
    output reg [dw-1:0] wb_s0_rdt,
    output reg          wb_s0_ack,

    input wire [aw-1:0] wb_s1_adr,
    input wire          wb_s1_cyc,
    input wire          wb_s1_we,
    input wire [dw-1:0] wb_s1_dat,

    input  wire         clk,
    input  wire         reset
);

    localparam aw = $clog2(DATA_DEPTH);
    localparam dw = (DATA_WIDTH);

    reg  [7:0] mem [0:DATA_DEPTH-1];
    reg  [aw-1:0] raddr, waddr;

    always @(*) begin
        raddr = wb_s0_adr;
        waddr = wb_s1_adr;
    end

    always @(posedge clk) begin
        if (wb_s0_cyc) begin
            wb_s0_rdt <= mem[raddr];
            wb_s0_ack <= 1;
        end
        else begin
            wb_s0_ack <= 0;
        end

        if (wb_s1_cyc & wb_s1_we) begin
            mem[waddr] <= wb_s1_dat;
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