`timescale 1ps/1ps
`default_nettype none

module tb_four_cell_phase_sweep;
    `include "analog_stimulus.vh"

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
    integer offset_ps;
    integer expected0;
    integer expected1;
    integer expected2;
    integer expected3;

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

    task drive_crossing;
        input [1:0] expected_cell;
        input integer nominal_ps;
        begin
            compare_high = 1'b1;
            @(negedge ramp_reset);
            if (active_cell !== expected_cell)
                $fatal(1, "cell sequence mismatch");
            #(nominal_ps + offset_ps) compare_high = 1'b0;
            @(posedge ramp_reset);
        end
    endtask

    initial begin
        if (!$value$plusargs("OFFSET_PS=%d", offset_ps))
            offset_ps = 0;
        expected0 = (ANALOG_TIME0_PS + offset_ps) / 50000;
        expected1 = (ANALOG_TIME1_PS + offset_ps) / 50000;
        expected2 = (ANALOG_TIME2_PS + offset_ps) / 50000;
        expected3 = (ANALOG_TIME3_PS + offset_ps) / 50000;

        repeat (2) @(negedge clk);
        rst_n = 1'b1;
        @(negedge clk);
        start = 1'b1;
        @(negedge clk);
        start = 1'b0;

        drive_crossing(2'd0, ANALOG_TIME0_PS);
        drive_crossing(2'd1, ANALOG_TIME1_PS);
        drive_crossing(2'd2, ANALOG_TIME2_PS);
        drive_crossing(2'd3, ANALOG_TIME3_PS);
        wait (done === 1'b1);
        #1;

        if (codes[5:0] !== expected0[5:0] ||
            codes[11:6] !== expected1[5:0] ||
            codes[17:12] !== expected2[5:0] ||
            codes[23:18] !== expected3[5:0]) begin
            $fatal(1, "phase mismatch offset=%0d codes=%0d,%0d,%0d,%0d expected=%0d,%0d,%0d,%0d",
                   offset_ps, codes[5:0], codes[11:6], codes[17:12],
                   codes[23:18], expected0, expected1, expected2, expected3);
        end
        $display("SWEEP offset_ps=%0d codes=%0d,%0d,%0d,%0d",
                 offset_ps, codes[5:0], codes[11:6], codes[17:12], codes[23:18]);
        $finish;
    end

    initial begin
        #20000000;
        $fatal(1, "phase sweep timeout");
    end
endmodule

`default_nettype wire
