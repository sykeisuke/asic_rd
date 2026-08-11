# GF180 Wilkinson ramp-generator baseline

This block charges a 1 pF ramp capacitor from a biased PMOS current source and
uses an NMOS switch to reset the ramp. It is the first on-chip ramp candidate;
the prototype retains an external ramp input as the mandatory debug path.

Run:

```sh
make ramp-generator
```

The automated test measures reset voltage, average slope from 0.6 V to 1.8 V,
the slope difference between the lower and upper halves, and average power.
Generated files under `work/` are not tracked by Git.

The present circuit requires an external 2.2 V PMOS bias. A self-biased or
programmable current reference and a buffered monitor output remain future
integration work.
