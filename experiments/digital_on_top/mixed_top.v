`timescale 1ns/1ps
`default_nettype none

// Digital-on-top integration experiment: the 8-bit parallel digital top plus
// one hand-made analog hard macro (minimum comparator, cell 0) placed and
// routed by LibreLane. Cells 1..3 keep external comparator inputs.
module mixed_top (
`ifdef USE_POWER_PINS
    inout  wire        VDD,
    inout  wire        VSS,
`endif
    input  wire        clk,
    input  wire        rst_n,
    input  wire        start,
    input  wire [3:1]  compare_high_ext,
    input  wire        cmp0_sample,
    input  wire        cmp0_ramp,
    input  wire        cmp0_bias,
    input  wire        shift_en,
    output wire        acquire,
    output wire        ramp_connect,
    output wire        ramp_reset,
    output wire        serial_data,
    output wire        data_ready,
    output wire        conversion_busy,
    output wire        conversion_done,
    output wire [3:0]  conversion_timeout,
    output wire        cmp0_out_mon
);
    wire cmp0_dout;
    assign cmp0_out_mon = cmp0_dout;

    comparator_min cmp0 (
`ifdef USE_POWER_PINS
        .vdd(VDD), .vss(VSS),
`endif
        .sample(cmp0_sample), .ramp(cmp0_ramp), .bias(cmp0_bias), .dout(cmp0_dout)
    );

    asic_digital_top digital (
        .clk(clk), .rst_n(rst_n), .start(start),
        .compare_high({compare_high_ext, cmp0_dout}), .shift_en(shift_en),
        .acquire(acquire), .ramp_connect(ramp_connect), .ramp_reset(ramp_reset),
        .serial_data(serial_data), .data_ready(data_ready),
        .conversion_busy(conversion_busy), .conversion_done(conversion_done),
        .conversion_timeout(conversion_timeout)
    );
endmodule

`default_nettype wire
