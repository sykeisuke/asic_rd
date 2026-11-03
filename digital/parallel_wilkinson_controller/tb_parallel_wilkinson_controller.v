`timescale 1ns/1ps
`default_nettype none

// Self-check against the Analog_top v7 timeline (tb_params.inc): the
// testbench models the macro's sampling sequencer (cell k's S2 opens at the
// k-th rising edge after the edge that first sees acq low) and the cell
// latch as a negative-edge flop on q <= dout, with dout falling at a chosen
// time after TR. It checks acq (a clean flop output, one fall and one rise
// per conversion), ramp_rst at TS_3 + 6 clocks, and
// code = floor((t_qfall - TR) / TCOUNT).
module tb_parallel_wilkinson_controller;
    localparam WIDTH = 8;
    localparam CELLS = 4;
    localparam integer TCOUNT_PS = 50000;   // 20 MHz, in ps

    reg clk = 1'b0;
    reg rst_n = 1'b1;
    reg start = 1'b0;
    reg  [CELLS-1:0] dout = {CELLS{1'b1}};   // comparator outputs (high = armed)
    reg  [CELLS-1:0] q    = {CELLS{1'b1}};   // cell latches, negative edge
    wire acq;
    wire ramp_rst;
    wire [CELLS*WIDTH-1:0] codes;
    wire [CELLS-1:0] timeout;
    wire busy, done;
    integer failures = 0;
    integer done_pulses = 0;

    parallel_wilkinson_controller #(.WIDTH(WIDTH), .CELLS(CELLS)) dut (
        .clk(clk), .rst_n(rst_n), .start(start), .q(q),
        .acq(acq), .ramp_rst(ramp_rst),
        .codes(codes), .timeout(timeout), .busy(busy), .done(done)
    );

    always #25 clk = ~clk;
    always @(negedge clk) q <= dout;          // Analog_top latch (dfxtn_2)
    always @(posedge clk) if (done) done_pulses = done_pulses + 1;

    // The macro's sequencer (mixed_signal/sample_seq): a token chain on the
    // rising edge. s2[k] falls at the k-th edge after the edge that sees
    // acq low; all close again once acq is high.
    reg [CELLS-1:0] s2 = {CELLS{1'b1}};
    always @(posedge clk) s2 <= acq ? {CELLS{1'b1}} : {s2[CELLS-2:0], 1'b0};

    // Timeline, in ps
    integer t_edge;                // last rising clock edge
    integer t_acq_fall, t_acq_rise;
    integer acq_falls, acq_rises;
    integer t_s2 [0:CELLS-1];
    integer t_tr;
    integer t_edge_at_fall;        // the edge acq fell after
    always @(posedge clk) t_edge = $realtime * 1000;
    always @(negedge acq) t_edge_at_fall = t_edge;
    always @(negedge acq) begin t_acq_fall = $realtime * 1000; acq_falls = acq_falls + 1; end
    always @(posedge acq) begin t_acq_rise = $realtime * 1000; acq_rises = acq_rises + 1; end
    genvar g;
    generate
        for (g = 0; g < CELLS; g = g + 1) begin : mon
            always @(negedge s2[g]) t_s2[g] = $realtime * 1000;
        end
    endgenerate
    always @(negedge ramp_rst) t_tr = $realtime * 1000;

    task check_timeline;
        integer k;
        begin
            // acq is a flop output: it falls right after a rising edge, so
            // the next edge (TS_0) sees it low (sample_seq setup ~0.3 ns).
            if (acq_falls != 1 || acq_rises != 1) begin
                $display("FAIL acq edges: %0d falls, %0d rises (1 each expected)", acq_falls, acq_rises); failures = failures + 1;
            end
            if (t_acq_fall - t_edge_at_fall > 1000) begin
                $display("FAIL acq falls %0d ps after a clock edge", t_acq_fall - t_edge_at_fall); failures = failures + 1;
            end
            if (t_s2[0] - t_acq_fall < TCOUNT_PS - 1100 || t_s2[0] - t_acq_fall > TCOUNT_PS + 100) begin
                $display("FAIL TS_0 - acq fall = %0d ps (one clock expected)", t_s2[0] - t_acq_fall); failures = failures + 1;
            end
            for (k = 1; k < CELLS; k = k + 1) begin
                if (t_s2[k] - t_s2[k-1] < TCOUNT_PS - 100 || t_s2[k] - t_s2[k-1] > TCOUNT_PS + 100) begin
                    $display("FAIL TSPACE cell %0d: %0d ps", k, t_s2[k] - t_s2[k-1]); failures = failures + 1;
                end
            end
            if (t_tr - t_s2[CELLS-1] < 6 * TCOUNT_PS - 100 || t_tr - t_s2[CELLS-1] > 6 * TCOUNT_PS + 100) begin
                $display("FAIL TR - TS3 = %0d ps", t_tr - t_s2[CELLS-1]); failures = failures + 1;
            end
            // acq returns high after the ramp is reset (re-track after hold).
            if (t_acq_rise <= t_tr || !ramp_rst) begin
                $display("FAIL acq rose at %0d ps, TR %0d ps, ramp_rst=%b", t_acq_rise, t_tr, ramp_rst); failures = failures + 1;
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
            acq_falls = 0; acq_rises = 0;
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
            if (busy || !ramp_rst || !acq) begin
                $display("FAIL final state busy=%b ramp_rst=%b acq=%b", busy, ramp_rst, acq); failures = failures + 1;
            end
            #60;
            if (s2 !== {CELLS{1'b1}}) begin
                $display("FAIL cells not back to track: s2=%b", s2); failures = failures + 1;
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
            $display("PASS: parallel Wilkinson controller self-check (8-bit, 4 cells, Analog_top v7 timeline, acq + synchronous capture)");
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
