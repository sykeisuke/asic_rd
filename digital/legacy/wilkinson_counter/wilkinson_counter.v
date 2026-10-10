`timescale 1ns/1ps
`default_nettype none

module wilkinson_counter #(
    parameter WIDTH = 6
) (
    input  wire             clk,
    input  wire             rst_n,
    input  wire             start,
    input  wire             compare_high,
    output reg  [WIDTH-1:0] code,
    output reg              valid,
    output reg              busy,
    output reg              overflow
);
    reg [WIDTH-1:0] count;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count    <= {WIDTH{1'b0}};
            code     <= {WIDTH{1'b0}};
            valid    <= 1'b0;
            busy     <= 1'b0;
            overflow <= 1'b0;
        end else begin
            valid <= 1'b0;

            if (start && !busy) begin
                count    <= {WIDTH{1'b0}};
                busy     <= 1'b1;
                overflow <= 1'b0;
            end else if (busy) begin
                if (!compare_high) begin
                    code  <= count;
                    valid <= 1'b1;
                    busy  <= 1'b0;
                end else if (&count) begin
                    code     <= count;
                    valid    <= 1'b1;
                    busy     <= 1'b0;
                    overflow <= 1'b1;
                end else begin
                    count <= count + {{(WIDTH-1){1'b0}}, 1'b1};
                end
            end
        end
    end
endmodule

`default_nettype wire
