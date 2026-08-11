`timescale 1ns/1ps
`default_nettype none

module four_cell_wilkinson_controller #(
    parameter WIDTH = 6,
    parameter RESET_CYCLES = 2,
    parameter SETTLE_CYCLES = 2
) (
    input  wire                 clk,
    input  wire                 rst_n,
    input  wire                 start,
    input  wire                 compare_high,
    output reg  [3:0]           mux_select,
    output reg                  ramp_reset,
    output reg                  bus_reset,
    output wire [4*WIDTH-1:0]   codes,
    output reg                  busy,
    output reg                  done,
    output wire [1:0]           active_cell
);
    localparam IDLE    = 3'd0;
    localparam RESET   = 3'd1;
    localparam SETTLE  = 3'd2;
    localparam START   = 3'd3;
    localparam CONVERT = 3'd4;

    reg [2:0] state;
    reg [1:0] cell_index;
    reg [7:0] wait_count;
    reg counter_start;
    wire [WIDTH-1:0] counter_code;
    wire counter_valid;
    wire counter_busy;
    wire counter_overflow;
    reg [WIDTH-1:0] code0;
    reg [WIDTH-1:0] code1;
    reg [WIDTH-1:0] code2;
    reg [WIDTH-1:0] code3;

    assign codes = {code3, code2, code1, code0};
    assign active_cell = cell_index;

    wilkinson_gray_counter #(.WIDTH(WIDTH)) counter (
        .clk(clk),
        .rst_n(rst_n),
        .start(counter_start),
        .compare_high(compare_high),
        .code(counter_code),
        .valid(counter_valid),
        .busy(counter_busy),
        .overflow(counter_overflow)
    );

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state         <= IDLE;
            cell_index    <= 2'd0;
            wait_count    <= 8'd0;
            counter_start <= 1'b0;
            mux_select    <= 4'b0000;
            ramp_reset    <= 1'b1;
            bus_reset     <= 1'b1;
            code0         <= {WIDTH{1'b0}};
            code1         <= {WIDTH{1'b0}};
            code2         <= {WIDTH{1'b0}};
            code3         <= {WIDTH{1'b0}};
            busy          <= 1'b0;
            done          <= 1'b0;
        end else begin
            counter_start <= 1'b0;
            done <= 1'b0;

            case (state)
                IDLE: begin
                    mux_select <= 4'b0000;
                    ramp_reset <= 1'b1;
                    bus_reset  <= 1'b1;
                    busy       <= 1'b0;
                    if (start) begin
                        cell_index <= 2'd0;
                        code0      <= {WIDTH{1'b0}};
                        code1      <= {WIDTH{1'b0}};
                        code2      <= {WIDTH{1'b0}};
                        code3      <= {WIDTH{1'b0}};
                        wait_count <= RESET_CYCLES - 1;
                        busy       <= 1'b1;
                        state      <= RESET;
                    end
                end

                RESET: begin
                    mux_select <= 4'b0000;
                    ramp_reset <= 1'b1;
                    bus_reset  <= 1'b1;
                    if (wait_count == 0) begin
                        mux_select <= 4'b0001 << cell_index;
                        bus_reset  <= 1'b0;
                        wait_count <= SETTLE_CYCLES - 1;
                        state      <= SETTLE;
                    end else begin
                        wait_count <= wait_count - 1'b1;
                    end
                end

                SETTLE: begin
                    if (wait_count == 0) begin
                        counter_start <= 1'b1;
                        state      <= START;
                    end else begin
                        wait_count <= wait_count - 1'b1;
                    end
                end

                START: begin
                    // The counter consumes the registered start pulse on this
                    // edge, exactly when the analog ramp is released.
                    ramp_reset <= 1'b0;
                    state <= CONVERT;
                end

                CONVERT: begin
                    if (counter_valid) begin
                        case (cell_index)
                            2'd0: code0 <= counter_code;
                            2'd1: code1 <= counter_code;
                            2'd2: code2 <= counter_code;
                            2'd3: code3 <= counter_code;
                        endcase
                        mux_select <= 4'b0000;
                        ramp_reset <= 1'b1;
                        bus_reset  <= 1'b1;
                        if (cell_index == 2'd3) begin
                            busy  <= 1'b0;
                            done  <= 1'b1;
                            state <= IDLE;
                        end else begin
                            cell_index <= cell_index + 1'b1;
                            wait_count <= RESET_CYCLES - 1;
                            state      <= RESET;
                        end
                    end
                end

                default: state <= IDLE;
            endcase
        end
    end
endmodule

`default_nettype wire
