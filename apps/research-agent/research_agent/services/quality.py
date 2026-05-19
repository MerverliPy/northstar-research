import uuid

from pydantic import BaseModel

from northstar_db import PostgresRepository
from northstar_llm import LLMService
from northstar_models import AnalysisCreate, QualityScoreResponse, QualityStatus

QUALITY_SYSTEM_PROMPT = """You are a content quality assessor. Score the given content against the specified criteria.
Return ONLY valid JSON matching this schema:
{
  "score": 0.0-1.0,
  "reasoning": "...",
}"""


class LLMQualityResult(BaseModel):
    score: float
    reasoning: str


async def score_quality(
    source_id: uuid.UUID,
    content: str,
    criteria: dict,
    llm_service: LLMService,
    db: PostgresRepository,
) -> QualityScoreResponse:
    criteria_text = ", ".join(f"{k}: {v}" for k, v in criteria.items())
    prompt = f"""Score this content on quality criteria: {criteria_text}

Content:
{content[:6000]}

Return score (0.0-1.0) and reasoning."""

    result: LLMQualityResult = await llm_service.generate_structured(
        prompt=prompt,
        system_prompt=QUALITY_SYSTEM_PROMPT,
        response_model=LLMQualityResult,
    )

    await db.create_analysis(
        AnalysisCreate(
            source_id=source_id,
            analysis_type="quality_score",
            content={"score": result.score, "reasoning": result.reasoning, "criteria": criteria},
            model_used=llm_service._primary_model,
            quality_score=result.score,
        )
    )

    quality_status = QualityStatus.ASSESSED
    if result.score < 0.3:
        quality_status = QualityStatus.FAILED

    return QualityScoreResponse(
        quality_status=quality_status,
        score=result.score,
        reasoning=result.reasoning,
        model_used=llm_service._primary_model,
    )
