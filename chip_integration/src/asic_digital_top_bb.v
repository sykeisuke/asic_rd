// Black box of the hardened digital top for chip synthesis. The macro is
// used as is from digital/asic_digital_top/physical/final_views
// (gds, lef, nl); the ports are those of digital/asic_digital_top/
// asic_digital_top.v, with the VDD/VSS straps of its LEF as power pins.
(* blackbox *)
module asic_digital_top (
`ifdef USE_POWER_PINS
    inout  wire       VDD,
    inout  wire       VSS,
`endif
    input  wire       clk,
    input  wire       rst_n,
    input  wire       start,
    input  wire [3:0] compare_high,
    input  wire       shift_en,
    output wire       acquire,
    output wire       ramp_connect,
    output wire       ramp_reset,
    output wire       serial_data,
    output wire       data_ready,
    output wire       conversion_busy,
    output wire       conversion_done,
    output wire [3:0] conversion_timeout
);
endmodule
