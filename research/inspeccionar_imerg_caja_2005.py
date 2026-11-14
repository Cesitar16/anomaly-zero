"""Inspecciona la cobertura rectangular de 12 muestras IMERG de 2005."""

import argparse
import calendar
import json
from pathlib import Path

import h5py
import numpy as np
from comparar_imerg_estacion_2005 import HASHES, check_hash


def inspect(cache):
    rows = []
    for month, digest in enumerate(HASHES, 1):
        path = cache / f"imerg_2005{month:02d}_v07b_ncar.h5"
        check_hash(path, digest)
        with h5py.File(path, "r") as source:
            grid = source["Grid"]
            lon, lat = grid["lon"][:], grid["lat"][:]
            xs = np.flatnonzero((lon >= 138) & (lon <= 153))
            ys = np.flatnonzero((lat >= -38) & (lat <= -24))
            if (
                not len(xs)
                or not len(ys)
                or np.any(np.diff(xs) != 1)
                or np.any(np.diff(ys) != 1)
            ):
                raise ValueError(f"Coordenadas inesperadas: {path}")
            precip = grid["precipitation"]
            if precip.shape != (1, 3600, 1800) or precip.attrs["units"] != b"mm/hr":
                raise ValueError(f"Dimensiones o unidades inesperadas: {path}")
            values = precip[0, xs[0] : xs[-1] + 1, ys[0] : ys[-1] + 1]
            valid = np.isfinite(values) & (values != precip.attrs["_FillValue"])
            values_valid = values[valid]
            if not values_valid.size:
                raise ValueError(f"Sin valores válidos en caja: {path}")
            auxiliary = {}
            for name in (
                "randomError",
                "gaugeRelativeWeighting",
                "precipitationQualityIndex",
            ):
                field = grid[name]
                if field.shape != precip.shape:
                    raise ValueError(f"Dimensiones inesperadas para {name}: {path}")
                a = field[0, xs[0] : xs[-1] + 1, ys[0] : ys[-1] + 1]
                ok = np.isfinite(a) & (a != field.attrs["_FillValue"])
                if not np.any(ok):
                    raise ValueError(f"Sin valores para {name}: {path}")
                auxiliary[name] = {
                    "finite_non_fill": int(ok.sum()),
                    "min": float(a[ok].min()),
                    "max": float(a[ok].max()),
                }
            days = calendar.monthrange(2005, month)[1]
            rows.append(
                {
                    "mes": f"2005-{month:02d}",
                    "celdas_caja": int(values.size),
                    "celdas_validas": int(valid.sum()),
                    "celdas_negativas": int((values_valid < 0).sum()),
                    "campos_auxiliares": auxiliary,
                    "tasa_min_mm_h": float(values_valid.min()),
                    "tasa_max_mm_h": float(values_valid.max()),
                    "total_min_mm": float(values_valid.min()) * 24 * days,
                    "total_max_mm": float(values_valid.max()) * 24 * days,
                }
            )
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=Path("data/cache/ful-102"))
    args = parser.parse_args()
    print(json.dumps(inspect(args.cache), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
