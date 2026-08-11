# Gray capture synthesis results

Date: 2026-08-11

The self-checking RTL test captures codes 16 and 20 from asynchronous
comparator edges and passes. The standalone block maps to 92 GF180
`mcu7t5v0` cells with a Liberty area of 3174.2592 um^2 at TT, 25 C, 3.3 V.

The mapped capture flops use the comparator input as a local falling-edge
clock. This is intentional and requires dedicated placement, clock routing,
and CDC review rather than ordinary synchronous timing assumptions.
