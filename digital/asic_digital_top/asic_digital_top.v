`timescale 1ns/1ps
`default_nettype none

// Tape-out 1 digital top (architecture of 2026-09-18): four storage cells are
// converted in parallel by one broadcast ramp and one comparator per cell;
// four 8-bit results are read out through a 32-bit synchronous serial port.
module asic_digital_top (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        start,
    input  wire [3:0]  compare_high,
    input  wire        shift_en,
    output wire        acquire,
    output wire        ramp_connect,
    output wire        ramp_reset,
    output wire        serial_data,
    output wire        data_ready,
    output wire        conversion_busy,
    output wire        conversion_done,
    output wire [3:0]  conversion_timeout
);
    wire [31:0] conversion_codes;

    parallel_wilkinson_controller #(.WIDTH(8), .CELLS(4)) controller (
        .clk(clk), .rst_n(rst_n), .start(start),
        .compare_high(compare_high), .acquire(acquire),
        .ramp_connect(ramp_connect), .ramp_reset(ramp_reset),
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
