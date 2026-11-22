//
//  SerializedRdfArtifact.swift
//  
//
//  Created by joechen on 2026/11/21.
//



from dataclasses import dataclass

from rdflib import Graph

from ontology.formats.registry import (
    FormatId,
    get_format_spec,
)


@dataclass(frozen=True)
class SerializedRdfArtifact:
    content: bytes
    format_id: FormatId
    media_type: str


class RdfSerializer:
    def serialize(
        self,
        graph: Graph,
        format_id: FormatId,
    ) -> SerializedRdfArtifact:
        spec = get_format_spec(format_id)

        if not spec.export_enabled:
            raise ValueError(f"Export is disabled for {format_id.value}")

        try:
            output = graph.serialize(
                format=spec.rdflib_format,
                encoding="utf-8",
            )
        except Exception as exc:
            raise ValueError(
                f"Unable to serialize {format_id.value}: {exc}"
            ) from exc

        if isinstance(output, str):
            output = output.encode("utf-8")

        return SerializedRdfArtifact(
            content=output,
            format_id=format_id,
            media_type=spec.media_type,
        )
