# Liberty timing model of the hardened digital top, so chip STA can time
# through the hard macro (LibreLane black-boxes a macro with a netlist but
# no liberty). OpenSTA's write_timing_model on the macro's own gate netlist
# with the as_sc library of each corner and the macro's own constraints.
# No parasitics: the model is the macro's cell delays only, optimistic by
# its wire delay. Run from chip_integration/ (scripts/macros.py digital):
#
#   sta -no_init -exit scripts/digital_timing_model.tcl
set in  inputs/digital
set lib /foss/pdk_libs/gf180mcuD/libs.ref/gf180mcu_as_sc_mcu7t3v3/lib
set out work/macros/asic_digital_top/lib
file mkdir $out
foreach corner {tt_025C_3v30 ff_n40C_3v60 ss_125C_3v00} {
    sta::clear_sta
    read_liberty $lib/gf180mcu_as_sc_mcu7t3v3__$corner.lib
    read_verilog $in/asic_digital_top.nl.v
    link_design asic_digital_top
    read_sdc $in/asic_digital_top.sdc
    write_timing_model -library_name asic_digital_top_$corner \
        -cell_name asic_digital_top $out/asic_digital_top__$corner.lib
    puts "digital_timing_model_$corner = 1"
}
