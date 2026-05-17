#!/usr/bin/env python3
"""
Extraction CLI — trigger LLM extraction on sources.
Usage: python tools/extract.py <source-id> [--force] [--agent-url http://localhost:8099]
"""

import argparse
import sys
import uuid

import httpx


def main():
    parser = argparse.ArgumentParser(description="Trigger LLM extraction on a source")
    parser.add_argument("source_id", help="Source UUID to extract")
    parser.add_argument("--force", action="store_true", help="Bypass FORCE_GRAPH_EXTRACTION gate")
    parser.add_argument("--agent-url", default="http://localhost:8099", help="Research Agent URL")
    args = parser.parse_args()

    try:
        uuid.UUID(args.source_id)
    except ValueError:
        print(f"Error: invalid source ID '{args.source_id}' — must be a valid UUID")
        sys.exit(1)

    url = f"{args.agent_url.rstrip('/')}/api/v1/extraction/extract"
    payload = {"source_id": args.source_id, "force": args.force}

    try:
        resp = httpx.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
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

    print(f"extraction_id: {data.get('extraction_id')}")
    print(f"status:        {data.get('status')}")
    print(f"message:       {data.get('message')}")


if __name__ == "__main__":
    main()
