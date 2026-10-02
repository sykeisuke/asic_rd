// Digital-on-top core of the waveform-sampling ASIC.
//
// The digital top (digital/asic_digital_top, unchanged) is soft logic
// that LibreLane synthesises, places and routes with the rest of the
// chip. The analog cells are hard macros (macros.py): wsa_cmp is the
// comparator, wsa_inv the replica inverter (cicpy), wsa_inv_gf the same
// inverter drawn in gdsfactory. Everything between them and the pads is
// wired here. Core nets are routed by LibreLane; the analog pad nets
// are drawn by librelane/analog_routes.tcl.
//
// Pads (0p5x1 slot, template pad positions unchanged):
//
//   input[0]  start          input[2]  test_mode (1: ext_compare drives capture 0)
//   input[1]  shift_en       input[3]  ext_compare (also captures 1..3, which have
//                                      no comparator on this chip)
//
//   bidir[0]  serial_data    bidir[4..7]  conversion_timeout[3..0]
//   bidir[1]  data_ready     bidir[8]     acquire
//   bidir[2]  conversion_busy bidir[9]    ramp_connect
//   bidir[3]  conversion_done bidir[10]   ramp_reset
//                            bidir[11]    comparator output (wsa_cmp.dout)
//                            bidir[12]    compare_high[0], as the capture sees it
//                            bidir[13]    wsa_inv_gf.Y = NOT compare_high[0]
//                            bidir[14..] unused: output and input off, pull-down
//
//   analog[0] wsa_cmp.vin    (held voltage in standalone mode)
//   analog[1] wsa_cmp.vramp  (external ramp)
//   analog[2] wsa_cmp.vbias
//   analog[3] wsa_inv.A      analog[4] wsa_inv.Y      analog[5] spare
//
// Digital top: the 8-bit parallel architecture of spec 0.6 (2026-09-18):
// four capture channels compare_high[3:0], no analog MUX, acquire /
// ramp_connect / ramp_reset mode outputs, 32-bit frame.
//
// Comparator polarity (simulations/gf180_comparator): dout is high while
// vin > vramp and falls at the crossing, which is the edge the capture
// channel latches on. So dout drives compare_high[0] as is.

`default_nettype none

module chip_core #(
    parameter NUM_INPUT_PADS,
    parameter NUM_BIDIR_PADS,
    parameter NUM_ANALOG_PADS
    )(
    `ifdef USE_POWER_PINS
    inout  wire VDD,
    inout  wire VSS,
    `endif

    input  wire clk,       // conversion clock
    input  wire rst_n,     // reset (active low)

    input  wire [NUM_INPUT_PADS-1:0] input_in,   // Input value
    output wire [NUM_INPUT_PADS-1:0] input_pu,   // Pull-up
    output wire [NUM_INPUT_PADS-1:0] input_pd,   // Pull-down

    input  wire [NUM_BIDIR_PADS-1:0] bidir_in,   // Input value
    output wire [NUM_BIDIR_PADS-1:0] bidir_out,  // Output value
    output wire [NUM_BIDIR_PADS-1:0] bidir_oe,   // Output enable
    output wire [NUM_BIDIR_PADS-1:0] bidir_cs,   // Input type (0=CMOS Buffer, 1=Schmitt Trigger)
    output wire [NUM_BIDIR_PADS-1:0] bidir_sl,   // Slew rate (0=fast, 1=slow)
    output wire [NUM_BIDIR_PADS-1:0] bidir_ie,   // Input enable
    output wire [NUM_BIDIR_PADS-1:0] bidir_pu,   // Pull-up
    output wire [NUM_BIDIR_PADS-1:0] bidir_pd,   // Pull-down

    inout  wire [NUM_ANALOG_PADS-1:0] analog  // Analog
);

    localparam NUM_OUT = 14;

    // Pad control. The first NUM_OUT bidirectional pads are outputs; the
    // rest are switched off and pulled down so they do not float.
    localparam [NUM_BIDIR_PADS-1:0] OUT_MASK = {NUM_OUT{1'b1}};

    assign input_pu = '0;
    assign input_pd = '0;

    assign bidir_oe = OUT_MASK;
    assign bidir_cs = '0;
    assign bidir_sl = '0;
    assign bidir_ie = '0;
    assign bidir_pu = '0;
    assign bidir_pd = ~OUT_MASK;

    logic _unused;
    assign _unused = &bidir_in;

    wire start       = input_in[0];
    wire shift_en    = input_in[1];
    wire test_mode   = input_in[2];
    wire ext_compare = input_in[3];

    // Analog hard macros

    wire cmp_dout;

    wsa_cmp u_cmp (
        `ifdef USE_POWER_PINS
        .VDD   (VDD),
        .VSS   (VSS),
        `endif
        .vin   (analog[0]),
        .vramp (analog[1]),
        .vbias (analog[2]),
        .dout  (cmp_dout)
    );

    wsa_inv u_inv (
        `ifdef USE_POWER_PINS
        .VDD   (VDD),
        .VSS   (VSS),
        `endif
        .A     (analog[3]),
        .Y     (analog[4])
    );

    // Digital test mode independent of the analog crossing (spec 7.3):
    // capture 0 comes from a pad instead of the comparator. Captures 1..3
    // have no comparator on this chip and always take the pad.
    wire       compare_high0 = test_mode ? ext_compare : cmp_dout;
    wire [3:0] compare_high  = {ext_compare, ext_compare, ext_compare, compare_high0};

    // A simple analog cell on core nets: the gdsfactory inverter inverts
    // the capture edge and drives a pad. With test_mode=1 and a square
    // wave on ext_compare, bidir[13] shows the inverter working in silicon
    // independent of the comparator. Its pins are ordinary signal nets,
    // routed by LibreLane like the template's SRAM pins.
    wire inv_gf_y;

    wsa_inv_gf u_inv_gf (
        `ifdef USE_POWER_PINS
        .VDD   (VDD),
        .VSS   (VSS),
        `endif
        .A     (compare_high0),
        .Y     (inv_gf_y)
    );

    // Digital top, as is

    wire       acquire;
    wire       ramp_connect;
    wire       ramp_reset;
    wire       serial_data;
    wire       data_ready;
    wire       conversion_busy;
    wire       conversion_done;
    wire [3:0] conversion_timeout;

    asic_digital_top u_digital (
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

    assign bidir_out = {
        {(NUM_BIDIR_PADS-NUM_OUT){1'b0}},
        inv_gf_y,
        compare_high0,
        cmp_dout,
        ramp_reset,
        ramp_connect,
        acquire,
        conversion_timeout,
        conversion_done,
        conversion_busy,
        data_ready,
        serial_data
    };

endmodule

`default_nettype wire
