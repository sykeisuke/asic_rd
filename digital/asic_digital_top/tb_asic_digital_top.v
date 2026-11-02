`timescale 1ns/1ps
`default_nettype none

module tb_asic_digital_top;
    reg clk = 1'b0;
    reg rst_n = 1'b1;
    reg start = 1'b0;
    reg [3:0] dout = 4'b1111;      // comparators, armed high
    reg [3:0] q = 4'b1111;         // Analog_top latches (negative edge)
    reg shift_en = 1'b0;
    wire [3:0] s0, s1, s2;
    wire ramp_rst, cnt_clk;
    wire serial_data, data_ready, conversion_busy, conversion_done;
    wire [3:0] conversion_timeout;
    reg [31:0] shifted_data;
    integer bit_index;

    asic_digital_top dut (
        .clk(clk), .rst_n(rst_n), .start(start), .q(q), .shift_en(shift_en),
        .s0(s0), .s1(s1), .s2(s2), .ramp_rst(ramp_rst), .cnt_clk(cnt_clk),
        .serial_data(serial_data), .data_ready(data_ready),
        .conversion_busy(conversion_busy), .conversion_done(conversion_done),
        .conversion_timeout(conversion_timeout)
    );

    always #25 clk = ~clk;
    always @(negedge cnt_clk) q <= dout;

    // comparator of cell idx decides `count` + 1/5 counts after TR
    task automatic cross_at;
        input integer idx;
        input integer count;
        begin
            @(negedge ramp_rst);
            #(count * 50 + 10) dout[idx] = 1'b0;
        end
    endtask

    initial begin
        $dumpfile("work/asic_digital_top.vcd");
        $dumpvars(0, tb_asic_digital_top);
        #1 rst_n = 1'b0;
        repeat (2) @(negedge clk);
        rst_n = 1'b1;
        @(negedge clk);
        start = 1'b1;
        @(negedge clk);
        start = 1'b0;

        fork
            cross_at(0, 16);
            cross_at(1, 20);
            cross_at(2, 27);
            cross_at(3, 200);
        join_none
        wait (data_ready);
        if (conversion_timeout !== 4'b0000)
            $fatal(1, "unexpected timeout flags %b", conversion_timeout);

        shifted_data = 32'd0;
        for (bit_index = 0; bit_index < 32; bit_index = bit_index + 1) begin
            @(negedge clk);
            shifted_data[bit_index] = serial_data;
            shift_en = 1'b1;
            @(negedge clk);
            shift_en = 1'b0;
        end
        @(posedge clk);
        #1;

        if (shifted_data !== {8'd200, 8'd27, 8'd20, 8'd16})
            $fatal(1, "serial mismatch got=%h expected=%h", shifted_data,
                   {8'd200, 8'd27, 8'd20, 8'd16});
        if (data_ready)
            $fatal(1, "data_ready did not clear after 32 shifts");
        #30;
        if (s2 !== 4'b1111 || s0 !== 4'b1111 || s1 !== 4'b0000 || !ramp_rst)
            $fatal(1, "cells not back to track: s2=%b s0=%b s1=%b ramp_rst=%b", s2, s0, s1, ramp_rst);

        $display("PASS: sample-to-serial digital flow codes=16,20,27,200 (8-bit x4, 32-bit frame, Analog_top interface)");
        $finish;
    end

    initial begin
        #60000;
        $fatal(1, "digital top timeout");
    end
endmodule

`default_nettype wire
