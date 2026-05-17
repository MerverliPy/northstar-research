import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from northstar_models import EntityType, ExtractionStatus
from northstar_models.schemas import EntityCreate, ClaimCreate

pytestmark = pytest.mark.asyncio


class TestRunExtraction:
    async def test_run_extraction_basic(self, mock_db, mock_llm_service, mock_neo4j, mock_vector_store):
        from research_agent.services.extraction import run_extraction, ExtractedEntity, ExtractedClaim, ExtractionResult

        mock_llm_service.generate_structured.return_value = ExtractionResult(
            entities=[
                ExtractedEntity(name="Org1", entity_type=EntityType.ORGANIZATION, description="desc", confidence=0.9),
                ExtractedEntity(name="Person1", entity_type=EntityType.PERSON, description=None, confidence=0.8),
            ],
            claims=[
                ExtractedClaim(claim_text="Claim 1", claim_type="fact", confidence=0.85, entity_name="Org1"),
            ],
        )

        source_id = uuid.uuid4()
        await run_extraction(
            source_id=source_id,
            llm_service=mock_llm_service,
            db=mock_db,
            neo4j=mock_neo4j,
            vector_store=mock_vector_store,
            force=False,
        )

        mock_db.get_source.assert_awaited_once_with(source_id)
        mock_db.get_extraction_log.assert_awaited_once_with(source_id)
        mock_db.update_extraction_log.assert_awaited()
        mock_llm_service.generate_structured.assert_awaited_once()
        mock_db.bulk_create_entities.assert_awaited_once()
        mock_db.bulk_create_claims.assert_awaited_once()
        mock_vector_store.add_documents.assert_awaited_once()

    async def test_run_extraction_with_force(self, mock_db, mock_llm_service, mock_neo4j, mock_vector_store):
        from research_agent.services.extraction import run_extraction, ExtractedEntity, ExtractedClaim, ExtractionResult

        mock_llm_service.generate_structured.return_value = ExtractionResult(
            entities=[
                ExtractedEntity(name="Org1", entity_type=EntityType.ORGANIZATION, description="desc", confidence=0.9),
            ],
            claims=[
                ExtractedClaim(claim_text="Claim 1", claim_type="fact", confidence=0.85, entity_name="Org1"),
            ],
        )

        source_id = uuid.uuid4()
        await run_extraction(
            source_id=source_id,
            llm_service=mock_llm_service,
            db=mock_db,
            neo4j=mock_neo4j,
            vector_store=mock_vector_store,
            force=True,
        )

        mock_neo4j.create_entity_node.assert_awaited()
        mock_neo4j.create_claim_relationship.assert_awaited()

    async def test_run_extraction_source_not_found(self, mock_db, mock_llm_service, mock_neo4j, mock_vector_store):
        from research_agent.services.extraction import run_extraction

        mock_db.get_source.return_value = None
        source_id = uuid.uuid4()
        await run_extraction(
            source_id=source_id,
            llm_service=mock_llm_service,
            db=mock_db,
            neo4j=mock_neo4j,
            vector_store=mock_vector_store,
            force=False,
        )

        mock_db.get_extraction_log.assert_not_awaited()

    async def test_run_extraction_log_not_found(self, mock_db, mock_llm_service, mock_neo4j, mock_vector_store):
        from research_agent.services.extraction import run_extraction

        mock_db.get_extraction_log.return_value = None
        source_id = uuid.uuid4()
        await run_extraction(
            source_id=source_id,
            llm_service=mock_llm_service,
            db=mock_db,
            neo4j=mock_neo4j,
            vector_store=mock_vector_store,
            force=False,
        )

        mock_db.update_extraction_log.assert_not_awaited()

    async def test_run_extraction_error_handling(self, mock_db, mock_llm_service, mock_neo4j, mock_vector_store):
        from research_agent.services.extraction import run_extraction

        mock_llm_service.generate_structured.side_effect = ValueError("LLM error")
        source_id = uuid.uuid4()

        await run_extraction(
            source_id=source_id,
            llm_service=mock_llm_service,
            db=mock_db,
            neo4j=mock_neo4j,
            vector_store=mock_vector_store,
            force=False,
        )

        mock_db.update_extraction_log.assert_awaited()
        call_args = mock_db.update_extraction_log.await_args_list[-1]
        args, _ = call_args
        assert len(args) >= 2
        assert args[1] == ExtractionStatus.FAILED

    async def test_extraction_creates_extraction_log(self, mock_db, mock_llm_service, mock_neo4j, mock_vector_store):
        from research_agent.services.extraction import run_extraction, ExtractionResult, ExtractedEntity, ExtractedClaim

        mock_llm_service.generate_structured.return_value = ExtractionResult(
            entities=[
                ExtractedEntity(name="E1", entity_type=EntityType.CONCEPT, description=None, confidence=0.7),
            ],
            claims=[
                ExtractedClaim(claim_text="C1", claim_type="fact", confidence=0.8, entity_name="E1"),
            ],
        )

        source_id = uuid.uuid4()
        await run_extraction(
            source_id=source_id,
            llm_service=mock_llm_service,
            db=mock_db,
            neo4j=mock_neo4j,
            vector_store=mock_vector_store,
            force=False,
        )

        mock_db.update_extraction_log.assert_awaited()
        last_call = mock_db.update_extraction_log.await_args_list[-1]
        args, _ = last_call
        assert len(args) >= 2
        assert args[1] == ExtractionStatus.COMPLETED

    async def test_extraction_with_empty_claims(self, mock_db, mock_llm_service, mock_neo4j, mock_vector_store):
        from research_agent.services.extraction import run_extraction, ExtractionResult, ExtractedEntity

        mock_llm_service.generate_structured.return_value = ExtractionResult(
            entities=[
                ExtractedEntity(name="E1", entity_type=EntityType.CONCEPT, description=None, confidence=0.7),
            ],
            claims=[],
        )

        source_id = uuid.uuid4()
        await run_extraction(
            source_id=source_id,
            llm_service=mock_llm_service,
            db=mock_db,
            neo4j=mock_neo4j,
            vector_store=mock_vector_store,
            force=False,
        )

        mock_db.bulk_create_entities.assert_awaited_once()
        mock_db.bulk_create_claims.assert_awaited_once_with([])

    async def test_extraction_updates_log_on_completion(self, mock_db, mock_llm_service, mock_neo4j, mock_vector_store):
        from research_agent.services.extraction import run_extraction, ExtractionResult, ExtractedEntity

        mock_llm_service.generate_structured.return_value = ExtractionResult(
            entities=[
                ExtractedEntity(name="E1", entity_type=EntityType.TECHNOLOGY, description=None, confidence=0.9),
            ],
            claims=[],
        )

        source_id = uuid.uuid4()
        await run_extraction(
            source_id=source_id,
            llm_service=mock_llm_service,
            db=mock_db,
            neo4j=mock_neo4j,
            vector_store=mock_vector_store,
            force=False,
        )

        mock_db.update_extraction_log.assert_awaited()
        final_update = mock_db.update_extraction_log.await_args_list[-1]
        args, _ = final_update
        assert len(args) >= 2
        assert args[1] == ExtractionStatus.COMPLETED
