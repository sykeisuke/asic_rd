`timescale 1ns/1ps
`default_nettype none

module tb_asic_digital_top;
    reg clk = 1'b0;
    reg rst_n = 1'b1;
    reg start = 1'b0;
    reg compare_high = 1'b0;
    reg shift_en = 1'b0;
    wire [3:0] mux_select;
    wire ramp_reset;
    wire bus_reset;
    wire serial_data;
    wire data_ready;
    wire conversion_busy;
    wire conversion_done;
    wire [1:0] active_cell;
    reg [23:0] shifted_data;
    integer bit_index;

    asic_digital_top dut (
        .clk(clk), .rst_n(rst_n), .start(start),
        .compare_high(compare_high), .shift_en(shift_en),
        .mux_select(mux_select), .ramp_reset(ramp_reset),
        .bus_reset(bus_reset), .serial_data(serial_data),
        .data_ready(data_ready), .conversion_busy(conversion_busy),
        .conversion_done(conversion_done), .active_cell(active_cell)
    );

    always #25 clk = ~clk;

    task provide_crossing;
        input integer count;
        begin
            compare_high = 1'b1;
            @(negedge ramp_reset);
            repeat (count + 1) @(negedge clk);
            compare_high = 1'b0;
            @(posedge ramp_reset);
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

        provide_crossing(16);
        provide_crossing(20);
        provide_crossing(27);
        provide_crossing(35);
        wait (data_ready);

        shifted_data = 24'd0;
        for (bit_index = 0; bit_index < 24; bit_index = bit_index + 1) begin
            @(negedge clk);
            shifted_data[bit_index] = serial_data;
            shift_en = 1'b1;
            @(negedge clk);
            shift_en = 1'b0;
        end
        @(posedge clk);
        #1;

        if (shifted_data !== {6'd35, 6'd27, 6'd20, 6'd16})
            $fatal(1, "serial mismatch got=%h expected=%h", shifted_data,
                   {6'd35, 6'd27, 6'd20, 6'd16});
        if (data_ready)
            $fatal(1, "data_ready did not clear after 24 shifts");

        $display("PASS: sample-to-serial digital flow codes=16,20,27,35");
        $finish;
    end

    initial begin
        #30000;
        $fatal(1, "digital top timeout");
    end
endmodule

`default_nettype wire
