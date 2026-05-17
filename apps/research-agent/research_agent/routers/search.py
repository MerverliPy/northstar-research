from fastapi import APIRouter, Depends

from northstar_models import SearchRequest, SearchResult as SearchResultSchema
from northstar_vector import VectorStore

from research_agent.dependencies import get_vector_store

router = APIRouter(prefix="/search", tags=["Search"])


@router.post("/", response_model=list[SearchResultSchema])
async def vector_search(
    req: SearchRequest,
    vector_store: VectorStore = Depends(get_vector_store),
):
    project_filters = {"project_id": str(req.project_id)}
    if req.filters:
        project_filters.update(req.filters)

    results = await vector_store.search(
        collection_name="default",
        query=req.query,
        top_k=req.top_k,
        filters=project_filters,
    )

    return [
        SearchResultSchema(
            content=r.text,
            score=r.score,
            metadata=r.metadata,
            source_id=r.source_id,
        )
        for r in results
    ]
