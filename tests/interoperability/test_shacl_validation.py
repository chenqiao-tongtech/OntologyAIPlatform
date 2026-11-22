#
//  test_shacl_validation.py
//  
//
//  Created by joechen on 2026/11/21.
//



from pathlib import Path

from rdflib import Graph, Namespace, RDF, Literal, XSD

from ontology.formats.validators.shacl_validator import ShaclValidator


SAMPLES = Path(__file__).resolve().parents[2] / "ontology" / "samples"


def load_graph(path: Path) -> Graph:
    graph = Graph()
    graph.parse(path, format="turtle")
    return graph


def test_customer_shapes_are_valid():
    shapes = load_graph(SAMPLES / "customer-shapes.ttl")

    # The Shapes Graph itself is checked with Meta-SHACL
    # during the validation call.
    empty_data = Graph()

    result = ShaclValidator().validate(
        empty_data,
        shapes,
    )

    assert result.conforms is True


def test_missing_customer_id_fails():
    shapes = load_graph(SAMPLES / "customer-shapes.ttl")

    data = Graph()
    ex = Namespace("https://example.com/ontology/customer#")

    customer = ex["customer-001"]

    data.add((customer, RDF.type, ex.Customer))
    data.add((customer, ex.hasOrder, ex["order-001"]))

    result = ShaclValidator().validate(data, shapes)

    assert result.conforms is False
    assert "customerId" in result.report_text or "MinCount" in result.report_text


def test_customer_with_required_id_passes():
    shapes = load_graph(SAMPLES / "customer-shapes.ttl")

    data = Graph()
    ex = Namespace("https://example.com/ontology/customer#")

    customer = ex["customer-001"]
    order = ex["order-001"]

    data.add((customer, RDF.type, ex.Customer))
    data.add((customer, ex.customerId, Literal("C10001", datatype=XSD.string)))
    data.add((customer, ex.hasOrder, order))
    data.add((order, RDF.type, ex.Order))

    result = ShaclValidator().validate(data, shapes)

    assert result.conforms is True
