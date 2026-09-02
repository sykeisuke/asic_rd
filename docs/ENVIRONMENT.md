# Development environment

## Host baseline

- Architecture: Apple Silicon arm64
- macOS: 26.5.2
- GitHub CLI: 2.97.0
- Docker Desktop: 4.85.0
- Docker CLI: 29.6.2
- IIC-OSIC-TOOLS tag: 2026.07
- IIC-OSIC-TOOLS index digest:
  `sha256:5d6adf1f437cd0f2f8f8614488ec3c247ba8c768f4663a25d5e997b30ccb13b0`
- IIC-OSIC-TOOLS architecture: native arm64
- GF180 Ciel revision: `f6eeac7dad085ffcc829ccfd721f7b4ce39edcf7`
- gdsfactory (in image): 9.46.0; kfactory 3.0.3; KLayout 0.30.9
- gdsfactory `gf180mcu` PDK plugin (via `make tools`): 1.0.0

Docker Desktop was installed without system-wide binary links. Use
`scripts/docker.sh` or add this directory to the shell PATH:

```text
/Applications/Docker.app/Contents/Resources/bin
```

## Next environment checkpoint

1. Verify `make check` succeeds.
2. Install the pinned Python EDA add-ons with `make tools` (gdsfactory
   `gf180mcu` PDK plugin 1.0.0 into the git-ignored `.eda-tools/`).
3. Run the first GF180 transistor simulation with `make nmos-dc`.
4. Open the browser desktop with `make vnc`.
5. Reproduce the NMOS test in Xschem and inspect the output curves.

