"""Valida los ejemplos JSON citados en docs/fe-03-explorer-ux.md contra docs/openapi-contract-v0.yaml.

Uso (desde la raiz del repositorio):

    pip install pyyaml jsonschema
    python docs/fe-03/validar_ejemplos.py [ruta/al/openapi.yaml]

Tres grupos de ejemplos:

  * OFICIAL: los que trae el propio OpenAPI.
  * OBSERVADO: respuestas reales del backend de `dev` (BE-03 y BE-04), capturadas el 2026-11-15 sobre el commit
    884c34f con `TestClient` y sin snapshot configurado (ver docs/fe-03/ejemplos-observados/). Son capturas de una
    implementacion, no son el contrato. `ruta_inexistente_dev.json` es el cuerpo que FastAPI devuelve para una ruta
    que no existe (por ejemplo /analyses): NO es un sobre de error del contrato y se comprueba que no lo sea.
  * DERIVADO: los que el contrato no trae y el backend actual no produce (regiones vacias, raster_layers). Se
    construyen a partir de los esquemas. Un ejemplo derivado NO es un ejemplo oficial ni una respuesta real.

Termina con codigo 1 si algun ejemplo no valida. Los AVISO no cambian el codigo de salida: senalan que el backend
dejo de comportarse como describe el documento (por ejemplo, si empieza a enviar `details` o `raster_layers`).

No inventa datos NASA: todo valor numerico proviene de un ejemplo oficial; los demas campos son estructurales.
"""

import copy
import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

AQUI = Path(__file__).resolve().parent
SPEC_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else AQUI.parent / "openapi-contract-v0.yaml"
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

# Respuestas reales del backend de dev: archivo -> esquema del OpenAPI.
ARCHIVOS_OBSERVADOS = {
    "regions_dev.json": "RegionsResponse",
    "products_dev_sin_snapshot.json": "ProductsResponse",
    "series_no_data_dev.json": "SeriesResponse",
    "error_404_region_dev.json": "ErrorResponse",
    "error_404_producto_dev.json": "ErrorResponse",
    "error_422_parametro_dev.json": "ErrorResponse",
    "error_422_limit_exceeded_dev.json": "ErrorResponse",
    "error_422_periodo_fuera_de_cobertura_dev.json": "ErrorResponse",
    "error_500_dev.json": "ErrorResponse",
    "error_503_dev.json": "ErrorResponse",
}
OBSERVADOS = {
    nombre[: -len(".json")]: (json.loads((AQUI / "ejemplos-observados" / nombre).read_text(encoding="utf-8")), esquema)
    for nombre, esquema in ARCHIVOS_OBSERVADOS.items()
}
RUTA_INEXISTENTE = json.loads((AQUI / "ejemplos-observados" / "ruta_inexistente_dev.json").read_text(encoding="utf-8"))

ENV = {"contract_version": "0.1-draft", "synthetic": True, "generated_at": "2026-01-01T00:00:00Z"}
punto = copy.deepcopy(OFICIALES["series_pointSample"][0])


def capas(estados):
    return [
        {
            "dataset_id": "ds-synthetic-001", "date": mes, "layer_type": "value", "unit": "mm/hr", "state": estado,
            "format": "image/png" if estado == "available" else None,
            "tile_template": f"https://tiles.example.invalid/{mes}/{{z}}/{{x}}/{{y}}.png" if estado == "available" else None,
        }
        for mes, estado in estados
    ]


# No los produce el backend actual: hoy publica una region y no incluye `raster_layers` en ninguna respuesta.
DERIVADOS = {
    "regions_vacio": ({**ENV, "regions": []}, "RegionsResponse"),
    "series_raster_todo_unavailable": ({**punto, "raster_layers": capas([("2005-01", "unavailable"), ("2005-02", "unavailable"), ("2005-03", "unavailable")])}, "SeriesResponse"),
    "series_raster_mixto": ({**punto, "raster_layers": capas([("2005-01", "available"), ("2005-02", "unavailable"), ("2005-03", "available")])}, "SeriesResponse"),
}


def avisos():
    """Comprueba que el backend siga comportandose como describe docs/fe-03-explorer-ux.md (sec. 4.1 y 11)."""
    salida = []
    if len(OBSERVADOS["regions_dev"][0]["regions"]) != 1:
        salida.append("el backend ya no publica exactamente una region (E1 deja de ser un caso defensivo)")
    for clave, (instancia, _) in OBSERVADOS.items():
        if "raster_layers" in instancia:
            salida.append(f"{clave}: el backend ya envia raster_layers")
        if "error" in instancia and instancia["error"]["details"] is not None:
            salida.append(f"{clave}: el backend ya envia error.details (hoy siempre null)")
    if "error" in RUTA_INEXISTENTE:
        salida.append("ruta_inexistente_dev: el backend ya responde con el sobre de error en rutas inexistentes")
    return salida


if __name__ == "__main__":
    fallos = 0
    for grupo, titulo in ((OFICIALES, "oficial"), (OBSERVADOS, "observado"), (DERIVADOS, "derivado")):
        for clave, (instancia, esquema) in grupo.items():
            errores = validar(instancia, esquema)
            print(f"{titulo:9} {clave:46} {esquema:18} {'OK' if not errores else 'ERRORES'}")
            for linea in errores[:5]:
                print("    ", linea)
            fallos += bool(errores)
    # El cuerpo de una ruta inexistente debe NO ser un ErrorResponse.
    no_es_sobre = bool(validar(RUTA_INEXISTENTE, "ErrorResponse"))
    print(f"{'observado':9} {'ruta_inexistente_dev':46} {'(sin sobre)':18} {'OK' if no_es_sobre else 'ERRORES'}")
    fallos += not no_es_sobre
    for linea in avisos():
        print("AVISO:", linea)
    print("ejemplos con errores:", fallos)
    sys.exit(1 if fallos else 0)
