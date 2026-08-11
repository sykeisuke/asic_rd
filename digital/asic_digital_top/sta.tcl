set liberty /foss/pdks/gf180mcuD/libs.ref/gf180mcu_fd_sc_mcu7t5v0/lib/gf180mcu_fd_sc_mcu7t5v0__tt_025C_3v30.lib
read_liberty $liberty
read_verilog work/asic_digital_top_mapped.v
link_design asic_digital_top
read_sdc asic_digital_top.sdc
report_checks -path_delay max -fields {slew cap input_pin} -digits 4
report_checks -path_delay min -fields {slew cap input_pin} -digits 4
report_clock_min_period -digits 4
report_tns
report_wns
