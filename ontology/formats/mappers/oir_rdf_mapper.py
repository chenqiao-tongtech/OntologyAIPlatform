//
//  OirRdfMapper.swift
//  
//
//  Created by joechen on 2026/11/21.
//



from uuid import UUID, uuid5

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import OWL, RDF, RDFS, XSD


P1_IMPORT_NAMESPACE = UUID(
    "5cc0f77d-86a8-4a62-9c21-2d6f0b7c8f10"
)


class OirRdfMapper:
    def __init__(self):
        self._graph = Graph()

    @staticmethod
    def internal_id_for_iri(
        ontology_id: UUID,
        iri: str,
    ) -> UUID:
        """Stable import identity for a named semantic resource."""
        return uuid5(ontology_id, iri)

    def to_graph(self, snapshot: dict) -> Graph:
        graph = Graph()

        namespace = Namespace(snapshot["namespace"])
        graph.bind("ex", namespace)
        graph.bind("owl", OWL)
        graph.bind("rdf", RDF)
        graph.bind("rdfs", RDFS)
        graph.bind("xsd", XSD)

        ontology_iri = snapshot.get("ontologyIri")
        if ontology_iri:
            graph.add((
                URIRef(ontology_iri),
                RDF.type,
                OWL.Ontology,
            ))

        for item in snapshot.get("classes", []):
            class_iri = URIRef(item["iri"])
            graph.add((class_iri, RDF.type, OWL.Class))

            for label in item.get("preferredLabels", []):
                graph.add((
                    class_iri,
                    RDFS.label,
                    Literal(
                        label["value"],
                        lang=label["language"],
                    ),
                ))

            if item.get("definition"):
                graph.add((
                    class_iri,
                    RDFS.comment,
                    Literal(item["definition"]),
                ))

            for parent_id in item.get("parentIris", []):
                graph.add((
                    class_iri,
                    RDFS.subClassOf,
                    URIRef(parent_id),
                ))

        for item in snapshot.get("datatypeProperties", []):
            prop = URIRef(item["iri"])

            graph.add((prop, RDF.type, OWL.DatatypeProperty))

            for domain_iri in item.get("domainIris", []):
                graph.add((
                    prop,
                    RDFS.domain,
                    URIRef(domain_iri),
                ))

            graph.add((
                prop,
                RDFS.range,
                URIRef(item["datatypeIri"]),
            ))

        for item in snapshot.get("objectProperties", []):
            prop = URIRef(item["iri"])

            graph.add((prop, RDF.type, OWL.ObjectProperty))

            for domain_iri in item.get("domainIris", []):
                graph.add((
                    prop,
                    RDFS.domain,
                    URIRef(domain_iri),
                ))

            for range_iri in item.get("rangeIris", []):
                graph.add((
                    prop,
                    RDFS.range,
                    URIRef(range_iri),
                ))

            if item.get("inverseIri"):
                graph.add((
                    prop,
                    OWL.inverseOf,
                    URIRef(item["inverseIri"]),
                ))

        # Relation is a P1 modeling projection over ObjectProperty.
        # Do not emit it as an instance assertion without actual individuals.
        return graph
