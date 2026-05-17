from pydantic import BaseModel


class DocumentChunk(BaseModel):
    id: str
    text: str
    metadata: dict = {}
    embedding: list[float] | None = None
    source_id: str | None = None
    project_id: str | None = None


class SearchResult(BaseModel):
    id: str
    text: str
    score: float
    metadata: dict
    source_id: str | None = None
    project_id: str | None = None


class CollectionInfo(BaseModel):
    name: str
    count: int
    dimension: int | None = None
