# Northstar Research CLI Tools

## extract
Trigger LLM extraction on a source:

    python tools/extract.py <source-id> [--force] [--agent-url http://localhost:8099]

## query
Search and retrieve research data:

    python tools/query.py projects [--limit 50] [--offset 0]
    python tools/query.py sources --project-id <uuid>
    python tools/query.py entities [--source-id <uuid>]
    python tools/query.py claims [--source-id <uuid>]
    python tools/query.py search --query "text" --project-id <uuid>

## export
Export source data as Markdown or JSON:

    python tools/export.py <source-id> [--format markdown|json] [--output file.md]
