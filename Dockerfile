FROM python:3.11-slim AS base
WORKDIR /app
RUN pip install --no-cache-dir uv

FROM base AS agent
COPY packages/northstar-models /app/packages/northstar-models
COPY packages/northstar-llm /app/packages/northstar-llm
COPY packages/northstar-vector /app/packages/northstar-vector
COPY packages/northstar-db /app/packages/northstar-db
COPY apps/research-agent /app/apps/research-agent
RUN pip install -e /app/packages/northstar-models \
    && pip install -e /app/packages/northstar-llm \
    && pip install -e /app/packages/northstar-vector \
    && pip install -e /app/packages/northstar-db \
    && pip install -e /app/apps/research-agent
CMD ["uvicorn", "research_agent.app.main:app", "--host", "0.0.0.0", "--port", "8099"]

FROM base AS bridge
COPY packages/northstar-models /app/packages/northstar-models
COPY apps/chat-import-bridge /app/apps/chat-import-bridge
RUN pip install -e /app/packages/northstar-models \
    && pip install -e /app/apps/chat-import-bridge
CMD ["uvicorn", "chat_import_bridge.app.main:app", "--host", "0.0.0.0", "--port", "3022"]

FROM base AS portal
COPY packages/northstar-models /app/packages/northstar-models
COPY packages/northstar-db /app/packages/northstar-db
COPY apps/research-portal /app/apps/research-portal
RUN pip install -e /app/packages/northstar-models \
    && pip install -e /app/packages/northstar-db \
    && pip install -e /app/apps/research-portal
CMD ["uvicorn", "research_portal.app.main:app", "--host", "0.0.0.0", "--port", "3010"]
