#!/usr/bin/env python3
"""
Query CLI — search and retrieve research data.
Usage: python tools/query.py <command> [options]

Commands:
  projects    List or search projects
  sources     List sources for a project
  entities    List entities
  claims      List claims
  search      Vector search for content
"""

import argparse
import sys
import uuid

import httpx


def fmt_val(v):
    if v is None:
        return "-"
    s = str(v)
    if len(s) > 60:
        return s[:57] + "..."
    return s


def fmt_table(rows, headers):
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(fmt_val(val)))
    sep = "  ".join("-" * w for w in col_widths)
    hdr = "  ".join(h.ljust(w) for h, w in zip(headers, col_widths))
    print(hdr)
    print(sep)
    for row in rows:
        line = "  ".join(fmt_val(v).ljust(w) for v, w in zip(row, col_widths))
        print(line)


def cmd_projects(args):
    url = f"{args.agent_url}/api/v1/projects/"
    try:
        resp = httpx.get(url, params={"limit": args.limit, "offset": args.offset}, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except httpx.HTTPStatusError as e:
        print(f"Error: HTTP {e.response.status_code}")
        sys.exit(1)
    except httpx.RequestError as e:
        print(f"Error: connection failed — {e}")
        sys.exit(1)

    if not data:
        print("No projects found.")
        return
    rows = [(p["id"], p["name"], p["status"], p.get("created_at", "-")) for p in data]
    fmt_table(rows, ["ID", "Name", "Status", "Created"])


def cmd_sources(args):
    if not args.project_id:
        print("Error: --project-id is required")
        sys.exit(1)
    url = f"{args.agent_url}/api/v1/sources/"
    try:
        resp = httpx.get(url, params={"project_id": args.project_id, "limit": args.limit, "offset": args.offset}, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except httpx.HTTPStatusError as e:
        print(f"Error: HTTP {e.response.status_code}")
        sys.exit(1)
    except httpx.RequestError as e:
        print(f"Error: connection failed — {e}")
        sys.exit(1)

    if not data:
        print("No sources found for this project.")
        return
    rows = [(s["id"], s["title"], s.get("content_type", "-"), s.get("created_at", "-")) for s in data]
    fmt_table(rows, ["ID", "Title", "Type", "Created"])


def cmd_entities(args):
    url = f"{args.agent_url}/api/v1/entities/"
    params = {"limit": args.limit, "offset": args.offset}
    if args.source_id:
        params["source_id"] = args.source_id
    if args.project_id:
        params["project_id"] = args.project_id
    try:
        resp = httpx.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except httpx.HTTPStatusError as e:
        print(f"Error: HTTP {e.response.status_code}")
        sys.exit(1)
    except httpx.RequestError as e:
        print(f"Error: connection failed — {e}")
        sys.exit(1)

    if not data:
        print("No entities found.")
        return
    rows = [(e["id"], e["name"], e.get("entity_type", "-"), fmt_val(e.get("description"))) for e in data]
    fmt_table(rows, ["ID", "Name", "Type", "Description"])


def cmd_claims(args):
    url = f"{args.agent_url}/api/v1/claims/"
    params = {"limit": args.limit, "offset": args.offset}
    if args.source_id:
        params["source_id"] = args.source_id
    if args.entity_id:
        params["entity_id"] = args.entity_id
    try:
        resp = httpx.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except httpx.HTTPStatusError as e:
        print(f"Error: HTTP {e.response.status_code}")
        sys.exit(1)
    except httpx.RequestError as e:
        print(f"Error: connection failed — {e}")
        sys.exit(1)

    if not data:
        print("No claims found.")
        return
    rows = [(c["id"], fmt_val(c.get("claim_text")), c.get("claim_type", "-"), c.get("confidence", "-")) for c in data]
    fmt_table(rows, ["ID", "Claim", "Type", "Confidence"])


def cmd_search(args):
    if not args.query:
        print("Error: --query is required")
        sys.exit(1)
    if not args.project_id:
        print("Error: --project-id is required")
        sys.exit(1)
    url = f"{args.agent_url}/api/v1/search/"
    payload = {"query": args.query, "project_id": args.project_id, "top_k": args.top_k}
    try:
        resp = httpx.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except httpx.HTTPStatusError as e:
        print(f"Error: HTTP {e.response.status_code}")
        sys.exit(1)
    except httpx.RequestError as e:
        print(f"Error: connection failed — {e}")
        sys.exit(1)

    if not data:
        print("No results found.")
        return
    rows = [(r.get("source_id", "-"), f"{r.get('score', 0):.4f}", fmt_val(r.get("content"))) for r in data]
    fmt_table(rows, ["Source ID", "Score", "Content"])


def main():
    parser = argparse.ArgumentParser(description="Query Northstar Research data")
    parser.add_argument("command", choices=["projects", "sources", "entities", "claims", "search"], help="Command to run")
    parser.add_argument("--agent-url", default="http://localhost:8099", help="Research Agent URL")
    parser.add_argument("--limit", type=int, default=50, help="Max results")
    parser.add_argument("--offset", type=int, default=0, help="Result offset")
    parser.add_argument("--project-id", help="Project UUID")
    parser.add_argument("--source-id", help="Source UUID")
    parser.add_argument("--entity-id", help="Entity UUID")
    parser.add_argument("--query", help="Search query text")
    parser.add_argument("--top-k", type=int, default=5, help="Top-K results for search")

    args = parser.parse_args()

    if args.project_id:
        try:
            uuid.UUID(args.project_id)
        except ValueError:
            print(f"Error: invalid project ID '{args.project_id}'")
            sys.exit(1)
    if args.source_id:
        try:
            uuid.UUID(args.source_id)
        except ValueError:
            print(f"Error: invalid source ID '{args.source_id}'")
            sys.exit(1)
    if args.entity_id:
        try:
            uuid.UUID(args.entity_id)
        except ValueError:
            print(f"Error: invalid entity ID '{args.entity_id}'")
            sys.exit(1)

    cmds = {
        "projects": cmd_projects,
        "sources": cmd_sources,
        "entities": cmd_entities,
        "claims": cmd_claims,
        "search": cmd_search,
    }
    cmds[args.command](args)


if __name__ == "__main__":
    main()
