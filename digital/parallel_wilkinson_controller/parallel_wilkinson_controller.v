`timescale 1ns/1ps
`default_nettype none

// Parallel Wilkinson controller for the Analog_top macro (mixed_signal/
// Analog_top, PIN_LIST.md / tb_params.inc), synchronous capture (ADR 0010).
//
// Interface to the analog macro (all switches HIGH = closed):
//   s2[i]  bottom plate to vref. Its FALLING edge is cell i's sampling
//          instant TS_i. Cells are sampled one clock apart (TSPACE = TCOUNT).
//   s0[i]  input gate; opens TNOV after s2 (delay line, 5 ns nominal).
//   s1[i]  ramp gate; closes 2 TNOV after s2 (delay line, 10 ns nominal)
//          and stays closed through the conversion.
//   ramp_rst  HIGH = ramp held at VR_LO. Falls at TR = TS3 + TR_CYCLES clocks
//          (300 ns = 6 clocks), on a rising clock edge; the count starts there.
//   q[i]   the cell's latch (negative-edge flop on cnt_clk): HIGH before the
//          crossing, falls once at the first FALLING clock edge after the
//          comparator decides. code_i = floor((t_qfall_i - TR) / TCOUNT),
//          which is the counter value at the rising edge that first sees
//          q[i] low (CAPTURE_LATENCY = 0).
//
// Sequence from `start` (one clock per step):
//   IDLE     s2=s0=1, s1=0, ramp_rst=1            tracking
//   SAMPLE   s2[k] <= 0 at cycle k (k = 0..3); s0/s1 follow by delay line
//   WAIT     TR_CYCLES clocks after the last sample (S1 charge drains, R6)
//   CONVERT  ramp_rst <= 0, counter 0,1,2,...; q flags sampled every edge
//   DRAIN    counter at full scale: one more cycle for a q from the last count
//   RETRACK  ramp_rst <= 1 and s1 off (s1_en <= 0); next cycle s2=s0=1, done
module parallel_wilkinson_controller #(
    parameter WIDTH = 8,
    parameter CELLS = 4,
    parameter TR_CYCLES = 6,
    parameter S0_STAGES = 12,
    parameter S1_STAGES = 25,
    // 1: q is HIGH before the crossing and falls after it (Analog_top v5,
    // comparator inn = bottom plate). 0: the opposite polarity, should the
    // comparator inputs be swapped.
    parameter Q_FALLS_AT_CROSSING = 1
) (
    input  wire                   clk,
    input  wire                   rst_n,
    input  wire                   start,
    input  wire [CELLS-1:0]       q,
    output reg  [CELLS-1:0]       s2,
    output wire [CELLS-1:0]       s0,
    output wire [CELLS-1:0]       s1,
    output reg                    ramp_rst,
    output wire [CELLS*WIDTH-1:0] codes,
    output reg  [CELLS-1:0]       timeout,
    output reg                    busy,
    output reg                    done
);
    localparam IDLE    = 3'd0;
    localparam SAMPLE  = 3'd1;
    localparam WAIT    = 3'd2;
    localparam CONVERT = 3'd3;
    localparam DRAIN   = 3'd4;
    localparam RETRACK = 3'd5;

    reg [2:0]       state;
    reg [7:0]       wait_count;
    reg [$clog2(CELLS+1)-1:0] cell_idx;
    reg             s1_en;
    reg [WIDTH-1:0] binary_count;
    reg [CELLS*WIDTH-1:0] code_r;
    reg [CELLS-1:0]       captured;
    assign codes = code_r;

    // Switch order inside a cell, from s2 through fixed delay lines.
    wire [CELLS-1:0] s2_d1;
    wire [CELLS-1:0] s2_d2;
    genvar g;
    generate
        for (g = 0; g < CELLS; g = g + 1) begin : sw
            delay_line #(.STAGES(S0_STAGES)) u_d0 (.a(s2[g]), .y(s2_d1[g]));
            delay_line #(.STAGES(S1_STAGES)) u_d1 (.a(s2[g]), .y(s2_d2[g]));
        end
    endgenerate
    assign s0 = s2_d1;                          // opens TNOV after s2
    assign s1 = {CELLS{s1_en}} & ~s2_d2;        // closes 2 TNOV after s2, off at retrack

    wire [CELLS-1:0] crossed = (Q_FALLS_AT_CROSSING != 0) ? ~q : q;
    wire all_captured = &captured;
    integer i;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state        <= IDLE;
            wait_count   <= 8'd0;
            cell_idx     <= 0;
            s2           <= {CELLS{1'b1}};
            s1_en        <= 1'b0;
            ramp_rst     <= 1'b1;
            binary_count <= {WIDTH{1'b0}};
            code_r       <= {(CELLS*WIDTH){1'b0}};
            captured     <= {CELLS{1'b0}};
            timeout      <= {CELLS{1'b0}};
            busy         <= 1'b0;
            done         <= 1'b0;
        end else begin
            done <= 1'b0;

            case (state)
                IDLE: begin
                    s2       <= {CELLS{1'b1}};
                    s1_en    <= 1'b0;
                    ramp_rst <= 1'b1;
                    busy     <= 1'b0;
                    if (start) begin
                        code_r   <= {(CELLS*WIDTH){1'b0}};
                        captured <= {CELLS{1'b0}};
                        timeout  <= {CELLS{1'b0}};
                        cell_idx <= 0;
                        s1_en    <= 1'b1;        // s1 may close once s2 has fallen
                        busy     <= 1'b1;
                        state    <= SAMPLE;
                    end
                end

                SAMPLE: begin
                    // TS_k: this rising edge opens S2 of cell k.
                    s2[cell_idx] <= 1'b0;
                    if (cell_idx == CELLS - 1) begin
                        wait_count <= TR_CYCLES - 1;
                        state      <= WAIT;
                    end else begin
                        cell_idx <= cell_idx + 1'b1;
                    end
                end

                WAIT: begin
                    if (wait_count == 0) begin
                        // TR: ramp released and counter started on this edge.
                        ramp_rst     <= 1'b0;
                        binary_count <= {WIDTH{1'b0}};
                        state        <= CONVERT;
                    end else begin
                        wait_count <= wait_count - 1'b1;
                    end
                end

                CONVERT: begin
                    for (i = 0; i < CELLS; i = i + 1) begin
                        if (crossed[i] && !captured[i]) begin
                            code_r[i*WIDTH +: WIDTH] <= binary_count;
                            captured[i] <= 1'b1;
                        end
                    end
                    if (all_captured) begin
                        ramp_rst <= 1'b1;
                        s1_en    <= 1'b0;
                        state    <= RETRACK;
                    end else if (&binary_count) begin
                        ramp_rst <= 1'b1;
                        state    <= DRAIN;
                    end else begin
                        binary_count <= binary_count + {{(WIDTH-1){1'b0}}, 1'b1};
                    end
                end

                DRAIN: begin
                    // A crossing in the last count shows up one edge later.
                    for (i = 0; i < CELLS; i = i + 1) begin
                        if (crossed[i] && !captured[i]) begin
                            code_r[i*WIDTH +: WIDTH] <= {WIDTH{1'b1}};
                            captured[i] <= 1'b1;
                        end else if (!captured[i]) begin
                            code_r[i*WIDTH +: WIDTH] <= {WIDTH{1'b1}};
                            timeout[i] <= 1'b1;
                        end
                    end
                    s1_en <= 1'b0;
                    state <= RETRACK;
                end

                RETRACK: begin
                    // s1 opened on the previous edge; now close s2 (s0 follows).
                    s2    <= {CELLS{1'b1}};
                    busy  <= 1'b0;
                    done  <= 1'b1;
                    state <= IDLE;
                end

                default: state <= IDLE;
            endcase
        end
    end
endmodule

`default_nettype wire
