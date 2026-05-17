# Setup

This repository is a scaffold for Northstar Research. It is safe to add to a fresh GitHub repository or use as a documentation/ops root for an existing Northstar Research checkout.

## Requirements

- Linux or WSL2
- Docker and Docker Compose
- Python 3.11+
- systemd user services enabled if running native WSL services
- Tailscale if exposing local dashboards to a tailnet

## Initial local setup

```bash
git clone <repo-url> northstar-research
cd northstar-research
cp config/.env.example .env
make doctor
```

## Existing system setup

For an existing local install, copy files selectively:

```bash
rsync -av --exclude '.git' northstar-research/ ~/northstar-research/
cd ~/northstar-research
make doctor
```

Review any file that could overlap with existing scripts or service files before overwriting.

## Configuration

Use `config/.env.example` as the template. Keep real `.env` values local and untracked.
