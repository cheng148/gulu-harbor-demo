from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from pydantic import TypeAdapter

from app.domain.catalog import Species
from app.domain.errors import KnowledgeUnavailableError
from app.domain.knowledge import KnowledgeEntry


class KnowledgeRetriever(Protocol):
    def search(
        self,
        required_source_ids: tuple[str, ...],
        species: tuple[Species, ...],
        *,
        expanded: bool,
    ) -> tuple[KnowledgeEntry, ...]: ...


def load_knowledge() -> tuple[KnowledgeEntry, ...]:
    path = Path(__file__).parent.parent / "data" / "knowledge.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    return TypeAdapter(tuple[KnowledgeEntry, ...]).validate_python(payload)


class LocalKnowledgeRetriever:
    def __init__(self, entries: tuple[KnowledgeEntry, ...] | None = None) -> None:
        self._entries = entries if entries is not None else load_knowledge()

    def search(
        self,
        required_source_ids: tuple[str, ...],
        species: tuple[Species, ...],
        *,
        expanded: bool,
    ) -> tuple[KnowledgeEntry, ...]:
        required = set(required_source_ids)
        exact = tuple(entry for entry in self._entries if entry.sourceId in required)
        if not expanded:
            return exact
        allowed_species = set(species)
        return tuple(
            entry
            for entry in self._entries
            if entry.sourceId in required
            or allowed_species.intersection(entry.appliesTo)
        )


def retrieve_knowledge(
    retriever: KnowledgeRetriever,
    required_source_ids: tuple[str, ...],
    species: tuple[Species, ...],
) -> tuple[KnowledgeEntry, ...]:
    required = set(required_source_ids)
    if not required:
        return ()

    found: dict[str, KnowledgeEntry] = {
        entry.sourceId: entry
        for entry in retriever.search(required_source_ids, species, expanded=False)
    }
    if not required.issubset(found):
        found.update(
            {
                entry.sourceId: entry
                for entry in retriever.search(
                    required_source_ids,
                    species,
                    expanded=True,
                )
            }
        )
    if not required.issubset(found):
        raise KnowledgeUnavailableError(
            "required recommendation knowledge is unavailable after one expanded lookup"
        )
    return tuple(found[source_id] for source_id in required_source_ids)
