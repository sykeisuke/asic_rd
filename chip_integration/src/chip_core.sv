// Digital-on-top core of the waveform-sampling chip, 1x0p5 slot.
//
// Two hard macros and the glue between them and the pads:
//
//   u_digital  asic_digital_top, taken as is from its own hardened views
//              (digital/asic_digital_top/physical/final_views): the 8-bit
//              parallel Wilkinson controller + 32-bit serial readout.
//   u_analog   wsa_analog_top, the Analog_top_v5 macro
//              (analog_macro.py; mostly placeholder layout for now).
//
// PROVISIONAL CONNECTION (2026-10-16). The per-cell sampling sequencer
// does not exist in RTL yet, so the sampling controls are board-driven
// (specification s.4, "board-controllable sampling controls"):
//
//   s1_i     = ramp_connect               (all four cells together)
//   ramp_rst = ramp_reset
//   s0_i     = samp_top[i] & acquire      (pads, gated by the controller)
//   s2_i     = samp_bot[i] & acquire
//   cnt_clk  = clk
//   compare_high[i] = test_mode ? ext_compare : q_i
//
// q_i is the latched comparator of cell i (dfxtn_2 on the falling count
// clock); it falls once, at the code, which is the edge the Gray capture
// in the digital top samples on. So q drives compare_high as is.
// test_mode is the specification 7.3 digital test mode: the capture runs
// from the ext_compare pad, independent of the analog crossing.
//
// Pads (template positions; fig11b names in brackets):
//
//   clk [CLK]           -> digital clk, analog cnt_clk
//   rst_n [RST_N]       -> digital rst_n
//   input[0] [IN0]  start          input[2] [IN2]  test_mode
//   input[1] [IN1]  shift_en       input[3] [IN3]  ext_compare
//
//   bidir outputs                  bidir inputs
//   [0]  serial_data               [15..18] samp_top[0..3]
//   [1]  data_ready                [19..22] samp_bot[0..3]
//   [2]  conversion_busy           [23]     ramp_sel
//   [3]  conversion_done           [24..25] amon_sel[0..1]
//   [4..7] conversion_timeout[0..3] [26]    cmp_sa_en
//   [8]  acquire                   [27..43] unused: driver and receiver
//   [9]  ramp_connect                       off, pull-down on
//   [10] ramp_reset
//   [11..14] compare_high[0..3], as the capture sees it
//
//   analog[3] [VIN]       asig_5p0 -> u_analog.vin
//   analog[2] [EXT_RAMP]  bi_a ANA -> u_analog.ext_ramp
//   analog[1] [AMON]      bi_a ANA -> u_analog.amon
//   analog[0] [CMP_OUT]   bi_a ANA -> u_analog.cmp_out
//   avdd_pad / avss_pad [AVDD / AVSS] (template bidir[45] / bidir[44])
//
// The four analog pad nets are drawn by librelane/analog_routes.tcl, not
// routed; AVDD/AVSS and the analog macro's DVDD/DVSS straps by
// librelane/power_routes.tcl.

