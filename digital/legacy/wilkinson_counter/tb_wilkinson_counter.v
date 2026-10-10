`timescale 1ns/1ps
`default_nettype none

module tb_wilkinson_counter;
    reg clk = 1'b0;
    reg rst_n = 1'b0;
    reg start = 1'b0;
    reg compare_high = 1'b0;
    wire [5:0] code;
    wire valid;
    wire busy;
    wire overflow;
    integer failures = 0;
    integer i;

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

    always #25 clk = ~clk;

    task begin_conversion;
        begin
            @(negedge clk);
            compare_high = 1'b1;
            start = 1'b1;
            @(negedge clk);
            start = 1'b0;
        end
    endtask

    task expect_code;
        input [5:0] expected;
        input expected_overflow;
        begin
            if (!valid || code !== expected || overflow !== expected_overflow) begin
                $display("FAIL code=%0d expected=%0d valid=%b overflow=%b", code,
                         expected, valid, overflow);
                failures = failures + 1;
            end
        end
    endtask

    initial begin
        $dumpfile("work/wilkinson_counter.vcd");
        $dumpvars(0, tb_wilkinson_counter);

        repeat (2) @(negedge clk);
        rst_n = 1'b1;

        // Match the transistor-level slice result: comparator stays high for
        // 32 count periods, then goes low and captures code 32.
        begin_conversion();
        repeat (32) @(negedge clk);
        compare_high = 1'b0;
        @(posedge clk);
        #1 expect_code(6'd32, 1'b0);
        @(posedge clk);
        #1;
        if (valid) begin
            $display("FAIL valid must be a one-cycle pulse");
            failures = failures + 1;
        end

        // A zero-length conversion captures zero.
        begin_conversion();
        compare_high = 1'b0;
        @(posedge clk);
        #1 expect_code(6'd0, 1'b0);

        // A comparator that never trips must saturate instead of wrapping.
        begin_conversion();
        for (i = 0; i < 64; i = i + 1)
            @(posedge clk);
        #1 expect_code(6'd63, 1'b1);

        if (failures == 0) begin
            $display("PASS: wilkinson_counter self-check");
            $finish;
        end

        $fatal(1, "%0d counter checks failed", failures);
    end
endmodule

`default_nettype wire
