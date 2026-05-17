# Security Policy

## Supported scope

This project is intended for local-first operation on trusted infrastructure. Treat it as private infrastructure unless a deployment has been explicitly hardened for public exposure.

## Sensitive material that must not be committed

- `.env` files or real environment values.
- Tailscale auth keys, API keys, tokens, passwords, cookies, private keys, and certificates.
- SQLite databases, PostgreSQL dumps, Neo4j dumps, embeddings stores, logs, backups, and exports.
- Raw chat/session memory dumps that contain local paths, hostnames, IP addresses, or private research content.
- Machine-specific service files with real usernames, absolute paths, or tailnet hostnames.

## Reporting a vulnerability

Open a private issue or contact the maintainer directly. Do not post secrets or exploit details in a public issue.

## Default security posture

- Bind local services to `127.0.0.1` unless there is a deliberate reverse-proxy or tailnet exposure path.
- Use HTTPS for tailnet-facing services when served through Tailscale Serve.
- Keep destructive cleanup disabled by default.
- Run backup/export/restore validation before any migration or graph rebuild.
