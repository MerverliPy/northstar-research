#!/usr/bin/env python3
"""
Export CLI — export research data in various formats.
Usage: python tools/export.py <source-id> [--format markdown|json] [--output file.md]
"""

import argparse
import json
import sys
import uuid

import httpx


def main():
    parser = argparse.ArgumentParser(description="Export source data as Markdown or JSON")
    parser.add_argument("source_id", help="Source UUID to export")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown", help="Output format")
    parser.add_argument("--output", help="Output file path (default: stdout)")
    parser.add_argument("--agent-url", default="http://localhost:8099", help="Research Agent URL")
    args = parser.parse_args()

    try:
        uuid.UUID(args.source_id)
    except ValueError:
        print(f"Error: invalid source ID '{args.source_id}' — must be a valid UUID")
        sys.exit(1)

    url = f"{args.agent_url.rstrip('/')}/api/v1/sources/{args.source_id}"
    try:
        resp = httpx.get(url, timeout=15)
        resp.raise_for_status()
        source = resp.json()
    except httpx.HTTPStatusError as e:
        detail = ""
        try:
            detail = e.response.json().get("detail", "")
        except Exception:
            detail = e.response.text
        print(f"Error: HTTP {e.response.status_code} — {detail or e.response.reason_phrase}")
        sys.exit(1)
    except httpx.RequestError as e:
        print(f"Error: connection failed — {e}")
        sys.exit(1)

    if args.format == "markdown":
        title = source.get("title", "Untitled")
        content = source.get("cleaned_content") or source.get("raw_content", "")
        output = f"# {title}\n\n{content}"
    else:
        output = json.dumps(source, indent=2, default=str)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
            if not output.endswith("\n"):
                f.write("\n")
        print(f"Exported to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
