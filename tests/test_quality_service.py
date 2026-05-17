import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from northstar_models import QualityStatus

pytestmark = pytest.mark.asyncio


class TestScoreQuality:
    async def test_score_quality_basic(self, mock_db, mock_llm_service):
        from research_agent.services.quality import score_quality

        mock_llm_service.generate_structured.return_value = MagicMock(
            score=0.85,
            reasoning="Good content quality",
        )

        source_id = uuid.uuid4()
        result = await score_quality(
            source_id=source_id,
            content="Test content",
            criteria={"relevance": "high"},
            llm_service=mock_llm_service,
            db=mock_db,
        )

        assert result.score == 0.85
        assert result.quality_status == QualityStatus.ASSESSED
        assert result.reasoning == "Good content quality"
        mock_llm_service.generate_structured.assert_awaited_once()
        mock_db.create_analysis.assert_awaited_once()

    async def test_score_quality_low_score(self, mock_db, mock_llm_service):
        from research_agent.services.quality import score_quality

        mock_llm_service.generate_structured.return_value = MagicMock(
            score=0.2,
            reasoning="Poor quality",
        )

        source_id = uuid.uuid4()
        result = await score_quality(
            source_id=source_id,
            content="Low quality content",
            criteria={"accuracy": "low"},
            llm_service=mock_llm_service,
            db=mock_db,
        )

        assert result.score == 0.2
        assert result.quality_status == QualityStatus.FAILED

    async def test_score_quality_persists_analysis(self, mock_db, mock_llm_service):
        from research_agent.services.quality import score_quality

        mock_llm_service.generate_structured.return_value = MagicMock(
            score=0.75,
            reasoning="Decent",
        )

        source_id = uuid.uuid4()
        await score_quality(
            source_id=source_id,
            content="Some content",
            criteria={"clarity": "medium"},
            llm_service=mock_llm_service,
            db=mock_db,
        )

        mock_db.create_analysis.assert_awaited_once()
        call_args = mock_db.create_analysis.await_args_list[0]
        args, _ = call_args
        analysis_data = args[0]
        assert analysis_data.analysis_type == "quality_score"
        assert analysis_data.quality_score == 0.75
        assert analysis_data.source_id == source_id

    async def test_score_quality_uses_primary_model(self, mock_db, mock_llm_service):
        from research_agent.services.quality import score_quality

        mock_llm_service.generate_structured.return_value = MagicMock(
            score=0.9,
            reasoning="Great",
        )
        mock_llm_service._primary_model = "qwen3:14b"

        source_id = uuid.uuid4()
        result = await score_quality(
            source_id=source_id,
            content="Great content",
            criteria={"overall": "high"},
            llm_service=mock_llm_service,
            db=mock_db,
        )

        assert result.model_used == "qwen3:14b"

    async def test_score_quality_error_handling(self, mock_db, mock_llm_service):
        from research_agent.services.quality import score_quality

        mock_llm_service.generate_structured.side_effect = ValueError("LLM error")

        source_id = uuid.uuid4()
        with pytest.raises(ValueError):
            await score_quality(
                source_id=source_id,
                content="Content",
                criteria={"test": "value"},
                llm_service=mock_llm_service,
                db=mock_db,
            )

        mock_db.create_analysis.assert_not_awaited()

    async def test_score_quality_analysis_created_with_correct_type(self, mock_db, mock_llm_service):
        from research_agent.services.quality import score_quality

        mock_llm_service.generate_structured.return_value = MagicMock(
            score=0.65,
            reasoning="Average",
        )

        source_id = uuid.uuid4()
        await score_quality(
            source_id=source_id,
            content="Average content",
            criteria={"readability": "medium"},
            llm_service=mock_llm_service,
            db=mock_db,
        )

        mock_db.create_analysis.assert_awaited_once()
        call_args = mock_db.create_analysis.await_args_list[0]
        args, _ = call_args
        analysis_data = args[0]
        assert analysis_data.analysis_type == "quality_score"
        assert "score" in analysis_data.content
        assert "reasoning" in analysis_data.content
        assert "criteria" in analysis_data.content

    async def test_score_quality_boundary_30_percent(self, mock_db, mock_llm_service):
        from research_agent.services.quality import score_quality

        mock_llm_service.generate_structured.return_value = MagicMock(
            score=0.3,
            reasoning="Borderline",
        )

        source_id = uuid.uuid4()
        result = await score_quality(
            source_id=source_id,
            content="Borderline content",
            criteria={"quality": "borderline"},
            llm_service=mock_llm_service,
            db=mock_db,
        )

        assert result.score == 0.3
        assert result.quality_status == QualityStatus.ASSESSED

        mock_llm_service.generate_structured.return_value = MagicMock(
            score=0.29,
            reasoning="Below borderline",
        )

        result = await score_quality(
            source_id=source_id,
            content="Below borderline content",
            criteria={"quality": "low"},
            llm_service=mock_llm_service,
            db=mock_db,
        )

        assert result.score == 0.29
        assert result.quality_status == QualityStatus.FAILED
