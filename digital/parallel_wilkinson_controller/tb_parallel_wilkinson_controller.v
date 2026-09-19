`timescale 1ns/1ps
`default_nettype none

module tb_parallel_wilkinson_controller;
    localparam WIDTH = 8;
    localparam CELLS = 4;

    reg clk = 1'b0;
    reg rst_n = 1'b1;
    reg start = 1'b0;
    reg [CELLS-1:0] compare_high = {CELLS{1'b0}};
    wire acquire;
    wire ramp_connect;
    wire ramp_reset;
    wire [CELLS*WIDTH-1:0] codes;
    wire [CELLS-1:0] timeout;
    wire busy;
    wire done;
    integer failures = 0;
    integer done_pulses = 0;
    integer k;

    parallel_wilkinson_controller #(.WIDTH(WIDTH), .CELLS(CELLS)) dut (
        .clk(clk), .rst_n(rst_n), .start(start),
        .compare_high(compare_high), .acquire(acquire),
        .ramp_connect(ramp_connect), .ramp_reset(ramp_reset),
        .codes(codes), .timeout(timeout), .busy(busy), .done(done)
    );

    always #25 clk = ~clk;
    always @(posedge clk)
        if (done) done_pulses = done_pulses + 1;

    // Each cell's comparator falls at its own count; a negative count means
    // "never crosses" (timeout expected).
    reg [WIDTH-1:0] expected [0:CELLS-1];
    integer crossing [0:CELLS-1];

    task automatic drop_at_count;
        input integer idx;
        input integer count;
        begin
            if (count >= 0) begin
                @(negedge ramp_reset);
                repeat (count + 1) @(negedge clk);
                compare_high[idx] = 1'b0;
            end
        end
    endtask

    task run_conversion;
        input integer c0, c1, c2, c3;
        input [CELLS-1:0] expect_timeout;
        integer n;
        begin
            crossing[0] = c0; crossing[1] = c1; crossing[2] = c2; crossing[3] = c3;
            for (n = 0; n < CELLS; n = n + 1)
                expected[n] = (crossing[n] < 0) ? {WIDTH{1'b1}} : crossing[n][WIDTH-1:0];

            compare_high = {CELLS{1'b1}};
            @(negedge clk);
            start = 1'b1;
            @(negedge clk);
            start = 1'b0;

            // Mode check while the bottom plates settle on the reset ramp.
            @(posedge clk); #1;
            if (acquire || !ramp_connect || !ramp_reset || !busy) begin
                $display("FAIL connect phase acquire=%b connect=%b reset=%b busy=%b",
                         acquire, ramp_connect, ramp_reset, busy);
                failures = failures + 1;
            end

            fork
                drop_at_count(0, crossing[0]);
                drop_at_count(1, crossing[1]);
                drop_at_count(2, crossing[2]);
                drop_at_count(3, crossing[3]);
            join

            wait (done == 1'b1);
            #1;
            for (n = 0; n < CELLS; n = n + 1) begin
                if (codes[n*WIDTH +: WIDTH] !== expected[n]) begin
                    $display("FAIL cell %0d code=%0d expected=%0d", n,
                             codes[n*WIDTH +: WIDTH], expected[n]);
                    failures = failures + 1;
                end
            end
            if (timeout !== expect_timeout) begin
                $display("FAIL timeout=%b expected=%b", timeout, expect_timeout);
                failures = failures + 1;
            end
            if (busy || !acquire || ramp_connect || !ramp_reset) begin
                $display("FAIL final mode acquire=%b connect=%b reset=%b busy=%b",
                         acquire, ramp_connect, ramp_reset, busy);
                failures = failures + 1;
            end
            @(posedge clk); #1;
            if (done) begin
                $display("FAIL done must be a single-cycle pulse");
                failures = failures + 1;
            end
            compare_high = {CELLS{1'b0}};
            repeat (3) @(negedge clk);
        end
    endtask

    initial begin
        $dumpfile("work/parallel_wilkinson_controller.vcd");
        $dumpvars(0, tb_parallel_wilkinson_controller);
        #1 rst_n = 1'b0;
        repeat (2) @(negedge clk);
        rst_n = 1'b1;
        if (!acquire || ramp_connect || !ramp_reset) begin
            $display("FAIL idle mode after reset");
            failures = failures + 1;
        end

        // 1. Four simultaneous conversions, legacy signature scaled to 8 bit.
        run_conversion(16, 20, 27, 35, 4'b0000);
        // 2. Same count on two cells, one cell near full scale.
        run_conversion(200, 200, 3, 254, 4'b0000);
        // 3. Cell 2 never crosses: code saturates, timeout flag set, others kept.
        run_conversion(40, 100, -1, 250, 4'b0100);
        // 4. Crossing exactly at the last count must still be captured.
        run_conversion(255, 0, 128, 1, 4'b0000);

        if (done_pulses != 4) begin
            $display("FAIL done pulses=%0d expected 4", done_pulses);
            failures = failures + 1;
        end
        if (failures == 0) begin
            $display("PASS: parallel Wilkinson controller self-check (8-bit, 4 cells)");
            $finish;
        end
        $fatal(1, "%0d parallel controller checks failed", failures);
    end

    initial begin
        #200000;
        $fatal(1, "parallel controller simulation timeout");
    end
endmodule

`default_nettype wire
