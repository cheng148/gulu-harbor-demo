from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.catalog import Species


class KnowledgeEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    sourceId: str = Field(min_length=1)
    title: str = Field(min_length=1)
    topic: str = Field(min_length=1)
    appliesTo: tuple[Species, ...] = Field(min_length=1)
    rewrittenBody: str = Field(min_length=1)
    sourceName: str = Field(min_length=1)
    sourceLocator: str = Field(min_length=1)
    publicationDate: date | None
    publicationDateUnknown: bool
    localReviewDate: date
    applicabilityBoundary: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_publication_date_state(self) -> KnowledgeEntry:
        if self.publicationDate is None and not self.publicationDateUnknown:
            raise ValueError("missing publication date must be marked unknown")
        if self.publicationDate is not None and self.publicationDateUnknown:
            raise ValueError("known publication date cannot also be marked unknown")
        return self
