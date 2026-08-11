`timescale 1ns/1ps
`default_nettype none

module serial_readout #(
    parameter WIDTH = 24
) (
    input  wire             clk,
    input  wire             rst_n,
    input  wire             load,
    input  wire             shift_en,
    input  wire [WIDTH-1:0] parallel_data,
    output wire             serial_data,
    output reg              data_ready
);
    reg [WIDTH-1:0] shift_register;
    reg [$clog2(WIDTH+1)-1:0] bits_remaining;

    assign serial_data = shift_register[0];

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            shift_register <= {WIDTH{1'b0}};
            bits_remaining <= 0;
            data_ready <= 1'b0;
        end else if (load) begin
            shift_register <= parallel_data;
            bits_remaining <= WIDTH;
            data_ready <= 1'b1;
        end else if (shift_en && data_ready) begin
            shift_register <= {1'b0, shift_register[WIDTH-1:1]};
            if (bits_remaining == 1) begin
                bits_remaining <= 0;
                data_ready <= 1'b0;
            end else begin
                bits_remaining <= bits_remaining - 1'b1;
            end
        end
    end
endmodule

`default_nettype wire
