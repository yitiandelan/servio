// Copyright (c) 2021 TIANLAN.tech
// SPDX-License-Identifier: Apache-2.0

// Language: Verilog 2001

`timescale 1ps / 1ps

module servio #(
    parameter DATA_DEPTH = 1024
)(
    input wire [aw-1:0] avs_rom_address,
    input wire          avs_rom_write,
    input wire [7:0]    avs_rom_writedata,

    input wire          clk,
    input wire          reset
);

    localparam aw = $clog2(DATA_DEPTH);
    localparam RESET_STRATEGY = "MINI";

    reg         stop = 1;
    reg         sclr;

    wire [31:0] wb_sm_adr [0:4-1];
    wire        wb_sm_cyc [0:4-1];
    wire [31:0] wb_sm_rdt [0:4-1];
    wire        wb_sm_ack [0:4-1];

    wire [aw-1:0] avm_ibus_ra;
    wire [7:0]    avm_ibus_rd;
    wire          avm_ibus_rr, avm_ibus_rv;

    always @(posedge clk) begin
        sclr <= (reset | stop);
    end

    generate
    genvar i;
    for (i=0; i<4; i=i+1) begin: sm

    wire 	    rf_wreq;
    wire 	    rf_rreq;
    wire [4:0]  wreg0;
    wire [4:0]  wreg1;
    wire 	    wen0;
    wire 	    wen1;
    wire 	    wdata0;
    wire 	    wdata1;
    wire [4:0]  rreg0;
    wire [4:0]  rreg1;
    wire 	    rf_ready;
    wire 	    rdata0;
    wire 	    rdata1;

    wire [8:0]  waddr;
    wire [1:0]  wdata;
    wire 	    wen;
    wire [8:0]  raddr;
    wire [1:0]  rdata;

    serv_top #(
        .RESET_PC       (0),
        .RESET_STRATEGY ("MINI"),
        .WITH_CSR       (0)
        ) cpu (
        .clk            (clk),
        .i_rst          (reset),
        .i_timer_irq    (1'b0),

        .o_rf_rreq      (rf_rreq),
        .o_rf_wreq      (rf_wreq),
        .i_rf_ready     (rf_ready),
        .o_wreg0        (wreg0),
        .o_wreg1        (wreg1),
        .o_wen0         (wen0),
        .o_wen1         (wen1),
        .o_wdata0       (wdata0),
        .o_wdata1       (wdata1),
        .o_rreg0        (rreg0),
        .o_rreg1        (rreg1),
        .i_rdata0       (rdata0),
        .i_rdata1       (rdata1),

        .o_ibus_adr     (wb_sm_adr[i][9:0]),
        .o_ibus_cyc     (wb_sm_cyc[i]),
        .i_ibus_rdt     (wb_sm_rdt[i]),
        .i_ibus_ack     (wb_sm_ack[i]),

        .o_dbus_adr     (),
        .o_dbus_dat     (),
        .o_dbus_sel     (),
        .o_dbus_we      (),
        .o_dbus_cyc     (),
        .i_dbus_rdt     (32'd0),
        .i_dbus_ack     (1'b0)
    );

    assign wb_sm_adr[i][31:10] = 0;

    serv_rf_ram #(
        .width          (2),
        .csr_regs       (0)
    ) rf_ram (
        .i_clk          (clk),
        .i_waddr        (waddr),
        .i_wdata        (wdata),
        .i_wen          (wen),
        .i_raddr        (raddr),
        .o_rdata        (rdata)
    );

    serv_rf_ram_if #(
        .width          (2),
        .reset_strategy (RESET_STRATEGY),
        .csr_regs       (0)
    ) rf_ram_if (
        .i_clk          (clk),
        .i_rst          (reset),
        .i_wreq         (rf_wreq),
        .i_rreq         (rf_rreq),
        .o_ready        (rf_ready),
        .i_wreg0        (wreg0),
        .i_wreg1        (wreg1),
        .i_wen0         (wen0),
        .i_wen1         (wen1),
        .i_wdata0       (wdata0),
        .i_wdata1       (wdata1),
        .i_rreg0        (rreg0),
        .i_rreg1        (rreg1),
        .o_rdata0       (rdata0),
        .o_rdata1       (rdata1),
        .o_waddr        (waddr),
        .o_wdata        (wdata),
        .o_wen          (wen),
        .o_raddr        (raddr),
        .i_rdata        (rdata)
    );

    end
    endgenerate

    servio_mux #(
        .DATA_DEPTH             (DATA_DEPTH)
        ) mux (
        .wb_s0_adr              (wb_sm_adr[0]),
        .wb_s0_cyc              (wb_sm_cyc[0]),
        .wb_s0_rdt              (wb_sm_rdt[0]),
        .wb_s0_ack              (wb_sm_ack[0]),

        .wb_s1_adr              (wb_sm_adr[1]),
        .wb_s1_cyc              (wb_sm_cyc[1]),
        .wb_s1_rdt              (wb_sm_rdt[1]),
        .wb_s1_ack              (wb_sm_ack[1]),

        .wb_s2_adr              (wb_sm_adr[2]),
        .wb_s2_cyc              (wb_sm_cyc[2]),
        .wb_s2_rdt              (wb_sm_rdt[2]),
        .wb_s2_ack              (wb_sm_ack[2]),

        .wb_s3_adr              (wb_sm_adr[3]),
        .wb_s3_cyc              (wb_sm_cyc[3]),
        .wb_s3_rdt              (wb_sm_rdt[3]),
        .wb_s3_ack              (wb_sm_ack[3]),

        .avm_s4_address         (avm_ibus_ra),
        .avm_s4_read            (avm_ibus_rr),
        .avm_s4_readdata        (avm_ibus_rd),
        .avm_s4_readdatavalid   (avm_ibus_rv),

        .clk                    (clk),
        .reset                  (sclr)
    );

    servio_rom #(
        .DATA_DEPTH             (DATA_DEPTH),
        .DATA_WIDTH             (8)
        ) rom (
        .avs_s0_address         (avm_ibus_ra),
        .avs_s0_read            (avm_ibus_rr),
        .avs_s0_readdata        (avm_ibus_rd),
        .avs_s0_readdatavalid   (avm_ibus_rv),

        .avs_s1_address         (avs_rom_address),
        .avs_s1_write           (avs_rom_write),
        .avs_s1_writedata       (avs_rom_writedata),

        .clk                    (clk),
        .reset                  (reset)
    );

    // simulation
    `ifdef SERVIO_SIM
    initial begin
        $dumpfile ("waveform.vcd");
        $dumpvars (0);
    end
    `endif

endmodule