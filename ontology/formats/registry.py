//
//  import.swift
//  
//
//  Created by joechen on 2026/11/21.
//



from dataclasses import dataclass
from enum import Enum


class FormatId(str, Enum):
    TURTLE = "turtle"
    RDFXML = "rdfxml"
    NTRIPLES = "ntriples"
    JSONLD = "jsonld"


@dataclass(frozen=True)
class FormatSpec:
    format_id: FormatId
    rdflib_format: str
    media_type: str
    extensions: tuple[str, ...]
    import_enabled: bool
    export_enabled: bool
    requires_local_context: bool = False


FORMAT_REGISTRY = {
    FormatId.TURTLE: FormatSpec(
        FormatId.TURTLE,
        "turtle",
        "text/turtle",
        (".ttl",),
        True,
        True,
    ),
    FormatId.RDFXML: FormatSpec(
        FormatId.RDFXML,
        "xml",
        "application/rdf+xml",
        (".rdf", ".xml", ".owl"),
        True,
        True,
    ),
    FormatId.NTRIPLES: FormatSpec(
        FormatId.NTRIPLES,
        "nt",
        "application/n-triples",
        (".nt",),
        True,
        True,
    ),
    FormatId.JSONLD: FormatSpec(
        FormatId.JSONLD,
        "json-ld",
        "application/ld+json",
        (".jsonld",),
        True,
        True,
        requires_local_context=True,
    ),
}


def get_format_spec(format_id: FormatId) -> FormatSpec:
    try:
        return FORMAT_REGISTRY[format_id]
    except KeyError as exc:
        raise ValueError(f"Unsupported RDF format: {format_id}") from exc
