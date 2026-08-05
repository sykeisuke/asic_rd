# GF180 3.3 V NMOS DC sweep

This is the first toolchain and PDK smoke test. It sweeps `VDS` from 0 V to
3.3 V for twelve `VGS` values between 0 V and 3.3 V. The device is the
GF180MCU `nfet_03v3` model with `L=0.28 um` and `W=1 um`.

Run:

```sh
make nmos-dc
```

Generated data is written to `work/nmos_id_vds.csv` and is intentionally not
tracked by Git. The Xschem source is `nmos_dc.sch`.

