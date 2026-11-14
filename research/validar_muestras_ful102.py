"""Comprueba muestras locales de FUL-102; no descarga datos ni modifica archivos."""

import argparse
import hashlib
import json
from pathlib import Path

import h5py
import numpy as np

SAMPLES = {
    "imerg_200501_v07b_ncar.h5": "bac3b9bc5ee8cc3eb1e5fe844778d54fd86e2b722813055b37f3872e6e4c73d5",
    "imerg_201001_v07b_ncar.h5": "59d477ca483062e697e5d6e2c4a4947399ef3a1c008df16ed5494a52fb03007b",
    "merra2_t2m_2005_ncar.nc4": "8359bed3bc8bd11f95dda6bb1a57e82b1acfc40262affa99edeb4832174e1073",
}


def verify_file(path, expected):
    digest = hashlib.sha256()
    with path.open("rb") as sample:
        for chunk in iter(lambda: sample.read(1024 * 1024), b""):
            digest.update(chunk)
    actual = digest.hexdigest()
    if actual != expected:
        raise ValueError(f"SHA-256 inesperado para {path}: {actual}")
    return actual


def text_attr(value):
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return str(value)


def inspect_imerg(path):
    with h5py.File(path, "r") as source:
        grid = source["Grid"]
        rain, lon, lat = grid["precipitation"], grid["lon"][:], grid["lat"][:]
        units = text_attr(rain.attrs["units"])
        if rain.shape != (1, 3600, 1800) or units != "mm/hr":
            raise ValueError(
                f"Dimensiones o unidades IMERG inesperadas: {rain.shape}, {units}"
            )
        x, y = int(np.argmin(abs(lon - 147.4575))), int(np.argmin(abs(lat + 35.1583)))
        lon_bounds, lat_bounds = grid["lon_bnds"][x], grid["lat_bnds"][y]
        if not (
            lon_bounds[0] <= 147.4575 <= lon_bounds[1]
            and lat_bounds[0] <= -35.1583 <= lat_bounds[1]
        ):
            raise ValueError(f"La celda más cercana no contiene la estación en {path}")
        value = float(rain[0, x, y])
        if not np.isfinite(value) or value == float(rain.attrs["_FillValue"]):
            raise ValueError(f"Precipitación faltante en {path}")
        return {
            "shape_time_lon_lat": rain.shape,
            "units": units,
            "cell_center_lon_lat": [float(lon[x]), float(lat[y])],
            "cell_rate_mm_per_hour": value,
            "january_total_mm_estimate": value * 744,
            "note": "Celda que contiene la estación Wagga Wagga AMO; no es una observación puntual.",
        }


def inspect_merra(path):
    with h5py.File(path, "r") as source:
        temp, lon, lat = source["T2M"], source["lon"][:], source["lat"][:]
        units = text_attr(temp.attrs["units"])
        if temp.shape != (12, 361, 576) or units != "K":
            raise ValueError(
                f"Dimensiones o unidades MERRA inesperadas: {temp.shape}, {units}"
            )
        x, y = int(np.argmin(abs(lon - 147.5))), int(np.argmin(abs(lat + 35.0)))
        value = float(temp[0, y, x])
        fill = float(np.asarray(temp.attrs["_FillValue"]).item())
        if not np.isfinite(value) or value == fill:
            raise ValueError(f"Temperatura faltante en {path}")
        time = source["time"]
        if (
            text_attr(time.attrs["units"]) != "days since 2005-01-01T00:30:00"
            or text_attr(time.attrs["calendar"]) != "standard"
        ):
            raise ValueError(f"Eje temporal inesperado en {path}")
        if not np.array_equal(
            time[:], [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
        ):
            raise ValueError(f"Meses inesperados en {path}")
        xs = np.flatnonzero((lon >= 138) & (lon <= 153))
        ys = np.flatnonzero((lat >= -38) & (lat <= -24))
        if (
            not len(xs)
            or not len(ys)
            or np.any(np.diff(xs) != 1)
            or np.any(np.diff(ys) != 1)
        ):
            raise ValueError(f"Coordenadas de caja inesperadas en {path}")
        box = temp[:, ys[0] : ys[-1] + 1, xs[0] : xs[-1] + 1]
        months = []
        for month, values in enumerate(box, 1):
            valid = np.isfinite(values) & (values != fill)
            if not np.any(valid):
                raise ValueError(f"Sin valores distintos del fill para mes {month}")
            months.append(
                {
                    "month": month,
                    "cells": int(values.size),
                    "finite_non_fill": int(valid.sum()),
                    "min_celsius": float(values[valid].min()) - 273.15,
                    "max_celsius": float(values[valid].max()) - 273.15,
                }
            )
        return {
            "shape_time_lat_lon": temp.shape,
            "units": units,
            "box_months": months,
            "cell_center_lon_lat": [float(lon[x]), float(lat[y])],
            "january_2005_kelvin": value,
            "january_2005_celsius": value - 273.15,
            "note": "Copia reorganizada por NCAR; no es el gránulo original NASA.",
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=Path("data/cache/ful-102"))
    args = parser.parse_args()
    results = {}
    for name, digest in SAMPLES.items():
        path = args.cache / name
        actual = verify_file(path, digest)
        details = (
            inspect_imerg(path) if name.startswith("imerg_") else inspect_merra(path)
        )
        results[name] = {"sha256": actual, **details}
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
