"""Chat orchestrator API with SSE streaming and conversation history."""

import json

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from starlette.requests import ClientDisconnect

from research_portal.services.orchestrator import Orchestrator
from research_portal.services.conversation import ConversationStore

router = APIRouter(prefix="/chat", tags=["chat"])


async def _get_orchestrator(request: Request) -> Orchestrator:
    return request.app.state.orchestrator


async def _get_conversation_store(request: Request) -> ConversationStore:
    return request.app.state.conversation_store


@router.get("/orchestrate")
async def orchestrate(
    request: Request,
    message: str = Query(..., description="Natural language message"),
    conversation_id: str | None = Query(None),
):
    """SSE endpoint: interprets natural language and executes platform operations."""
    orchestrator = await _get_orchestrator(request)
    store = await _get_conversation_store(request)

    conv_id = conversation_id
    if conv_id is None:
        title = message[:80] + ("..." if len(message) > 80 else "")
        conv_full = store.create_conversation(title=title)
        conv_id = conv_full["id"]

    store.add_message(
        conversation_id=conv_id,
        role="user",
        content=message,
    )

    tool_results_buffer: list[dict] = []
    assistant_content_parts: list[str] = []

    async def event_stream():
        try:
            async for event in orchestrator.orchestrate(message):
                event_type = event.get("event", "message")

                if event_type == "thinking":
                    pass

                elif event_type == "action":
                    tool_results_buffer.append(event.get("data", {}))

                elif event_type == "result":
                    data = event.get("data", {})
                    existing = next(
                        (t for t in tool_results_buffer if t.get("action") == data.get("action") and t.get("status") == "running"),
                        None,
                    )
                    if existing:
                        existing.update(data)
                    else:
                        tool_results_buffer.append(data)
                    summary = data.get("summary", "")
                    if summary:
                        assistant_content_parts.append(summary)

                elif event_type == "error":
                    assistant_content_parts.append(f"Error: {event.get('data', {}).get('message', 'Unknown error')}")

                yield f"event: {event_type}\ndata: {json.dumps(event.get('data', {}))}\n\n"

            assistant_content = "\n".join(assistant_content_parts)

            store.add_message(
                conversation_id=conv_id,
                role="assistant",
                content=assistant_content,
                tool_results=tool_results_buffer if tool_results_buffer else None,
            )

        except ClientDisconnect:
            pass

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
    )


@router.get("/conversations")
async def list_conversations(request: Request, limit: int = Query(50)):
    store = await _get_conversation_store(request)
    return store.list_conversations(limit=limit)


@router.post("/conversations")
async def create_conversation(request: Request, title: str = "New Conversation", project_id: str | None = None):
    store = await _get_conversation_store(request)
    return store.create_conversation(title=title, project_id=project_id)


@router.get("/conversations/{conv_id}")
async def get_conversation(request: Request, conv_id: str):
    store = await _get_conversation_store(request)
    conv = store.get_conversation(conv_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.delete("/conversations/{conv_id}")
async def delete_conversation(request: Request, conv_id: str):
    store = await _get_conversation_store(request)
    deleted = store.delete_conversation(conv_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"deleted": True}
