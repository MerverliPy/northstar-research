from chat_import_bridge.models import StagedImport


async def to_markdown(staged: StagedImport) -> dict:
    title = staged.title or "Untitled Import"
    content = staged.raw_content or ""
    created = staged.created_at.strftime("%Y-%m-%d %H:%M:%S UTC") if staged.created_at else "Unknown"

    markdown = f"# {title}\n\n**Source:** {staged.source_type}\n**Date:** {created}\n\n{content}"

    return {
        "title": title,
        "markdown": markdown,
        "metadata": {
            "source_type": staged.source_type,
            "created_at": created,
            "status": staged.status,
        },
    }
