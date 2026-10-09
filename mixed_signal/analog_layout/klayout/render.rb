# Render a GDS to PNG, headless, with the PDK's own layer properties.
#
#   klayout -z -rd input=X.gds -rd out=X.png -r render.rb
#
# -z, not -b: batch mode has no main window and LayoutView cannot be
# created without one. QT_QPA_PLATFORM=offscreen is what keeps -z from
# needing a display.

mw = RBA::Application.instance.main_window
mw.load_layout($input, 0)
lv = mw.current_view

lyp = "/foss/pdks/gf180mcuD/libs.tech/klayout/tech/gf180mcu.lyp"
lv.load_layer_props(lyp) if File.exist?(lyp)

lv.max_hier
lv.zoom_fit
lv.save_image($out, ($width || 1600).to_i, ($height || 1000).to_i)
puts "RENDERED #{$out}"
