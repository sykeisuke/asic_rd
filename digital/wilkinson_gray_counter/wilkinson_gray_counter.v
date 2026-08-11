`timescale 1ns/1ps
`default_nettype none

module wilkinson_gray_counter #(
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
    reg [WIDTH-1:0] binary_count;
    wire [WIDTH-1:0] gray_count;
    reg [WIDTH-1:0] captured_gray;
    reg capture_toggle;
    reg capture_sync1;
    reg capture_sync2;
    reg capture_seen;
    integer i;

    function [WIDTH-1:0] gray_to_binary;
        input [WIDTH-1:0] gray;
        begin
            gray_to_binary[WIDTH-1] = gray[WIDTH-1];
            for (i = WIDTH-2; i >= 0; i = i - 1)
                gray_to_binary[i] = gray_to_binary[i+1] ^ gray[i];
        end
    endfunction

    assign gray_count = binary_count ^ (binary_count >> 1);

    // The comparator edge acts as a local capture clock. Gray coding ensures
    // that a clock-boundary ambiguity can affect at most one counter bit.
    always @(negedge compare_high or negedge rst_n) begin
        if (!rst_n) begin
            captured_gray <= {WIDTH{1'b0}};
            capture_toggle <= 1'b0;
        end else if (busy) begin
            captured_gray <= gray_count;
            capture_toggle <= ~capture_toggle;
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            binary_count <= {WIDTH{1'b0}};
            code          <= {WIDTH{1'b0}};
            valid         <= 1'b0;
            busy          <= 1'b0;
            overflow      <= 1'b0;
            capture_sync1 <= 1'b0;
            capture_sync2 <= 1'b0;
            capture_seen  <= 1'b0;
        end else begin
            capture_sync1 <= capture_toggle;
            capture_sync2 <= capture_sync1;
            valid <= 1'b0;

            if (start && !busy) begin
                binary_count <= {WIDTH{1'b0}};
                busy          <= 1'b1;
                overflow      <= 1'b0;
                capture_seen  <= capture_sync2;
            end else if (busy && capture_sync2 != capture_seen) begin
                code <= gray_to_binary(captured_gray);
                capture_seen <= capture_sync2;
                valid <= 1'b1;
                busy <= 1'b0;
            end else if (busy) begin
                if (&binary_count) begin
                    code     <= binary_count;
                    valid    <= 1'b1;
                    busy     <= 1'b0;
                    overflow <= 1'b1;
                end else begin
                    binary_count <= binary_count + {{(WIDTH-1){1'b0}}, 1'b1};
                end
            end
        end
    end
endmodule

`default_nettype wire
