from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from backend.app.data_sources import earthdata_spatial

_ASSET_RE = re.compile(
    r"^3B-MO\.MS\.MRG\.3IMERG\.(?P<year>\d{4})(?P<month>\d{2})01-"
    r"S000000-E235959\.(?P<suffix_month>\d{2})\.V(?P<version>\d{2}[A-Z])\.HDF5$"
)
_PRODUCT = {
    "key": "imerg_final",
    "short_name": "GPM_3IMERGM",
    "version": "07",
    "variable": "precipitation",
}


@dataclass(frozen=True)
class MonthlyAsset:
    period: str
    path: Path
    manifest_path: Path
    sha256: str
    manifest: dict


@dataclass(frozen=True)
class CenterMask:
    values: np.ndarray
    geometry_sha256: str
    coordinates_sha256: str
    cache_hit: bool


def sha256_file(path: Path | str) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _identity(manifest: dict) -> tuple:
    product = manifest.get("product", {})
    return tuple(product.get(key) for key in ("key", "short_name", "version", "variable"))


def select_imerg_2005(
    candidate_paths: Iterable[Path | str], *, require_complete: bool = True
) -> list[MonthlyAsset]:
    """Validate and order recognized IMERG Final V07B monthly files for 2005."""
    assets: dict[str, MonthlyAsset] = {}
    for candidate in candidate_paths:
        path = Path(candidate)
        match = _ASSET_RE.fullmatch(path.name)
        if match is None:
            raise ValueError(f"Nombre IMERG mensual o versión V07B inesperados: {path.name}")
        year, month, suffix_month, file_version = match.groups()
        if year != "2005":
            raise ValueError(f"Archivo fuera del año 2005: {path.name}")
        if month not in {f"{value:02d}" for value in range(1, 13)}:
            raise ValueError(f"Mes inválido en nombre de archivo: {path.name}")
        if suffix_month != month:
            raise ValueError(f"Mes del nombre y sufijo no coinciden: {path.name}")
        if file_version != "07B":
            raise ValueError(f"Versión de archivo distinta de V07B: {path.name}")
        period = f"{year}-{month}"
        if period in assets:
            raise ValueError(f"Granules duplicados para {period}: {assets[period].path.name}, {path.name}")

        manifest_path = Path(f"{path}.manifest.json")
        if not path.is_file():
            raise FileNotFoundError(f"No existe el granule: {path}")
        if not manifest_path.is_file():
            raise FileNotFoundError(f"Falta manifiesto de {period}: {manifest_path}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if _identity(manifest) != tuple(_PRODUCT[key] for key in ("key", "short_name", "version", "variable")):
            raise ValueError(f"Identidad/version/variable de manifiesto inesperada para {period}: {path.name}")
        if manifest.get("period", {}).get("month") != period:
            raise ValueError(
                f"Periodo del nombre ({period}) y del manifiesto "
                f"({manifest.get('period', {}).get('month')}) no coinciden: {path.name}"
            )
        digest = sha256_file(path)
        if manifest.get("bytes") != path.stat().st_size or manifest.get("sha256") != digest:
            raise ValueError(f"Tamaño/SHA-256 no coincide con manifiesto: {path.name}")
        assets[period] = MonthlyAsset(period, path, manifest_path, digest, manifest)

    if require_complete:
        expected = [f"2005-{month:02d}" for month in range(1, 13)]
        missing = [period for period in expected if period not in assets]
        if missing:
            raise FileNotFoundError(
                "Faltan granules IMERG Final 2005: " + ", ".join(missing)
                + ". No se descargaron automáticamente. Revisa README.md de la Release "
                "be02-samples-2005-v1 y vuelve a extraer sus ZIP en el data_root común."
            )
    return [assets[key] for key in sorted(assets)]


def discover_imerg_2005(directory: Path | str, *, require_complete: bool = True) -> list[MonthlyAsset]:
    """Discover only product-shaped files, then validate identity and coverage."""
    root = Path(directory)
    if not root.is_dir():
        raise FileNotFoundError(f"No existe el directorio IMERG: {root}")
    candidates = sorted(root.glob("3B-MO.MS.MRG.3IMERG.*.HDF5"))
    return select_imerg_2005(candidates, require_complete=require_complete)


def _coordinate_digest(latitudes: np.ndarray, longitudes: np.ndarray) -> str:
    digest = hashlib.sha256()
    for values in (latitudes, longitudes):
        normalized = np.ascontiguousarray(values, dtype=np.float64)
        digest.update(str(normalized.shape).encode("ascii"))
        digest.update(normalized.tobytes())
    return digest.hexdigest()


class CenterMaskCache:
    """Cache exact native-grid center selection by geometry and coordinates."""

    def __init__(self) -> None:
        self._key: tuple[str, str] | None = None
        self._values: np.ndarray | None = None
        self.build_count = 0

    def get(
        self, latitudes: np.ndarray, longitudes: np.ndarray, polygon_path: Path | str
    ) -> CenterMask:
        latitudes = np.asarray(latitudes, dtype=np.float64).reshape(-1)
        longitudes = np.asarray(longitudes, dtype=np.float64).reshape(-1)
        if not latitudes.size or not longitudes.size:
            raise ValueError("Las coordenadas de la grilla no pueden estar vacías")
        if not np.isfinite(latitudes).all() or not np.isfinite(longitudes).all():
            raise ValueError("Las coordenadas de la grilla deben ser finitas")
        geometry_path = Path(polygon_path)
        geometry_digest = sha256_file(geometry_path)
        coordinate_digest = _coordinate_digest(latitudes, longitudes)
        key = (geometry_digest, coordinate_digest)
        if key == self._key and self._values is not None:
            return CenterMask(self._values, geometry_digest, coordinate_digest, True)

        geometry = json.loads(geometry_path.read_text(encoding="utf-8"))
        crs_name = (geometry.get("crs") or {}).get("properties", {}).get("name")
        if crs_name is not None and crs_name.upper() not in {"EPSG:4326", "CRS84", "OGC:CRS84"}:
            raise ValueError("El CRS del polígono debe ser compatible con latitud/longitud")
        polygons = list(earthdata_spatial._geometries(geometry))
        if not polygons or any(not exterior for exterior, _ in polygons):
            raise ValueError("El GeoJSON no contiene anillos Polygon válidos")
        exterior_points = [point for exterior, _ in polygons for point in exterior]
        west = min(point[0] for point in exterior_points)
        east = max(point[0] for point in exterior_points)
        south = min(point[1] for point in exterior_points)
        north = max(point[1] for point in exterior_points)
        lat_indexes = np.flatnonzero((latitudes >= south) & (latitudes <= north))
        lon_indexes = np.flatnonzero((longitudes >= west) & (longitudes <= east))
        values = np.zeros((latitudes.size, longitudes.size), dtype=bool)
        for iy in lat_indexes:
            for ix in lon_indexes:
                values[iy, ix] = earthdata_spatial._inside(
                    float(longitudes[ix]), float(latitudes[iy]), polygons
                )
        values.setflags(write=False)
        self._key = key
        self._values = values
        self.build_count += 1
        return CenterMask(values, geometry_digest, coordinate_digest, False)


def valid_data_mask(values: np.ndarray, sentinels: Iterable[float | None]) -> np.ndarray:
    """Match FUL-106's finite/non-fill rule; numeric zero remains valid."""
    values = np.asarray(values)
    valid = np.isfinite(values)
    for sentinel in sentinels:
        if sentinel is not None:
            valid &= ~np.isclose(values, float(sentinel), rtol=1e-6, atol=1e-8)
    return valid
