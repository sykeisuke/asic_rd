`timescale 1ns/1ps
`default_nettype none

module tb_asic_digital_top;
    reg clk = 1'b0;
    reg rst_n = 1'b1;
    reg start = 1'b0;
    reg [3:0] crossed = 4'b0000;
    reg shift_en = 1'b0;
    wire acquire;
    wire ramp_connect;
    wire ramp_reset;
    wire serial_data;
    wire data_ready;
    wire conversion_busy;
    wire conversion_done;
    wire [3:0] conversion_timeout;
    reg [31:0] shifted_data;
    integer bit_index;

    asic_digital_top dut (
        .clk(clk), .rst_n(rst_n), .start(start),
        .crossed(crossed), .shift_en(shift_en),
        .acquire(acquire), .ramp_connect(ramp_connect),
        .ramp_reset(ramp_reset), .serial_data(serial_data),
        .data_ready(data_ready), .conversion_busy(conversion_busy),
        .conversion_done(conversion_done),
        .conversion_timeout(conversion_timeout)
    );

    always #25 clk = ~clk;

    // Cell model: crossing in counter cycle `count`, flag raised by the
    // cell's flip-flop at the edge ending that cycle.
    task automatic cell_flag;
        input integer idx;
        input integer count;
        begin
            @(negedge ramp_reset);
            repeat (count + 1) @(posedge clk);
            #1 crossed[idx] = 1'b1;
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
            cell_flag(0, 16);
            cell_flag(1, 20);
            cell_flag(2, 27);
            cell_flag(3, 200);
        join
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
        if (!acquire || ramp_connect || !ramp_reset)
            $fatal(1, "analog mode did not return to acquire");

        $display("PASS: sample-to-serial digital flow codes=16,20,27,200 (8-bit x4, 32-bit frame, synchronous capture)");
        $finish;
    end

    initial begin
        #60000;
        $fatal(1, "digital top timeout");
    end
endmodule

`default_nettype wire
