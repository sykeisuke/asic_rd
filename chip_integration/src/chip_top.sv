// SPDX-FileCopyrightText: © 2025 Project Template Contributors
// SPDX-License-Identifier: Apache-2.0
//
// Pad ring of the waveform-sampling chip on the wafer.space 1x0p5 slot.
// Derived from wafer-space/gf180mcu-project-template, commit
// 0de7e394337a1f7f5303ac7a3681bf2481b58176 (src/chip_top.sv), with the
// frozen pad library gf180mcu_ocd_io only (no fd_io branch) and these
// changes, all at the template's pad positions (slot_1x0p5.yaml order):
//
// - bidir[45] and bidir[44] are re-typed to a second core supply pair:
//   avdd_pad (gf180mcu_ocd_io__vdd) whose VDD pin is the analog supply
//   AVDD, and avss_pad (gf180mcu_ocd_io__vss). The 1x0p5 counterpart of
//   the frozen 0p5x1 ring's bidir[43:42] (PDK_PAD_SUPPLY_FREEZE.md WS-06).
//   The bidir bus is therefore bidir[43:0] (IO0..IO43 of fig11b).
//   AVSS is VSS: the ocd_io ring's VSS rail runs through every cell,
//   break cells included, and all grounds are common on the COB.
// - analog[2:0] are gf180mcu_ocd_io__bi_a (pad -> 4 x ppolyf series R ->
//   ANA with secondary diodes; its digital driver and receiver are held
//   off), analog[3] (VIN) is gf180mcu_ocd_io__asig_5p0, as in the chip
//   floorplan record (mixed_signal/chip_floorplan_v2).
// - no SRAM. The design lives in chip_core.sv.

`default_nettype none

`include "slot_defines.svh"

