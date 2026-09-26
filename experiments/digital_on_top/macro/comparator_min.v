(* blackbox *)
module comparator_min (
`ifdef USE_POWER_PINS
    inout wire vdd,
    inout wire vss,
`endif
    input  wire sample,
    input  wire ramp,
    input  wire bias,
    output wire dout
);
endmodule
