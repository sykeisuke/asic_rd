`timescale 1ps/1ps
`default_nettype none

module tb_four_cell_cosim;
    `include "analog_stimulus.vh"

    reg clk = 1'b0;
    reg rst_n = 1'b1;
    reg start = 1'b0;
    reg compare_high = 1'b0;
    wire [3:0] mux_select;
    wire ramp_reset;
    wire bus_reset;
    wire [23:0] codes;
    wire busy;
    wire done;
    wire [1:0] active_cell;

    four_cell_wilkinson_controller dut (
        .clk(clk),
        .rst_n(rst_n),
        .start(start),
        .compare_high(compare_high),
        .mux_select(mux_select),
        .ramp_reset(ramp_reset),
        .bus_reset(bus_reset),
        .codes(codes),
        .busy(busy),
        .done(done),
        .active_cell(active_cell)
    );

    always #25000 clk = ~clk;

    task drive_analog_crossing;
        input [1:0] expected_cell;
        input integer conversion_ps;
        begin
            compare_high = 1'b1;
            @(negedge ramp_reset);
            if (active_cell !== expected_cell)
                $fatal(1, "cell sequence mismatch: got %0d expected %0d",
                       active_cell, expected_cell);
            #(conversion_ps) compare_high = 1'b0;
            @(posedge ramp_reset);
        end
    endtask

    initial begin
        $dumpfile("work/four_cell_cosim.vcd");
        $dumpvars(0, tb_four_cell_cosim);
        #1 rst_n = 1'b0;
        repeat (2) @(negedge clk);
        rst_n = 1'b1;
        @(negedge clk);
        start = 1'b1;
        @(negedge clk);
        start = 1'b0;

        drive_analog_crossing(2'd0, ANALOG_TIME0_PS);
        drive_analog_crossing(2'd1, ANALOG_TIME1_PS);
        drive_analog_crossing(2'd2, ANALOG_TIME2_PS);
        drive_analog_crossing(2'd3, ANALOG_TIME3_PS);
        wait (done === 1'b1);
        #1;

        if (codes !== {ANALOG_CODE3, ANALOG_CODE2,
                       ANALOG_CODE1, ANALOG_CODE0}) begin
            $fatal(1, "four-cell mismatch: RTL=%h analog=%h", codes,
                   {ANALOG_CODE3, ANALOG_CODE2, ANALOG_CODE1, ANALOG_CODE0});
        end
        $display("PASS: analog times captured RTL codes %0d %0d %0d %0d",
                 codes[5:0], codes[11:6], codes[17:12], codes[23:18]);
        $finish;
    end

    initial begin
        #20000000;
        $fatal(1, "four-cell co-simulation timeout");
    end
endmodule

`default_nettype wire
