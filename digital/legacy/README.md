# Legacy digital blocks

Blocks that are no longer on the Tape-out 1 path. They are kept, not deleted,
because older regressions still build them.

| Block | What it was | Still used by |
| --- | --- | --- |
| [`four_cell_wilkinson_controller/`](four_cell_wilkinson_controller/) | Sequential controller: one shared comparator, four cells converted one at a time through an analog MUX, 6-bit. Superseded on 2026-09-18 by [`../parallel_wilkinson_controller/`](../parallel_wilkinson_controller/). | `make controller`, `make four-cell-cosim`, `make phase-sweep` |
| [`wilkinson_counter/`](wilkinson_counter/) | First 6-bit binary counter and capture (August 2026). | `make counter`, `make cosim` |

The current digital path is [`../parallel_wilkinson_controller/`](../parallel_wilkinson_controller/)
inside [`../asic_digital_top/`](../asic_digital_top/).
