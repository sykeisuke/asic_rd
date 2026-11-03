# Legacy digital blocks

Blocks that are no longer on the Tape-out 1 path. They are kept, not deleted,
because older regressions still build them.

| Block | What it was | Still used by |
| --- | --- | --- |
| [`four_cell_wilkinson_controller/`](four_cell_wilkinson_controller/) | Sequential controller: one shared comparator, four cells converted one at a time through an analog MUX, 6-bit. Superseded on 2026-09-18 by [`../parallel_wilkinson_controller/`](../parallel_wilkinson_controller/). | `make controller`, `make four-cell-cosim`, `make phase-sweep` |
| [`wilkinson_counter/`](wilkinson_counter/) | First 6-bit binary counter and capture (August 2026). | `make counter`, `make cosim` |
| [`delay_line.v`](delay_line.v) | Kept `dlybuff_2` / `dlya_1` delay line that ordered the cell switches `s2`/`s0`/`s1` from the digital top (2026-10-28 to 2026-11-03). Superseded by the sequencer inside the Analog_top macro (`mixed_signal/sample_seq`, ADR 0027). | nothing |

The current digital path is [`../parallel_wilkinson_controller/`](../parallel_wilkinson_controller/)
inside [`../asic_digital_top/`](../asic_digital_top/).
