import uuid

import structlog
from pydantic import BaseModel

from northstar_db import Neo4jRepository, PostgresRepository
from northstar_llm import LLMService
from northstar_models import ClaimCreate, EntityCreate, EntityType, ExtractionStatus
from northstar_models.models import Source
from northstar_vector import DocumentChunk, VectorStore

logger = structlog.get_logger(__name__)


class ExtractedEntity(BaseModel):
    name: str
    entity_type: EntityType
    description: str | None = None
    confidence: float | None = None


class ExtractedClaim(BaseModel):
    claim_text: str
    claim_type: str | None = None
    confidence: float | None = None
    entity_name: str | None = None


class ExtractionResult(BaseModel):
    entities: list[ExtractedEntity]
    claims: list[ExtractedClaim]


EXTRACTION_SYSTEM_PROMPT = """You are a research extraction system. Extract entities and claims from the given source content.
Return ONLY valid JSON matching this schema:
{
  "entities": [{"name": "...", "entity_type": "person|organization|concept|technology|location|event|product|document|other", "description": "...", "confidence": 0.0-1.0}],
  "claims": [{"claim_text": "...", "claim_type": "...", "confidence": 0.0-1.0, "entity_name": "..."}]
}"""


EXTRACTION_USER_PROMPT_TEMPLATE = """Extract entities and claims from the following source content:

Title: {title}
Content Type: {content_type}

Content:
{content}

Return entities and claims in the specified JSON format."""


async def run_extraction(
    source_id: uuid.UUID,
    llm_service: LLMService,
    db: PostgresRepository,
    neo4j: Neo4jRepository,
    vector_store: VectorStore,
    force: bool = False,
) -> None:
    source = await db.get_source(source_id)
    if source is None:
        logger.error("source_not_found", source_id=str(source_id))
        return

    log = await db.get_extraction_log(source_id)
    if log is None:
        logger.error("extraction_log_not_found", source_id=str(source_id))
        return

    try:
        log = await db.update_extraction_log(log.id, ExtractionStatus.IN_PROGRESS)

        prompt = EXTRACTION_USER_PROMPT_TEMPLATE.format(
            title=source.title,
            content_type=source.content_type,
            content=source.raw_content[:8000],
        )

        result: ExtractionResult = await llm_service.generate_structured(
            prompt=prompt,
            system_prompt=EXTRACTION_SYSTEM_PROMPT,
            response_model=ExtractionResult,
        )

        entity_creates = [
            EntityCreate(
                source_id=source_id,
                name=e.name,
                entity_type=e.entity_type,
                description=e.description,
                confidence=e.confidence,
            )
            for e in result.entities
        ]

        created_entities = await db.bulk_create_entities(entity_creates)

        entity_name_map: dict[str, uuid.UUID] = {}
        for ce in created_entities:
            entity_name_map[ce.name] = ce.id

        claim_creates = [
            ClaimCreate(
                source_id=source_id,
                entity_id=entity_name_map.get(c.entity_name) if c.entity_name else None,
                claim_text=c.claim_text,
                claim_type=c.claim_type,
                confidence=c.confidence,
            )
            for c in result.claims
        ]

        created_claims = await db.bulk_create_claims(claim_creates)

        if force:
            for entity in created_entities:
                await neo4j.create_entity_node(entity)
            for claim in created_claims:
                await neo4j.create_claim_relationship(claim)

        content_for_vector = f"{source.title}\n\n{source.raw_content[:4000]}"
        doc = DocumentChunk(
            id=f"source_{source.id}",
            text=content_for_vector,
            metadata={"title": source.title, "content_type": source.content_type},
            source_id=str(source.id),
            project_id=str(source.project_id),
        )
        await vector_store.add_documents("default", [doc])

        await db.update_extraction_log(
            log.id,
            ExtractionStatus.COMPLETED,
            entities_found=len(created_entities),
        )

        logger.info(
            "extraction_completed",
            source_id=str(source_id),
            entities=len(created_entities),
            claims=len(created_claims),
        )

    except Exception as exc:
        logger.error("extraction_failed", source_id=str(source_id), error=str(exc))
        await db.update_extraction_log(
            log.id,
            ExtractionStatus.FAILED,
            error_message=str(exc),
        )
