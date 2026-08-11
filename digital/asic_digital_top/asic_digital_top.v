`timescale 1ns/1ps
`default_nettype none

module asic_digital_top (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        start,
    input  wire        compare_high,
    input  wire        shift_en,
    output wire [3:0]  mux_select,
    output wire        ramp_reset,
    output wire        bus_reset,
    output wire        serial_data,
    output wire        data_ready,
    output wire        conversion_busy,
    output wire        conversion_done,
    output wire [1:0]  active_cell
);
    wire [23:0] conversion_codes;

    four_cell_wilkinson_controller controller (
        .clk(clk), .rst_n(rst_n), .start(start),
        .compare_high(compare_high), .mux_select(mux_select),
        .ramp_reset(ramp_reset), .bus_reset(bus_reset),
        .codes(conversion_codes), .busy(conversion_busy),
        .done(conversion_done), .active_cell(active_cell)
    );

    serial_readout #(.WIDTH(24)) readout (
        .clk(clk), .rst_n(rst_n), .load(conversion_done),
        .shift_en(shift_en), .parallel_data(conversion_codes),
        .serial_data(serial_data), .data_ready(data_ready)
    );
endmodule

`default_nettype wire
