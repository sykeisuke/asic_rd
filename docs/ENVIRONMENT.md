# Development environment

## Host baseline

- Architecture: Apple Silicon arm64
- macOS: 26.5.2
- GitHub CLI: 2.97.0
- Docker Desktop: 4.85.0
- Docker CLI: 29.6.2

Docker Desktop was installed without system-wide binary links. Use
`scripts/docker.sh` or add this directory to the shell PATH:

```text
/Applications/Docker.app/Contents/Resources/bin
```

## Next environment checkpoint

1. Complete the Docker Desktop first-run screen and start its daemon.
2. Verify `./scripts/docker.sh info` succeeds.
3. Install a pinned IIC-OSIC-TOOLS release with GF180 support.
4. Record the image tag and immutable digest here.
5. Run the first GF180 transistor simulation.

