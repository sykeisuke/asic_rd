`timescale 1ns/1ps
`default_nettype none

module tb_wilkinson_gray_counter;
    reg clk = 1'b0;
    reg rst_n = 1'b1;
    reg start = 1'b0;
    reg compare_high = 1'b0;
    wire [5:0] code;
    wire valid;
    wire busy;
    wire overflow;
    integer failures = 0;

    wilkinson_gray_counter dut (
        .clk(clk), .rst_n(rst_n), .start(start),
        .compare_high(compare_high), .code(code), .valid(valid),
        .busy(busy), .overflow(overflow)
    );

    always #25 clk = ~clk;

    task run_conversion;
        input integer crossing_ns;
        input [5:0] expected;
        begin
            @(negedge clk);
            compare_high = 1'b1;
            start = 1'b1;
            @(negedge clk);
            start = 1'b0;
            // The delay argument is measured from the preceding counter-start
            // edge; this task resumes 25 ns later at the falling clock edge.
            #(crossing_ns - 25) compare_high = 1'b0;
            wait (valid);
            #1;
            if (code !== expected || overflow) begin
                $display("FAIL crossing=%0d code=%0d expected=%0d", crossing_ns,
                         code, expected);
                failures = failures + 1;
            end
            @(negedge clk);
        end
    endtask

    initial begin
        $dumpfile("work/wilkinson_gray_counter.vcd");
        $dumpvars(0, tb_wilkinson_gray_counter);
        #1 rst_n = 1'b0;
        repeat (2) @(negedge clk);
        rst_n = 1'b1;

        run_conversion(831, 6'd16);
        run_conversion(1040, 6'd20);

        if (failures == 0) begin
            $display("PASS: Gray counter asynchronous capture self-check");
            $finish;
        end
        $fatal(1, "%0d Gray counter checks failed", failures);
    end

    initial begin
        #10000;
        $fatal(1, "Gray counter timeout");
    end
endmodule

`default_nettype wire
