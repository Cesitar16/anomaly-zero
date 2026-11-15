"""Valida los ejemplos JSON citados en docs/fe-03-explorer-ux.md contra docs/openapi-contract-v0.yaml.

Uso (desde la raíz del repositorio):

    pip install pyyaml jsonschema
    python docs/fe-03/validar_ejemplos.py

Qué hace:
  * Toma los ejemplos OFICIALES del OpenAPI (los que trae el propio contrato) y comprueba que cumplan su esquema.
  * Construye los ejemplos DERIVADOS (los que el contrato no trae: 404, 500, regiones vacías, raster_layers...)
    a partir de los esquemas y los valida igual. Un ejemplo derivado NO es un ejemplo oficial.
  * Termina con código 1 si alguno no valida.

No inventa datos NASA: todo valor numérico proviene de un ejemplo oficial; los demás campos son estructurales.
"""

import copy
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

SPEC_PATH = Path(__file__).resolve().parent.parent / "openapi-contract-v0.yaml"
SPEC = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))
COMPONENTS = SPEC["components"]


def validar(instancia, nombre_esquema):
    esquema = {"$ref": f"#/components/schemas/{nombre_esquema}", "components": COMPONENTS}
    errores = sorted(Draft202012Validator(esquema).iter_errors(instancia), key=lambda e: list(e.path))
    return [f"{'/'.join(map(str, e.path))}: {e.message[:140]}" for e in errores]


series_ej = SPEC["paths"]["/series"]["get"]["responses"]["200"]["content"]["application/json"]["examples"]
resp = COMPONENTS["responses"]

OFICIALES = {
    "series_pointSample": (series_ej["pointSample"]["value"], "SeriesResponse"),
    "series_noData": (series_ej["noData"]["value"], "SeriesResponse"),
    "error_422_invalidParameters": (resp["InvalidRequest"]["content"]["application/json"]["examples"]["invalidParameters"]["value"], "ErrorResponse"),
    "error_503_snapshotUnavailable": (resp["ServiceUnavailable"]["content"]["application/json"]["examples"]["snapshotUnavailable"]["value"], "ErrorResponse"),
    "error_409_methodUnavailable": (resp["AnalysisUnavailable"]["content"]["application/json"]["examples"]["methodUnavailable"]["value"], "ErrorResponse"),
    "analysis_202_pending": (resp["AnalysisPending"]["content"]["application/json"]["examples"]["pendingAnalysis"]["value"], "AnalysisResponse"),
}

ENV = {"contract_version": "0.1-draft", "synthetic": True, "generated_at": "2026-01-01T00:00:00Z"}
punto = copy.deepcopy(OFICIALES["series_pointSample"][0])


def error(code, mensaje, request_id):
    return {**ENV, "error": {"code": code, "message": mensaje, "retryable": False, "request_id": request_id, "details": None}}


def capas(estados):
    return [
        {
            "dataset_id": "ds-synthetic-001", "date": mes, "layer_type": "value", "unit": "mm/hr", "state": estado,
            "format": "image/png" if estado == "available" else None,
            "tile_template": f"https://tiles.example.invalid/{mes}/{{z}}/{{x}}/{{y}}.png" if estado == "available" else None,
        }
        for mes, estado in estados
    ]


DERIVADOS = {
    "regions_vacio": ({**ENV, "regions": []}, "RegionsResponse"),
    "regions_una": ({**ENV, "regions": [punto["region"]]}, "RegionsResponse"),
    "products_uno": ({**ENV, "region_id": punto["region"]["region_id"], "products": [punto["product"]]}, "ProductsResponse"),
    "error_404_RESOURCE_NOT_FOUND": (error("RESOURCE_NOT_FOUND", "La región solicitada no existe.", "req-synthetic-notfound-001"), "ErrorResponse"),
    "error_500_INTERNAL_ERROR": (error("INTERNAL_ERROR", "Error interno inesperado.", "req-synthetic-internal-001"), "ErrorResponse"),
    "series_raster_todo_unavailable": ({**punto, "raster_layers": capas([("2005-01", "unavailable"), ("2005-02", "unavailable"), ("2005-03", "unavailable")])}, "SeriesResponse"),
    "series_raster_mixto": ({**punto, "raster_layers": capas([("2005-01", "available"), ("2005-02", "unavailable"), ("2005-03", "available")])}, "SeriesResponse"),
}

if __name__ == "__main__":
    fallos = 0
    for grupo, titulo in ((OFICIALES, "oficial"), (DERIVADOS, "derivado")):
        for clave, (instancia, esquema) in grupo.items():
            errores = validar(instancia, esquema)
            print(f"{titulo:9} {clave:34} {esquema:18} {'OK' if not errores else 'ERRORES'}")
            for linea in errores[:5]:
                print("    ", linea)
            fallos += bool(errores)
    print("ejemplos con errores:", fallos)
    sys.exit(1 if fallos else 0)
