`timescale 1ns/1ps
`default_nettype none

// Tape-out 1 digital top for the Analog_top macro (mixed_signal/Analog_top):
// four storage cells converted in parallel on one ramp, one comparator and
// one clocked latch per cell. The digital top generates the sampling
// sequence (s2/s0/s1 per cell, one cell per clock, switch order by delay
// lines), the ramp reset, and the count; it samples the cells' latched
// flags q[3:0] and reads the four 8-bit codes out through a 32-bit
// synchronous serial port. cnt_clk is the conversion clock handed to the
// macro's latches (they sample on its falling edge).
module asic_digital_top (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        start,
    input  wire [3:0]  q,
    input  wire        shift_en,
    output wire [3:0]  s0,
    output wire [3:0]  s1,
    output wire [3:0]  s2,
    output wire        ramp_rst,
    output wire        cnt_clk,
    output wire        serial_data,
    output wire        data_ready,
    output wire        conversion_busy,
    output wire        conversion_done,
    output wire [3:0]  conversion_timeout
);
    wire [31:0] conversion_codes;

    assign cnt_clk = clk;

    parallel_wilkinson_controller #(.WIDTH(8), .CELLS(4)) controller (
        .clk(clk), .rst_n(rst_n), .start(start), .q(q),
        .s2(s2), .s0(s0), .s1(s1), .ramp_rst(ramp_rst),
        .codes(conversion_codes), .timeout(conversion_timeout),
        .busy(conversion_busy), .done(conversion_done)
    );

    serial_readout #(.WIDTH(32)) readout (
        .clk(clk), .rst_n(rst_n), .load(conversion_done),
        .shift_en(shift_en), .parallel_data(conversion_codes),
        .serial_data(serial_data), .data_ready(data_ready)
    );
endmodule

`default_nettype wire