module chip_top #(
    parameter NUM_DVDD_PADS = `NUM_DVDD_PADS,
    parameter NUM_DVSS_PADS = `NUM_DVSS_PADS,
    parameter NUM_VDD_PADS = `NUM_VDD_PADS,
    parameter NUM_VSS_PADS = `NUM_VSS_PADS,
    parameter NUM_INPUT_PADS = `NUM_INPUT_PADS,
    // two of the slot's bidir positions are the AVDD pair
    parameter NUM_BIDIR_PADS = `NUM_BIDIR_PADS - 2,
    parameter NUM_ANALOG_PADS = `NUM_ANALOG_PADS
    )(
    `ifdef USE_POWER_PINS
    inout  wire VDD,
    inout  wire VSS,
    inout  wire DVDD,
    inout  wire DVSS,
    inout  wire AVDD,
    `endif

    inout  wire clk_PAD,
    inout  wire rst_n_PAD,

    inout  wire [NUM_INPUT_PADS-1:0] input_PAD,
    inout  wire [NUM_BIDIR_PADS-1:0] bidir_PAD,

    inout  wire [NUM_ANALOG_PADS-1:0] analog_PAD
);

    wire clk_PAD2CORE;
    wire rst_n_PAD2CORE;

    wire [NUM_INPUT_PADS-1:0] input_PAD2CORE;
    wire [NUM_INPUT_PADS-1:0] input_CORE2PAD_PU;
    wire [NUM_INPUT_PADS-1:0] input_CORE2PAD_PD;

    wire [NUM_BIDIR_PADS-1:0] bidir_PAD2CORE;
    wire [NUM_BIDIR_PADS-1:0] bidir_CORE2PAD;
    wire [NUM_BIDIR_PADS-1:0] bidir_CORE2PAD_OE;
    wire [NUM_BIDIR_PADS-1:0] bidir_CORE2PAD_CS;
    wire [NUM_BIDIR_PADS-1:0] bidir_CORE2PAD_SL;
    wire [NUM_BIDIR_PADS-1:0] bidir_CORE2PAD_IE;
    wire [NUM_BIDIR_PADS-1:0] bidir_CORE2PAD_PU;
    wire [NUM_BIDIR_PADS-1:0] bidir_CORE2PAD_PD;

    // analog[2:0]: core side of the bi_a pads and their (held-off)
    // digital controls
    wire [2:0] ana_CORE;
    wire [2:0] ana_A, ana_OE, ana_CS, ana_SL, ana_IE, ana_PU, ana_PD;
    wire [2:0] ana_PDRV0, ana_PDRV1;

    // Power/ground pad instances
    generate
    for (genvar i=0; i<NUM_DVDD_PADS; i++) begin : dvdd_pads
        (* keep *)
        gf180mcu_ocd_io__dvdd pad (
            `ifdef USE_POWER_PINS
            .DVDD   (DVDD),
            .DVSS   (DVSS),
            .VDD    (VDD),
            .VSS    (VSS)
            `endif
        );
    end
    for (genvar i=0; i<NUM_DVSS_PADS; i++) begin : dvss_pads
        (* keep *)
        gf180mcu_ocd_io__dvss pad (
            `ifdef USE_POWER_PINS
            .DVDD   (DVDD),
            .DVSS   (DVSS),
            .VDD    (VDD),
            .VSS    (VSS)
            `endif
        );
    end
    for (genvar i=0; i<NUM_VDD_PADS; i++) begin : vdd_pads
        (* keep *)
        gf180mcu_ocd_io__vdd pad (
            `ifdef USE_POWER_PINS
            .DVDD   (DVDD),
            .DVSS   (DVSS),
            .VDD    (VDD),
            .VSS    (VSS)
            `endif
        );
    end
    for (genvar i=0; i<NUM_VSS_PADS; i++) begin : vss_pads
        (* keep *)
        gf180mcu_ocd_io__vss pad (
            `ifdef USE_POWER_PINS
            .DVDD   (DVDD),
            .DVSS   (DVSS),
            .VDD    (VDD),
            .VSS    (VSS)
            `endif
        );
    end
    endgenerate

    // The AVDD pair (template bidir[45], bidir[44])
    (* keep *)
    gf180mcu_ocd_io__vdd avdd_pad (
        `ifdef USE_POWER_PINS
        .DVDD   (DVDD),
        .DVSS   (DVSS),
        .VDD    (AVDD),
        .VSS    (VSS)
        `endif
    );
    (* keep *)
    gf180mcu_ocd_io__vss avss_pad (
        `ifdef USE_POWER_PINS
        .DVDD   (DVDD),
        .DVSS   (DVSS),
        .VDD    (VDD),
        .VSS    (VSS)
        `endif
    );

    // Signal IO pad instances

    // Schmitt trigger
    gf180mcu_ocd_io__in_s clk_pad (
        `ifdef USE_POWER_PINS
        .DVDD   (DVDD),
        .DVSS   (DVSS),
        .VDD    (VDD),
        .VSS    (VSS),
        `endif
        .Y      (clk_PAD2CORE),
        .PAD    (clk_PAD),
        .PU     (1'b0),
        .PD     (1'b0)
    );

    // Normal input
    gf180mcu_ocd_io__in_c rst_n_pad (
        `ifdef USE_POWER_PINS
        .DVDD   (DVDD),
        .DVSS   (DVSS),
        .VDD    (VDD),
        .VSS    (VSS),
        `endif
        .Y      (rst_n_PAD2CORE),
        .PAD    (rst_n_PAD),
        .PU     (1'b0),
        .PD     (1'b0)
    );

    generate
    for (genvar i=0; i<NUM_INPUT_PADS; i++) begin : inputs
        (* keep *)
        gf180mcu_ocd_io__in_c pad (
            `ifdef USE_POWER_PINS
            .DVDD   (DVDD),
            .DVSS   (DVSS),
            .VDD    (VDD),
            .VSS    (VSS),
            `endif
            .Y      (input_PAD2CORE[i]),
            .PAD    (input_PAD[i]),
            .PU     (input_CORE2PAD_PU[i]),
            .PD     (input_CORE2PAD_PD[i])
        );
    end
    endgenerate

    generate
    for (genvar i=0; i<NUM_BIDIR_PADS; i++) begin : bidir
        (* keep *)
        gf180mcu_ocd_io__bi_24t pad (
            `ifdef USE_POWER_PINS
            .DVDD   (DVDD),
            .DVSS   (DVSS),
            .VDD    (VDD),
            .VSS    (VSS),
            `endif
            .A      (bidir_CORE2PAD[i]),
            .OE     (bidir_CORE2PAD_OE[i]),
            .Y      (bidir_PAD2CORE[i]),
            .PAD    (bidir_PAD[i]),
            .CS     (bidir_CORE2PAD_CS[i]),
            .SL     (bidir_CORE2PAD_SL[i]),
            .IE     (bidir_CORE2PAD_IE[i]),
            .PU     (bidir_CORE2PAD_PU[i]),
            .PD     (bidir_CORE2PAD_PD[i])
        );
    end
    endgenerate

    // analog[2:0]: EXT_RAMP, AMON, CMP_OUT through bi_a (ANA side to the
    // analog macro; the driver and receiver are held off by chip_core)
    generate
    for (genvar i=0; i<3; i++) begin : analog
        (* keep *)
        gf180mcu_ocd_io__bi_a pad (
            `ifdef USE_POWER_PINS
            .DVDD   (DVDD),
            .DVSS   (DVSS),
            .VDD    (VDD),
            .VSS    (VSS),
            `endif
            .A      (ana_A[i]),
            .OE     (ana_OE[i]),
            .Y      (),
            .PAD    (analog_PAD[i]),
            // Synthesis black-boxes the pads from their liberty, which
            // has no ANA pin (untimed analog side), so ANA exists only
            // where the Verilog models are read (lint, JSON header);
            // librelane/analog_routes.tcl makes the same connection in
            // the database, ANA -> the analog macro pin's net
            `ifdef USE_POWER_PINS
            .ANA    (ana_CORE[i]),
            `endif
            .CS     (ana_CS[i]),
            .SL     (ana_SL[i]),
            .IE     (ana_IE[i]),
            .PU     (ana_PU[i]),
            .PD     (ana_PD[i]),
            .PDRV0  (ana_PDRV0[i]),
            .PDRV1  (ana_PDRV1[i])
        );
    end
    endgenerate

    // analog[3]: VIN through asig_5p0 (the bond pad net is the core net)
    (* keep *)
    gf180mcu_ocd_io__asig_5p0 analog3_pad (
        `ifdef USE_POWER_PINS
        .DVDD   (DVDD),
        .DVSS   (DVSS),
        .VDD    (VDD),
        .VSS    (VSS),
        `endif
        .ASIG5V (analog_PAD[3])
    );

    // Core design

    chip_core #(
        .NUM_INPUT_PADS  (NUM_INPUT_PADS),
        .NUM_BIDIR_PADS  (NUM_BIDIR_PADS)
    ) i_chip_core (
        `ifdef USE_POWER_PINS
        .VDD        (VDD),
        .VSS        (VSS),
        .AVDD       (AVDD),
        `endif

        .clk        (clk_PAD2CORE),
        .rst_n      (rst_n_PAD2CORE),

        .input_in   (input_PAD2CORE),
        .input_pu   (input_CORE2PAD_PU),
        .input_pd   (input_CORE2PAD_PD),

        .bidir_in   (bidir_PAD2CORE),
        .bidir_out  (bidir_CORE2PAD),
        .bidir_oe   (bidir_CORE2PAD_OE),
        .bidir_cs   (bidir_CORE2PAD_CS),
        .bidir_sl   (bidir_CORE2PAD_SL),
        .bidir_ie   (bidir_CORE2PAD_IE),
        .bidir_pu   (bidir_CORE2PAD_PU),
        .bidir_pd   (bidir_CORE2PAD_PD),

        .vin        (analog_PAD[3]),
        .ext_ramp   (ana_CORE[2]),
        .amon       (ana_CORE[1]),
        .cmp_out    (ana_CORE[0]),

        .ana_a      (ana_A),
        .ana_oe     (ana_OE),
        .ana_cs     (ana_CS),
        .ana_sl     (ana_SL),
        .ana_ie     (ana_IE),
        .ana_pu     (ana_PU),
        .ana_pd     (ana_PD),
        .ana_pdrv0  (ana_PDRV0),
        .ana_pdrv1  (ana_PDRV1)
    );

    // Do not remove, necessary for tapeout
    (* keep *) gf180mcu_ws_ip__qrcode_id qrcode_id ();
    (* keep *) gf180mcu_ws_ip__shuttle_id shuttle_id ();
    (* keep *) gf180mcu_ws_ip__project_id project_id ();
    (* keep *) gf180mcu_ws_ip__marker marker ();

    // wafer.space logo - can be removed if desired
    (* keep *) gf180mcu_ws_ip__logo wafer_space_logo ();

endmodule

`default_nettype wire
