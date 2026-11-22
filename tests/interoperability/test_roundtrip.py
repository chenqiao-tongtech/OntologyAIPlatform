#
//  test_roundtrip.py
//  
//
//  Created by joechen on 2026/11/21.
//



from pathlib import Path

from rdflib import Graph
from rdflib.compare import isomorphic

from ontology.formats.importers.rdf_importer import RdfImporter
from ontology.formats.registry import FormatId
from ontology.formats.serializers.rdf_serializer import RdfSerializer


SAMPLES = Path(__file__).resolve().parents[2] / "ontology" / "samples"


def test_turtle_to_rdfxml_roundtrip():
    source_bytes = (SAMPLES / "customer.ttl").read_bytes()

    imported = RdfImporter().import_bytes(
        source_bytes,
        FormatId.TURTLE,
    )

    exported = RdfSerializer().serialize(
        imported.graph,
        FormatId.RDFXML,
    )

    reimported = RdfImporter().import_bytes(
        exported.content,
        FormatId.RDFXML,
    )

    assert isomorphic(imported.graph, reimported.graph)


def test_rdfxml_to_turtle_roundtrip():
    source_bytes = (SAMPLES / "customer.rdf").read_bytes()

    imported = RdfImporter().import_bytes(
        source_bytes,
        FormatId.RDFXML,
    )

    exported = RdfSerializer().serialize(
        imported.graph,
        FormatId.TURTLE,
    )

    reimported = RdfImporter().import_bytes(
        exported.content,
        FormatId.TURTLE,
    )

    assert isomorphic(imported.graph, reimported.graph)


def test_blank_node_restriction_survives_serialization():
    source_bytes = (SAMPLES / "customer.ttl").read_bytes()

    imported = RdfImporter().import_bytes(
        source_bytes,
        FormatId.TURTLE,
    )

    exported = RdfSerializer().serialize(
        imported.graph,
        FormatId.RDFXML,
    )

    reimported = RdfImporter().import_bytes(
        exported.content,
        FormatId.RDFXML,
    )

    assert isomorphic(imported.graph, reimported.graph)
