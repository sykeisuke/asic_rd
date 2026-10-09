`timescale 1ns/1ps
`default_nettype none

// Parallel Wilkinson controller, synchronous capture (decided 2026-10-09 on
// the design review's recommendation): every analog cell latches its
// comparator output with the conversion clock and presents a synchronous
// flag `crossed[i]` (1 once the ramp has passed the stored sample). The
// digital block samples the four flags every clock and records, per cell,
// the counter value of the cycle in which the crossing happened. No
// asynchronous capture, no Gray coding, no clock-domain crossing.
//
// Timing convention (CAPTURE_LATENCY = number of clock edges between the
// comparator crossing and the flag becoming visible; 1 for a single
// flip-flop in the cell, 2 for a two-stage synchronizer):
//   cycle k   : binary_count == k (k = 0 is the first cycle after ramp release)
//   crossing in cycle N -> cell flop samples at the edge ending cycle N
//                       -> flag visible in cycle N+1 (latency 1)
//                       -> sampled here at the edge ending cycle N+1, where
//                          binary_count == N+1, so code = N+1 - 1 = N.
//
// Sequence
//   IDLE    acquire=1  ramp_connect=0  ramp_reset=1   cells may track/hold
//   CONNECT acquire=0  ramp_connect=1  ramp_reset=1   cell nodes settle on the
//                                                     (reset) ramp output
//   CONVERT acquire=0  ramp_connect=1  ramp_reset=0   ramp runs, counter counts,
//                                                     flags are sampled
//   DRAIN   counter reached full scale; CAPTURE_LATENCY more cycles so a
//           crossing in the last count can still arrive
//   -> done pulse, back to IDLE. A cell whose flag never rises reads 255 and
//      sets timeout[i].
module parallel_wilkinson_controller #(
    parameter WIDTH = 8,
    parameter CELLS = 4,
    parameter CONNECT_CYCLES = 2,
    parameter CAPTURE_LATENCY = 1
) (
    input  wire                   clk,
    input  wire                   rst_n,
    input  wire                   start,
    input  wire [CELLS-1:0]       crossed,
    output reg                    acquire,
    output reg                    ramp_connect,
    output reg                    ramp_reset,
    output wire [CELLS*WIDTH-1:0] codes,
    output reg  [CELLS-1:0]       timeout,
    output reg                    busy,
    output reg                    done
);
    localparam IDLE    = 2'd0;
    localparam CONNECT = 2'd1;
    localparam CONVERT = 2'd2;
    localparam DRAIN   = 2'd3;

    reg [1:0]       state;
    reg [7:0]       wait_count;
    reg [WIDTH-1:0] binary_count;
    reg [CELLS*WIDTH-1:0] code_r;
    reg [CELLS-1:0]       captured;
    assign codes = code_r;

    // Count of the cycle in which a flag seen now was produced.
    wire [WIDTH-1:0] crossing_count = binary_count - CAPTURE_LATENCY[WIDTH-1:0];

    integer i;
    wire all_captured = &captured;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state        <= IDLE;
            wait_count   <= 8'd0;
            binary_count <= {WIDTH{1'b0}};
            code_r       <= {(CELLS*WIDTH){1'b0}};
            captured     <= {CELLS{1'b0}};
            timeout      <= {CELLS{1'b0}};
            acquire      <= 1'b1;
            ramp_connect <= 1'b0;
            ramp_reset   <= 1'b1;
            busy         <= 1'b0;
            done         <= 1'b0;
        end else begin
            done <= 1'b0;

            case (state)
                IDLE: begin
                    acquire      <= 1'b1;
                    ramp_connect <= 1'b0;
                    ramp_reset   <= 1'b1;
                    busy         <= 1'b0;
                    if (start) begin
                        acquire      <= 1'b0;
                        ramp_connect <= 1'b1;
                        code_r       <= {(CELLS*WIDTH){1'b0}};
                        captured     <= {CELLS{1'b0}};
                        timeout      <= {CELLS{1'b0}};
                        wait_count   <= CONNECT_CYCLES - 1;
                        busy         <= 1'b1;
                        state        <= CONNECT;
                    end
                end

                CONNECT: begin
                    if (wait_count == 0) begin
                        // Ramp released and counter started on the same edge.
                        ramp_reset   <= 1'b0;
                        binary_count <= {WIDTH{1'b0}};
                        state        <= CONVERT;
                    end else begin
                        wait_count <= wait_count - 1'b1;
                    end
                end

                CONVERT: begin
                    // Sample the flags: a cell is captured on the first cycle
                    // its flag is seen; the code is the count of the cycle in
                    // which the comparator actually crossed.
                    for (i = 0; i < CELLS; i = i + 1) begin
                        if (crossed[i] && !captured[i]
                            && binary_count >= CAPTURE_LATENCY[WIDTH-1:0]) begin
                            code_r[i*WIDTH +: WIDTH] <= crossing_count;
                            captured[i] <= 1'b1;
                        end
                    end
                    if (all_captured) begin
                        ramp_reset   <= 1'b1;
                        ramp_connect <= 1'b0;
                        acquire      <= 1'b1;
                        busy         <= 1'b0;
                        done         <= 1'b1;
                        state        <= IDLE;
                    end else if (&binary_count) begin
                        // Full scale reached: stop the ramp, keep sampling for
                        // the flags still in flight.
                        ramp_reset <= 1'b1;
                        wait_count <= CAPTURE_LATENCY;
                        state      <= DRAIN;
                    end else begin
                        binary_count <= binary_count + {{(WIDTH-1){1'b0}}, 1'b1};
                    end
                end

                DRAIN: begin
                    for (i = 0; i < CELLS; i = i + 1) begin
                        if (crossed[i] && !captured[i]) begin
                            code_r[i*WIDTH +: WIDTH] <= {WIDTH{1'b1}};
                            captured[i] <= 1'b1;
                        end
                    end
                    if (wait_count == 0 || all_captured) begin
                        for (i = 0; i < CELLS; i = i + 1) begin
                            if (!captured[i] && !crossed[i]) begin
                                code_r[i*WIDTH +: WIDTH] <= {WIDTH{1'b1}};
                                timeout[i] <= 1'b1;
                            end
                        end
                        ramp_connect <= 1'b0;
                        acquire      <= 1'b1;
                        busy         <= 1'b0;
                        done         <= 1'b1;
                        state        <= IDLE;
                    end else begin
                        wait_count <= wait_count - 1'b1;
                    end
                end

                default: state <= IDLE;
            endcase
        end
    end
endmodule

`default_nettype wire
