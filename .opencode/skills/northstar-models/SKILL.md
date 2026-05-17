---
name: northstar-models
description: Patterns for Pydantic schemas and SQLAlchemy ORM models in the Northstar Research project
---
## Schema Triple Pattern

Every entity has three Pydantic models:
```python
from pydantic import BaseModel

class XCreate(BaseModel):
    """Fields required to create an entity."""
    ...

class XRead(BaseModel):
    """Fields returned when reading an entity."""
    model_config = {"from_attributes": True}

class XUpdate(BaseModel):
    """Fields that can be updated. All optional."""
    ...
```

## SQLAlchemy ORM Models

All ORM models in `northstar_models/models.py` inherit `CommonModel(DeclarativeBase)`:
```python
from northstar_models.base import CommonModel
from sqlalchemy.orm import mapped_column
from sqlalchemy import JSON, String, Text

class Source(CommonModel):
    __tablename__ = "sources"
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
```

Key points:
- `CommonModel` provides: `id` (UUID, PK), `created_at` (datetime), `updated_at` (datetime)
- Metadata column: Pydantic field is `metadata`, SQLAlchemy column is `metadata_`, DB column is `"metadata"`
- All columns use `mapped_column()` with explicit types
- No relationships in models (graph relationships handled by Neo4jRepository)

## Enums

Defined in `northstar_models/enums.py`. Used in both Pydantic schemas and SQLAlchemy models:
```python
from enum import Enum
class SourceType(str, Enum):
    CHAT = "chat"
    DOCUMENT = "document"
```

## Editable Install Chain

- `northstar-models` has NO internal dependencies (standalone)
- `northstar-llm` depends on models
- `northstar-vector` depends on llm
- `northstar-db` depends on models
