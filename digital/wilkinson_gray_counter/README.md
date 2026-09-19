# Gray-coded Wilkinson capture (single-channel reference)

> Since 2026-09-18 the production path is the four-channel capture inside
> [`../parallel_wilkinson_controller/`](../parallel_wilkinson_controller/),
> which uses the same Gray-capture and toggle-synchronizer scheme per cell.
> This single-channel block remains the reference implementation and feeds
> the legacy sequential controller.

This production-path counter converts its synchronous binary count to Gray
code and captures that Gray word directly on the falling comparator edge. A
toggle synchronizer returns the capture event to the main clock domain, where
the word is decoded and presented with the existing `valid` interface.

Only one Gray bit changes at a count boundary, limiting an ambiguous capture to
adjacent codes. Run functional verification and GF180 mapping with:

```sh
make gray-counter
```

The comparator is intentionally used as a local capture clock. Physical clock
routing, recovery/removal checks, and transistor-level metastability behavior
must be reviewed during backend signoff.
