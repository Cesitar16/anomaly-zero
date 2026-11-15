"""Offline structural and scientific-semantic checks for AZ-04 examples."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

ROOT = Path(__file__).resolve().parents[1]
OPENAPI_PATH = ROOT / "docs/openapi-contract-v0.yaml"
CONTRACT_VERSION = "0.1-draft"
EXPECTED_PRODUCTS = {
    "MERRA-2": ("T2M", "K"),
    "GPM_3IMERGM": ("precipitation", "mm/hr"),
    "GLDAS_NOAH025_M": ("SoilMoi0_10cm_inst", "kg m-2"),
}


def load_spec(path: Path = OPENAPI_PATH) -> dict[str, Any]:
    spec = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(spec, dict) or spec.get("openapi") != "3.1.0":
        raise ValueError("Se esperaba OpenAPI 3.1.0")
    return spec


def _resolve_pointer(spec: dict[str, Any], ref: str) -> Any:
    if not ref.startswith("#/"):
        raise ValueError(f"Referencia externa no permitida por la prueba offline: {ref}")
    current: Any = spec
    for part in ref[2:].split("/"):
        token = part.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, dict) or token not in current:
            raise ValueError(f"Referencia OpenAPI sin destino: {ref}")
        current = current[token]
    return current


def assert_local_references_resolve(spec: dict[str, Any]) -> int:
    count = 0

    def visit(node: Any) -> None:
        nonlocal count
        if isinstance(node, dict):
            if "$ref" in node:
                _resolve_pointer(spec, node["$ref"])
                count += 1
            for child in node.values():
                visit(child)
        elif isinstance(node, list):
            for child in node:
                visit(child)

    visit(spec)
    return count


def _schema_registry(spec: dict[str, Any]) -> Registry:
    schema = Resource.from_contents(spec, default_specification=DRAFT202012)
    return Registry().with_resource("https://anomaly-zero.invalid/openapi.yaml", schema)


def validate_schema(schema: dict[str, Any], value: Any, spec: dict[str, Any]) -> list[str]:
    candidate = {
        "$id": "https://anomaly-zero.invalid/openapi.yaml",
        "allOf": [schema],
        "components": spec.get("components", {}),
    }
    validator = Draft202012Validator(
        candidate,
        registry=_schema_registry(spec),
    )
    return [error.message for error in validator.iter_errors(value)]


def assert_scientific_semantics(payload: dict[str, Any], *, production: bool = False) -> None:
    if payload.get("contract_version") != CONTRACT_VERSION:
        raise ValueError("contract_version incompatible con AZ-04")
    if not isinstance(payload.get("synthetic"), bool):
        raise TypeError("Todo fixture/payload debe declarar synthetic como boolean")
    if production and payload["synthetic"]:
        raise ValueError("Un fixture sintético no puede usarse como observación real")
    generated_at = payload.get("generated_at")
    if generated_at is not None and not re.fullmatch(r"\d{4}-\d{2}-\d{2}T.+(?:Z|\+00:00)", generated_at):
        raise ValueError("generated_at debe ser una fecha UTC explícita")

    product = payload.get("product")
    if isinstance(product, dict):
        short_name = product.get("short_name")
        expected = EXPECTED_PRODUCTS.get(short_name)
        if expected:
            variable, unit = expected
            if product.get("variable") != variable or product.get("unit") != unit:
                raise ValueError(f"Variable/unidad incoherentes para {short_name}")
        if short_name == "GPM_3IMERGM" and product.get("quantity") == "monthly_accumulation":
            raise ValueError("IMERG mm/hr no puede etiquetarse como acumulado mensual")
        transforms = payload.get("transformations", [])
        if isinstance(transforms, list) and transforms:
            for item in transforms:
                if not all(item.get(key) for key in ("operation", "input_unit", "output_unit", "code_version")):
                    raise ValueError("Cada conversión necesita operación, unidades y versión de código")

    quality = payload.get("quality")
    if isinstance(quality, dict):
        checks = quality.get("qa_checks", [])
        demonstrated = any(
            check.get("applied") is True and check.get("state") in {"passed", "partial"}
            for check in checks
        )
        if quality.get("verification_state") == "provider_qa_applied" and not demonstrated:
            raise ValueError("provider_qa_applied requiere controles aplicados y evidenciados")
        if quality.get("provider_flags_applied") is True and not demonstrated:
            raise ValueError("provider_flags_applied requiere controles QA demostrables")

    data_state = payload.get("data_state")
    series = payload.get("series")
    if isinstance(series, list):
        dates: list[str] = []
        for point in series:
            date = point.get("date")
            if not isinstance(date, str) or not re.fullmatch(r"\d{4}-\d{2}-01", date):
                raise ValueError("Las series mensuales deben etiquetarse con el primer día del mes")
            dates.append(date)
            value = point.get("value")
            quality_point = point.get("quality", {})
            if value is None:
                if not quality_point.get("missing_reason"):
                    raise ValueError("value=null requiere missing_reason")
            elif isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError("value debe ser número finito o null")
            elif not math.isfinite(value):
                raise ValueError("NaN/Infinity no se pueden publicar como JSON")
            elif quality_point.get("missing_reason") is not None:
                raise ValueError("Un valor presente no debe tener missing_reason")
        if dates != sorted(dates) or len(dates) != len(set(dates)):
            raise ValueError("Fechas mensuales duplicadas o fuera de orden")
        if data_state == "no_data" and series:
            raise ValueError("no_data debe tener una serie vacía")
        if data_state == "available" and any(point.get("value") is None for point in series):
            raise ValueError("available no puede ocultar faltantes dentro de la serie")

    support = payload.get("spatial_aggregation")
    if isinstance(support, dict):
        kind = support.get("support_type")
        if kind == "regional_aggregate":
            if support.get("approval_state") != "approved" or not support.get("approval_reference"):
                raise ValueError("regional_aggregate requiere aprobación y referencia verificable")
            coverage = payload.get("coverage", {}).get("spatial_coverage")
            if isinstance(coverage, dict):
                basin_fraction = coverage.get("valid_area_fraction_of_basin")
                if basin_fraction is not None and basin_fraction > 1:
                    raise ValueError("Cobertura A_valid/A_basin > 1 bloquea agregación regional")

    analysis_id = payload.get("analysis_id")
    if analysis_id is not None and production:
        if payload.get("status") == "complete":
            raise ValueError("Gate T/motor no aprobado: no afirmar análisis real complete")
        metrics = payload.get("metrics", {})
        if payload.get("status") == "pending" and any(value is not None for value in metrics.values()):
            raise ValueError("Análisis pending no debe presentar métricas calculadas")


def iter_openapi_examples(spec: dict[str, Any]):
    def resolve_response(response: dict[str, Any]) -> dict[str, Any]:
        while "$ref" in response:
            response = _resolve_pointer(spec, response["$ref"])
        return response

    for path, path_item in spec.get("paths", {}).items():
        for method, operation in path_item.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                continue
            for status, raw_response in operation.get("responses", {}).items():
                response = resolve_response(raw_response)
                for media_type, media in (response.get("content") or {}).items():
                    for name, example in (media.get("examples") or {}).items():
                        if "value" in example:
                            yield path, method.upper(), status, media_type, name, media["schema"], example["value"]


def markdown_json_examples(path: Path) -> list[dict[str, Any]]:
    content = path.read_text(encoding="utf-8")
    return [json.loads(block) for block in re.findall(r"```json\s*\n(.*?)\n```", content, re.DOTALL)]
