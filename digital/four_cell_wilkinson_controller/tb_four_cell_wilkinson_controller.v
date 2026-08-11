`timescale 1ns/1ps
`default_nettype none

module tb_four_cell_wilkinson_controller;
    reg clk = 1'b0;
    reg rst_n = 1'b0;
    reg start = 1'b0;
    reg compare_high = 1'b0;
    wire [3:0] mux_select;
    wire ramp_reset;
    wire bus_reset;
    wire [23:0] codes;
    wire busy;
    wire done;
    wire [1:0] active_cell;
    integer failures = 0;
    integer done_pulses = 0;

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

    always #25 clk = ~clk;
    always @(posedge clk)
        if (done) done_pulses = done_pulses + 1;

    task provide_crossing;
        input [1:0] expected_cell;
        input integer count;
        begin
            compare_high = 1'b1;
            wait (ramp_reset == 1'b0);
            if (active_cell !== expected_cell ||
                mux_select !== (4'b0001 << expected_cell) || bus_reset) begin
                $display("FAIL control cell=%0d select=%b bus_reset=%b",
                         active_cell, mux_select, bus_reset);
                failures = failures + 1;
            end
            repeat (count + 1) @(negedge clk);
            compare_high = 1'b0;
            wait (ramp_reset == 1'b1);
        end
    endtask

    initial begin
        $dumpfile("work/four_cell_wilkinson_controller.vcd");
        $dumpvars(0, tb_four_cell_wilkinson_controller);
        repeat (2) @(negedge clk);
        rst_n = 1'b1;
        @(negedge clk);
        start = 1'b1;
        @(negedge clk);
        start = 1'b0;

        provide_crossing(2'd0, 16);
        provide_crossing(2'd1, 20);
        provide_crossing(2'd2, 27);
        provide_crossing(2'd3, 35);
        wait (done == 1'b1);
        #1;

        if (codes !== {6'd35, 6'd27, 6'd20, 6'd16}) begin
            $display("FAIL codes=%h expected=%h", codes,
                     {6'd35, 6'd27, 6'd20, 6'd16});
            failures = failures + 1;
        end
        if (busy || mux_select != 0 || !ramp_reset || !bus_reset) begin
            $display("FAIL final control state");
            failures = failures + 1;
        end
        @(posedge clk);
        #1;
        if (done || done_pulses != 1) begin
            $display("FAIL done must pulse once");
            failures = failures + 1;
        end

        if (failures == 0) begin
            $display("PASS: four-cell Wilkinson controller self-check");
            $finish;
        end
        $fatal(1, "%0d controller checks failed", failures);
    end

    initial begin
        #20000;
        $fatal(1, "controller simulation timeout");
    end
endmodule

`default_nettype wire
