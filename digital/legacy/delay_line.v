`timescale 1ns/1ps
`default_nettype none

// Fixed delay line for the switch-order edges inside the sampling sequence
// (S0 opens TNOV after S2, S1 closes 2 TNOV after S2; TNOV = 5 ns nominal).
// Synthesis instantiates STAGES delay buffers of the frozen 3.3 V library
// (gf180mcu_as_sc_mcu7t3v3__dlybuff_2, about 0.40 ns each at typical; the
// chain is kept so no tool removes it). With SCL_FD_SC_MCU7T5V0 defined
// (the 5 V flow rehearsals such as mixed_signal/top_placement) it uses the
// 5 V library's dlya_1 instead (about 0.37 ns). Simulation uses a behavioral delay
// of the same nominal value. PVT spread of the standard-cell delay is about
// +-40 %, which moves TNOV and with it a per-cell offset of about 1 LSB that
// the pedestal calibration removes (spec 5.5).
module delay_line #(
    parameter STAGES = 12,
    parameter real STAGE_NS = 0.40
) (
    input  wire a,
    output wire y
);
`ifdef SYNTHESIS
    wire [STAGES:0] chain;
    assign chain[0] = a;
    genvar g;
    generate
        for (g = 0; g < STAGES; g = g + 1) begin : stage
`ifdef SCL_FD_SC_MCU7T5V0
            // 5 V library (flow rehearsals only): dlya_1, about 0.37 ns typical
            (* keep *) gf180mcu_fd_sc_mcu7t5v0__dlya_1 u_dly (.I(chain[g]), .Z(chain[g+1]));
`else
            (* keep *) gf180mcu_as_sc_mcu7t3v3__dlybuff_2 u_dly (.A(chain[g]), .Y(chain[g+1]));
`endif
        end
    endgenerate
    assign y = chain[STAGES];
`else
    /* verilator lint_off STMTDLY */
    reg y_r = 1'b0;
    always @(a) y_r <= #(STAGES * STAGE_NS) a;
    assign y = y_r;
    /* verilator lint_on STMTDLY */
`endif
endmodule

`default_nettype wire