`default_nettype none

module chip_core #(
    parameter NUM_INPUT_PADS,
    parameter NUM_BIDIR_PADS
    )(
    `ifdef USE_POWER_PINS
    inout  wire VDD,
    inout  wire VSS,
    inout  wire AVDD,
    `endif

    input  wire clk,       // conversion clock, 20 MHz
    input  wire rst_n,     // reset (active low)

    input  wire [NUM_INPUT_PADS-1:0] input_in,
    output wire [NUM_INPUT_PADS-1:0] input_pu,
    output wire [NUM_INPUT_PADS-1:0] input_pd,

    input  wire [NUM_BIDIR_PADS-1:0] bidir_in,
    output wire [NUM_BIDIR_PADS-1:0] bidir_out,
    output wire [NUM_BIDIR_PADS-1:0] bidir_oe,
    output wire [NUM_BIDIR_PADS-1:0] bidir_cs,
    output wire [NUM_BIDIR_PADS-1:0] bidir_sl,
    output wire [NUM_BIDIR_PADS-1:0] bidir_ie,
    output wire [NUM_BIDIR_PADS-1:0] bidir_pu,
    output wire [NUM_BIDIR_PADS-1:0] bidir_pd,

    inout  wire vin,
    inout  wire ext_ramp,
    inout  wire amon,
    inout  wire cmp_out,

    output wire [2:0] ana_a,
    output wire [2:0] ana_oe,
    output wire [2:0] ana_cs,
    output wire [2:0] ana_sl,
    output wire [2:0] ana_ie,
    output wire [2:0] ana_pu,
    output wire [2:0] ana_pd,
    output wire [2:0] ana_pdrv0,
    output wire [2:0] ana_pdrv1
);
    localparam N_OUT = 15;  // bidir[14:0] outputs
    localparam N_IN  = 12;  // bidir[26:15] inputs

    // west inputs
    wire start       = input_in[0];
    wire shift_en    = input_in[1];
    wire test_mode   = input_in[2];
    wire ext_compare = input_in[3];

    assign input_pu = '0;
    assign input_pd = '0;

    // bidir inputs
    wire [3:0] samp_top  = bidir_in[18:15];
    wire [3:0] samp_bot  = bidir_in[22:19];
    wire       ramp_sel  = bidir_in[23];
    wire [1:0] amon_sel  = bidir_in[25:24];
    wire       cmp_sa_en = bidir_in[26];

    // the digital top
    wire       acquire, ramp_connect, ramp_reset;
    wire       serial_data, data_ready, conversion_busy, conversion_done;
    wire [3:0] conversion_timeout;
    wire [3:0] compare_high;
    wire [3:0] q;

    assign compare_high = test_mode ? {4{ext_compare}} : q;

    asic_digital_top u_digital (
        `ifdef USE_POWER_PINS
        .VDD                (VDD),
        .VSS                (VSS),
        `endif
        .clk                (clk),
        .rst_n              (rst_n),
        .start              (start),
        .compare_high       (compare_high),
        .shift_en           (shift_en),
        .acquire            (acquire),
        .ramp_connect       (ramp_connect),
        .ramp_reset         (ramp_reset),
        .serial_data        (serial_data),
        .data_ready         (data_ready),
        .conversion_busy    (conversion_busy),
        .conversion_done    (conversion_done),
        .conversion_timeout (conversion_timeout)
    );

    // the analog top
    wire [3:0] s0 = samp_top & {4{acquire}};
    wire [3:0] s2 = samp_bot & {4{acquire}};

    wsa_analog_top u_analog (
        `ifdef USE_POWER_PINS
        .dvdd      (VDD),
        .dvss      (VSS),
        .avdd      (AVDD),
        .avss      (VSS),
        `endif
        .vin       (vin),
        .ext_ramp  (ext_ramp),
        .amon      (amon),
        .cmp_out   (cmp_out),
        .s0_0      (s0[0]),
        .s0_1      (s0[1]),
        .s0_2      (s0[2]),
        .s0_3      (s0[3]),
        .s1_0      (ramp_connect),
        .s1_1      (ramp_connect),
        .s1_2      (ramp_connect),
        .s1_3      (ramp_connect),
        .s2_0      (s2[0]),
        .s2_1      (s2[1]),
        .s2_2      (s2[2]),
        .s2_3      (s2[3]),
        .ramp_rst  (ramp_reset),
        .cnt_clk   (clk),
        .q0        (q[0]),
        .q1        (q[1]),
        .q2        (q[2]),
        .q3        (q[3]),
        .ramp_sel  (ramp_sel),
        .amon_sel0 (amon_sel[0]),
        .amon_sel1 (amon_sel[1]),
        .cmp_sa_en (cmp_sa_en)
    );

    // bidir outputs
    wire [N_OUT-1:0] outs = {compare_high, ramp_reset, ramp_connect, acquire,
                             conversion_timeout, conversion_done,
                             conversion_busy, data_ready, serial_data};
    localparam N_USED = N_OUT + N_IN;

    assign bidir_out = {{(NUM_BIDIR_PADS-N_OUT){1'b0}}, outs};
    assign bidir_oe  = {{(NUM_BIDIR_PADS-N_OUT){1'b0}}, {N_OUT{1'b1}}};
    assign bidir_ie  = {{(NUM_BIDIR_PADS-N_USED){1'b0}}, {N_IN{1'b1}}, {N_OUT{1'b0}}};
    assign bidir_pd  = {{(NUM_BIDIR_PADS-N_USED){1'b1}}, {N_USED{1'b0}}};
    assign bidir_pu  = '0;
    assign bidir_cs  = '0;
    assign bidir_sl  = '0;

    // bi_a analog pads: digital driver off, receiver off, no pulls
    assign ana_a     = '0;
    assign ana_oe    = '0;
    assign ana_cs    = '0;
    assign ana_sl    = '0;
    assign ana_ie    = '0;
    assign ana_pu    = '0;
    assign ana_pd    = '0;
    assign ana_pdrv0 = '0;
    assign ana_pdrv1 = '0;

    logic _unused;
    assign _unused = &{bidir_in[NUM_BIDIR_PADS-1:N_USED], bidir_in[N_OUT-1:0]};

endmodule

`default_nettype wire
