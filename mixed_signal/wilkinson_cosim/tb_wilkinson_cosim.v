`timescale 1ps/1ps
`default_nettype none

module tb_wilkinson_cosim;
    `include "analog_stimulus.vh"

    reg clk = 1'b0;
    reg rst_n = 1'b0;
    reg start = 1'b0;
    reg compare_high = 1'b1;
    wire [5:0] code;
    wire valid;
    wire busy;
    wire overflow;

    wilkinson_counter dut (
        .clk(clk),
        .rst_n(rst_n),
        .start(start),
        .compare_high(compare_high),
        .code(code),
        .valid(valid),
        .busy(busy),
        .overflow(overflow)
    );

    // 20 MHz conversion clock. Its phase places a rising edge at 100.5 ns,
    // matching the analog slice's measured conversion-start event.
    initial begin
        #500 clk = 1'b1;
        forever #25000 clk = ~clk;
    end

    initial begin
        $dumpfile("work/wilkinson_cosim.vcd");
        $dumpvars(0, tb_wilkinson_cosim);

        #50000 rst_n = 1'b1;
        #25000 start = 1'b1;
        #50000 start = 1'b0;

        // Conversion starts at 100.5 ns. Drive the digital comparator input
        // low after the transistor-level conversion interval.
        #(ANALOG_CONVERSION_PS - 24500) compare_high = 1'b0;

        wait (valid === 1'b1);
        #1;
        if (code !== ANALOG_EXPECTED_CODE || overflow !== 1'b0) begin
            $fatal(1, "mixed-signal mismatch: RTL=%0d analog=%0d overflow=%b",
                   code, ANALOG_EXPECTED_CODE, overflow);
        end

        $display("PASS: analog timing %0d ps captured RTL code %0d",
                 ANALOG_CONVERSION_PS, code);
        $finish;
    end

    initial begin
        #5000000;
        $fatal(1, "mixed-signal co-verification timeout");
    end
endmodule

`default_nettype wire
