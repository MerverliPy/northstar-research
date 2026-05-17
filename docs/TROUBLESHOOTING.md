# Troubleshooting

## Portal route returns HTTP 404

Likely cause: service is running, but the route has not been installed in that app. Check service status and route registration before patching.

## Local HTTP sent to HTTPS tailnet listener

Use HTTPS for Tailscale Serve hostnames and HTTP for `127.0.0.1` inside WSL.

## Docker credential helper failure inside WSL

Symptom:

```text
failed to solve: error getting credentials
A specified logon session does not exist. It may already have been terminated.
```

Conservative repair:

```bash
mkdir -p ~/.docker
[ -f ~/.docker/config.json ] && cp ~/.docker/config.json ~/.docker/config.json.bak.$(date +%Y%m%d-%H%M%S)
printf '{\n  "auths": {}\n}\n' > ~/.docker/config.json
```

## Docker container disappeared after patching

Run from the service directory:

```bash
docker compose up -d --build
docker compose ps
```

## WSL GPU mismatch

In WSL, `lspci` may not show the same GPU state as `nvidia-smi`. Prefer `nvidia-smi` and Docker runtime validation for GPU availability.
