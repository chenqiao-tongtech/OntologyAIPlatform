//
//  ImportedRdfDocument.swift
//  
//
//  Created by joechen on 2026/11/21.
//



from dataclasses import dataclass
from hashlib import sha256

from rdflib import Graph

from ontology.formats.registry import (
    FormatId,
    get_format_spec,
)


@dataclass
class ImportedRdfDocument:
    graph: Graph
    format_id: FormatId
    source_sha256: str
    triple_count: int


class RdfImporter:
    def __init__(self, max_bytes: int = 20 * 1024 * 1024):
        if max_bytes <= 0:
            raise ValueError("max_bytes must be positive")
        self.max_bytes = max_bytes

    def import_bytes(
        self,
        content: bytes,
        format_id: FormatId,
        base_iri: str | None = None,
    ) -> ImportedRdfDocument:
        if not isinstance(content, bytes):
            raise TypeError("RDF content must be bytes")

        if not content:
            raise ValueError("Empty RDF document")

        if len(content) > self.max_bytes:
            raise ValueError(
                f"RDF document exceeds limit of {self.max_bytes} bytes"
            )

        spec = get_format_spec(format_id)
        if not spec.import_enabled:
            raise ValueError(f"Import is disabled for {format_id.value}")

        graph = Graph()

        try:
            graph.parse(
                data=content,
                format=spec.rdflib_format,
                publicID=base_iri,
            )
        except Exception as exc:
            raise ValueError(
                f"Unable to parse {format_id.value}: {exc}"
            ) from exc

        return ImportedRdfDocument(
            graph=graph,
            format_id=format_id,
            source_sha256=sha256(content).hexdigest(),
            triple_count=len(graph),
        )
