`timescale 1ns/1ps
`default_nettype none

// Self-check against the Analog_top timeline (tb_params.inc): the testbench
// models the cell latch as a negative-edge flop on q <= dout, with dout
// falling at a chosen time after TR, and checks the sampling sequence
// (S2 falling one clock apart, S0 after TNOV, S1 after 2 TNOV, ramp_rst at
// TS3 + 6 clocks) and code = floor((t_qfall - TR) / TCOUNT).
module tb_parallel_wilkinson_controller;
    localparam WIDTH = 8;
    localparam CELLS = 4;
    localparam integer TCOUNT_PS = 50000;   // 20 MHz, in ps

    reg clk = 1'b0;
    reg rst_n = 1'b1;
    reg start = 1'b0;
    reg  [CELLS-1:0] dout = {CELLS{1'b1}};   // comparator outputs (high = armed)
    reg  [CELLS-1:0] q    = {CELLS{1'b1}};   // cell latches, negative edge
    wire [CELLS-1:0] s0, s1, s2;
    wire ramp_rst;
    wire [CELLS*WIDTH-1:0] codes;
    wire [CELLS-1:0] timeout;
    wire busy, done;
    integer failures = 0;
    integer done_pulses = 0;

    parallel_wilkinson_controller #(.WIDTH(WIDTH), .CELLS(CELLS)) dut (
        .clk(clk), .rst_n(rst_n), .start(start), .q(q),
        .s2(s2), .s0(s0), .s1(s1), .ramp_rst(ramp_rst),
        .codes(codes), .timeout(timeout), .busy(busy), .done(done)
    );

    always #25 clk = ~clk;
    always @(negedge clk) q <= dout;          // Analog_top latch (dfxtn_2)
    always @(posedge clk) if (done) done_pulses = done_pulses + 1;

    // Timeline checks
    integer t_s2 [0:CELLS-1];      // ps
    integer t_s0 [0:CELLS-1];
    integer t_s1 [0:CELLS-1];
    integer t_tr;
    genvar g;
    generate
        for (g = 0; g < CELLS; g = g + 1) begin : mon
            always @(negedge s2[g]) t_s2[g] = $realtime * 1000;
            always @(negedge s0[g]) t_s0[g] = $realtime * 1000;
            always @(posedge s1[g]) t_s1[g] = $realtime * 1000;
        end
    endgenerate
    always @(negedge ramp_rst) t_tr = $realtime * 1000;

    task check_timeline;
        integer k;
        begin
            for (k = 0; k < CELLS; k = k + 1) begin
                if (k > 0 && (t_s2[k] - t_s2[k-1] < TCOUNT_PS - 100 || t_s2[k] - t_s2[k-1] > TCOUNT_PS + 100)) begin
                    $display("FAIL TSPACE cell %0d: %0d ps", k, t_s2[k] - t_s2[k-1]); failures = failures + 1;
                end
                if (t_s0[k] - t_s2[k] < 4000 || t_s0[k] - t_s2[k] > 6000) begin
                    $display("FAIL TNOV cell %0d: s0 opens %0d ps after s2", k, t_s0[k] - t_s2[k]); failures = failures + 1;
                end
                if (t_s1[k] - t_s2[k] < 9000 || t_s1[k] - t_s2[k] > 11000) begin
                    $display("FAIL TCONN cell %0d: s1 closes %0d ps after s2", k, t_s1[k] - t_s2[k]); failures = failures + 1;
                end
            end
            if (t_tr - t_s2[CELLS-1] < 6 * TCOUNT_PS - 100 || t_tr - t_s2[CELLS-1] > 6 * TCOUNT_PS + 100) begin
                $display("FAIL TR - TS3 = %0d ps", t_tr - t_s2[CELLS-1]); failures = failures + 1;
            end
        end
    endtask

    // dout of cell idx falls `t_after_tr` ps after TR (negative: never).
    task automatic cross_at;
        input integer idx;
        input integer t_after_tr;
        begin
            if (t_after_tr >= 0) begin
                @(negedge ramp_rst);
                #(t_after_tr / 1000.0) dout[idx] = 1'b0;
            end
        end
    endtask

    reg [WIDTH-1:0] expected [0:CELLS-1];
    integer tcross [0:CELLS-1];

    task run_conversion;
        input integer c0, c1, c2, c3;   // dout fall times after TR (ps); <0 never
        input [CELLS-1:0] expect_timeout;
        integer n;
        integer kfall;
        begin
            tcross[0] = c0; tcross[1] = c1; tcross[2] = c2; tcross[3] = c3;
            for (n = 0; n < CELLS; n = n + 1) begin
                if (tcross[n] < 0) expected[n] = {WIDTH{1'b1}};
                else begin
                    // q falls at the first falling clock edge after dout falls;
                    // falling edges sit at TR + (k + 1/2) TCOUNT, k = 0, 1, ...
                    // -> the k of that edge is the code (floor((t_qfall - TR)/TCOUNT)).
                    kfall = (tcross[n] + TCOUNT_PS / 2) / TCOUNT_PS;   // first k with (k+1/2)T > t
                    if (kfall >= 256) expected[n] = {WIDTH{1'b1}};
                    else expected[n] = kfall[WIDTH-1:0];
                end
            end
            dout = {CELLS{1'b1}};
            @(negedge clk); start = 1'b1;
            @(negedge clk); start = 1'b0;
            fork
                cross_at(0, tcross[0]);
                cross_at(1, tcross[1]);
                cross_at(2, tcross[2]);
                cross_at(3, tcross[3]);
            join_none
            wait (done == 1'b1); #1;
            check_timeline;
            for (n = 0; n < CELLS; n = n + 1)
                if (codes[n*WIDTH +: WIDTH] !== expected[n]) begin
                    $display("FAIL cell %0d code=%0d expected=%0d (dout fell %0d ps after TR)",
                             n, codes[n*WIDTH +: WIDTH], expected[n], tcross[n]);
                    failures = failures + 1;
                end
            if (timeout !== expect_timeout) begin
                $display("FAIL timeout=%b expected=%b", timeout, expect_timeout); failures = failures + 1;
            end
            if (busy || !ramp_rst || s1 !== {CELLS{1'b0}}) begin
                $display("FAIL final state busy=%b ramp_rst=%b s1=%b", busy, ramp_rst, s1); failures = failures + 1;
            end
            #30;
            if (s2 !== {CELLS{1'b1}} || s0 !== {CELLS{1'b1}}) begin
                $display("FAIL not back to track: s2=%b s0=%b", s2, s0); failures = failures + 1;
            end
            dout = {CELLS{1'b1}};
            repeat (4) @(negedge clk);
        end
    endtask

    initial begin
        $dumpfile("work/parallel_wilkinson_controller.vcd");
        $dumpvars(0, tb_parallel_wilkinson_controller);
        #1 rst_n = 1'b0;
        repeat (2) @(negedge clk);
        rst_n = 1'b1;

        // 1. Analog_top's functional record: mid-codes 16/80/160/240 cross just
        //    after (n + 1/2) counts (1 ns past the falling edge, as the
        //    comparator delay makes them) -> codes 17/81/161/241 by the latch rule.
        run_conversion(16 * 50000 + 26000, 80 * 50000 + 26000, 160 * 50000 + 26000, 240 * 50000 + 26000, 4'b0000);
        // 2. Crossings just before and after a falling clock edge, two equal.
        run_conversion(20 * 50000 + 20000, 20 * 50000 + 30000, 20 * 50000 + 30000, 3 * 50000, 4'b0000);
        // 3. Cell 2 never crosses: 255 + timeout; others kept.
        run_conversion(40 * 50000 + 10000, 100 * 50000 + 10000, -1, 250 * 50000 + 10000, 4'b0100);
        // 4. Crossing in the last count and in the first.
        run_conversion(255 * 50000 + 10000, 10000, 128 * 50000 + 10000, 50000 + 10000, 4'b0000);

        if (done_pulses != 4) begin
            $display("FAIL done pulses=%0d expected 4", done_pulses); failures = failures + 1;
        end
        if (failures == 0) begin
            $display("PASS: parallel Wilkinson controller self-check (8-bit, 4 cells, Analog_top timeline, synchronous capture)");
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
