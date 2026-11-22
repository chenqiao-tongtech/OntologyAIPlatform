//
//  ShaclValidationResult.swift
//  
//
//  Created by joechen on 2026/11/21.
//



from dataclasses import dataclass

from rdflib import Graph
from pyshacl import validate


@dataclass(frozen=True)
class ShaclValidationResult:
    conforms: bool
    report_graph: Graph
    report_text: str


class ShaclValidator:
    def validate(
        self,
        data_graph: Graph,
        shapes_graph: Graph,
        ontology_graph: Graph | None = None,
    ) -> ShaclValidationResult:
        conforms, report_graph, report_text = validate(
            data_graph,
            shacl_graph=shapes_graph,
            ont_graph=ontology_graph,
            inference="none",
            abort_on_first=False,
            allow_infos=False,
            allow_warnings=False,
            meta_shacl=True,
            advanced=False,
            js=False,
        )

        return ShaclValidationResult(
            conforms=bool(conforms),
            report_graph=report_graph,
            report_text=str(report_text),
        )
