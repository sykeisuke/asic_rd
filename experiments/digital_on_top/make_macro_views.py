"""Post-process Magic's raw LEF and write the Liberty stub / Verilog blackbox
for the comparator_min hard macro (called by make_macro.sh inside the container)."""
import re

raw = open("macro/comparator_min_raw.lef").read()
dirs = {"sample": "INPUT", "ramp": "INPUT", "bias": "INPUT", "dout": "OUTPUT",
        "vdd": "INOUT", "vss": "INOUT"}
use = {"vdd": "POWER", "vss": "GROUND"}
out = []
for line in raw.splitlines():
    m = re.match(r"\s*PIN (\w+)", line)
    out.append(line)
    if m:
        p = m.group(1)
        out.append(f"    DIRECTION {dirs[p]} ;")
        out.append(f"    USE {use.get(p, 'SIGNAL')} ;")
lef = "\n".join(out) + "\n"
# Well layers are not routing layers; OpenROAD rejects them in OBS.
lef = re.sub(r"      LAYER [NP]well ;\n        RECT [^\n]*\n", "", lef)
open("macro/comparator_min.lef", "w").write(lef)

pins = ["sample", "ramp", "bias", "dout"]
lib = [
    "library (comparator_min) {",
    "  delay_model : table_lookup;",
    '  time_unit : "1ns"; voltage_unit : "1V"; current_unit : "1uA";',
    '  capacitive_load_unit (1,pf); leakage_power_unit : "1nW"; pulling_resistance_unit : "1kohm";',
    "  nom_process : 1.0; nom_temperature : 25.0; nom_voltage : 3.3;",
    "  input_threshold_pct_fall : 50.0; input_threshold_pct_rise : 50.0;",
    "  output_threshold_pct_fall : 50.0; output_threshold_pct_rise : 50.0;",
    "  slew_lower_threshold_pct_fall : 20.0; slew_lower_threshold_pct_rise : 20.0;",
    "  slew_upper_threshold_pct_fall : 80.0; slew_upper_threshold_pct_rise : 80.0;",
    "  cell (comparator_min) {",
    "    area : 588.7;",
    '    pg_pin (vdd) { pg_type : primary_power; voltage_name : "vdd"; }',
    '    pg_pin (vss) { pg_type : primary_ground; voltage_name : "vss"; }',
]
for p in pins:
    d = "output" if p == "dout" else "input"
    lib.append(f"    pin ({p}) {{ direction : {d}; capacitance : 0.005; }}")
lib += ["  }", "}", ""]
open("macro/comparator_min.lib", "w").write("\n".join(lib))

open("macro/comparator_min.v", "w").write("""(* blackbox *)
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
""")
print("wrote macro/comparator_min.{lef,lib,v}")
