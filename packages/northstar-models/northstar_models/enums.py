import enum


class ProjectStatus(enum.StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class ExtractionStatus(enum.StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class EntityType(enum.StrEnum):
    ORGANIZATION = "organization"
    PERSON = "person"
    CONCEPT = "concept"
    TECHNOLOGY = "technology"
    LOCATION = "location"
    EVENT = "event"
    PRODUCT = "product"
    DOCUMENT = "document"
    OTHER = "other"


class QualityStatus(enum.StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    ASSESSED = "assessed"
    FAILED = "failed"


class LLMTask(enum.StrEnum):
    EXTRACTION = "extraction"
    QUALITY = "quality"
    SUMMARIZATION = "summarization"
    SEARCH = "search"
    CLASSIFICATION = "classification"
