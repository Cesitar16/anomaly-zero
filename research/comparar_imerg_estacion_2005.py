"""Reproduce la comparación exploratoria IMERG-estación para 2005, sin descargas."""

import argparse
import calendar
import hashlib
import json
from pathlib import Path

import h5py
import numpy as np

STATION = "ASN00072150"
STATION_HASH = "20715522da8333f1da5c0d715ca30f46341181dee1914d23480dd9f08c412761"
HASHES = (
    "bac3b9bc5ee8cc3eb1e5fe844778d54fd86e2b722813055b37f3872e6e4c73d5",
    "fe0aa14ac528459d485ca5a8685f2d4e4019992b976379ca2880a3422bc85e24",
    "ddc2aa593acf426ba0314a2deea1ab67292936deae7dbfa7a2450a528bc76e38",
    "7cc4510027369ac01919d8e3eb37dba1b38f5947e8d66fff37092ae4d78e415f",
    "18968b856e22a83a783807cdc7f6dcf55fed8399bc4ba7abfca0bcea583373fd",
    "f5bf5b041a941de0274e86851f3d3a32265c9dc314b8626e728ae1e4896ca92c",
    "6bdc0ab9dcc8844adcd997f3ad48b21491c2bc03f8aab30ef75167c68c877e0d",
    "02fb3b1fde299ec18d4855a7cbfa3a291bbf1536da508a158db04f7291b507e6",
    "a11525d4772209293adcff54209d0e83d405ce593e89a6767e567088673fc126",
    "2010f5adf42e99ceec0c968399360944e13ed2c06ba5e68f65984ed4b21c6529",
    "378adc0ff8210c10354f694301f2536444cea73ca557838240ebc71cdc93daf8",
    "6566b1594efc9163cc4952767df58d9396cd2db206c4baa1f6540b04077661c3",
)


def check_hash(path, expected):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != expected:
        raise ValueError(f"SHA-256 inesperado: {path}")


def compare(cache):
    station = cache / f"noaa_ghcnd_{STATION}.dly"
    check_hash(station, STATION_HASH)
    rows = station.read_text(encoding="ascii").splitlines()
    result = []
    for month, expected in enumerate(HASHES, 1):
        ym = f"2005{month:02d}"
        days = calendar.monthrange(2005, month)[1]
        lines = [
            s
            for s in rows
            if s[:11] == STATION and s[11:17] == ym and s[17:21] == "PRCP"
        ]
        if len(lines) != 1:
            raise ValueError(f"Registro diario ausente o duplicado: {ym}")
        line = lines[0]
        observations = [
            (int(line[21 + i * 8 : 26 + i * 8]), line[26 + i * 8 : 29 + i * 8])
            for i in range(days)
        ]
        if any(value == -9999 or flags != "  a" for value, flags in observations):
            raise ValueError(f"Faltantes o banderas inesperadas en {ym}")
        path = cache / f"imerg_{ym}_v07b_ncar.h5"
        check_hash(path, expected)
        with h5py.File(path, "r") as source:
            grid = source["Grid"]
            rain, lon, lat = grid["precipitation"], grid["lon"][:], grid["lat"][:]
            if rain.shape != (1, 3600, 1800) or rain.attrs["units"] != b"mm/hr":
                raise ValueError(f"Dimensiones o unidades inesperadas en {ym}")
            x, y = (
                int(np.argmin(abs(lon - 147.4573))),
                int(np.argmin(abs(lat + 35.1583))),
            )
            xb, yb = grid["lon_bnds"][x], grid["lat_bnds"][y]
            if not (xb[0] <= 147.4573 <= xb[1] and yb[0] <= -35.1583 <= yb[1]):
                raise ValueError(f"La celda no contiene la estación en {ym}")
            rate = float(rain[0, x, y])
            if not np.isfinite(rate) or rate == float(rain.attrs["_FillValue"]):
                raise ValueError(f"Precipitación faltante en {ym}")
        result.append(
            {
                "mes": ym,
                "estacion_mm": sum(v for v, _ in observations) / 10,
                "imerg_mm": rate * days * 24,
                "dias_estacion": days,
            }
        )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=Path("data/cache/ful-102"))
    args = parser.parse_args()
    print(json.dumps(compare(args.cache), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
