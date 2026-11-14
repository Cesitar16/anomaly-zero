"""Audita localmente respuestas CMR reconstruidas de Work, sin red ni descargas."""

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROWS = (2, 3, 4, 5, 6, 13, 14, 15, 16, 17, 18, 19, 20, 22, 23, 24, 25, 26)
COLLECTIONS = {
    2: ("GLDAS_NOAH025_M", "2.1"),
    3: ("GPM_3IMERGM", "07"),
    4: ("M2TMNXSLV", "5.12.4"),
    5: ("SPL3SMP", "009"),
    6: ("SPL4SMGP", "008"),
}


def audit(cache, manifest):
    with manifest.open(encoding="utf-8", newline="") as source:
        records = {int(row["fila"]): row for row in csv.DictReader(source)}
    results = {}
    for number in ROWS:
        row = records[number]
        body = (cache / f"work_reconstructed_row_{number}.json").read_bytes()
        if (
            len(body) != int(row["bytes_work"])
            or hashlib.sha256(body).hexdigest() != row["sha256_work"]
        ):
            raise ValueError(f"Tamaño o hash no coincide para fila {number}")
        entries = json.loads(body)["feed"].get("entry", [])
        result = {"id": row["id"], "registros": len(entries), "sha256_verificado": True}
        if number in COLLECTIONS:
            if (
                len(entries) != 1
                or (entries[0]["short_name"], entries[0]["version_id"])
                != COLLECTIONS[number]
            ):
                raise ValueError(f"Identidad de colección inesperada: fila {number}")
            result["coleccion"] = entries[0]["short_name"]
            result["version"] = entries[0]["version_id"]
        elif number in (15, 18):
            months = Counter(item["time_start"][:7] for item in entries)
            expected = {
                f"{year}-{month:02}"
                for year in range(2005, 2026)
                for month in range(1, 13)
            }
            result["meses_faltantes_2005_2025"] = sorted(expected - months.keys())
            result["meses_duplicados"] = sorted(
                month for month, count in months.items() if count > 1
            )
            result["meses_distintos"] = len(months)
        elif entries:
            result["primer_inicio"] = entries[0].get("time_start")
            result["primer_titulo"] = entries[0].get("title")
        results[str(number)] = result
    return results


def audit_all(cache, manifest):
    with manifest.open(encoding="utf-8", newline="") as source:
        records = list(csv.DictReader(source))
    checked = []
    for row in records:
        if row["estado"] != "MISMO_SHA256":
            continue
        name = Path(row["archivo_local_ignorado"]).name
        if not name:
            raise ValueError(f"Ruta ausente para fila {row['fila']}")
        path = cache / name
        if path.stat().st_size != int(row["bytes_work"]):
            raise ValueError(f"Tamaño no coincide para fila {row['fila']}")
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if digest != row["sha256_work"]:
            raise ValueError(f"Hash no coincide para fila {row['fila']}")
        checked.append({"fila": row["fila"], "id": row["id"], "archivo": str(path)})
    return checked


def audit_merra_repeat(cache, manifest):
    with manifest.open(encoding="utf-8", newline="") as source:
        row = next(r for r in csv.DictReader(source) if r["fila"] == "21")
    body = (cache / "merra_cmr_2005_2025.json").read_bytes()
    digest = hashlib.sha256(body).hexdigest()
    expected_digest = "d913e89dfb40bf5d9c2107cd647e7d99c1fa94f3f62cd46e5343d2ce1d5e1429"
    if digest != expected_digest or digest == row["sha256_work"]:
        raise ValueError(
            "La consulta repetida MERRA-2 no coincide con la copia documentada"
        )
    entries = json.loads(body)["feed"]["entry"]
    months = Counter(e["time_start"][:7] for e in entries)
    expected = {
        f"{year}-{month:02}" for year in range(2005, 2026) for month in range(1, 13)
    }
    return {
        "origen": "consulta repetida; no es el cuerpo original de Work",
        "sha256": digest,
        "registros": len(entries),
        "meses_distintos": len(months),
        "meses_faltantes": sorted(expected - months.keys()),
        "meses_inesperados": sorted(months.keys() - expected),
        "meses_duplicados": sorted(k for k, count in months.items() if count > 1),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=Path("data/cache/ful-102"))
    parser.add_argument("--manifest", type=Path, default=Path("docs/pruebas_work.csv"))
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--todas",
        action="store_true",
        help="Verifica las copias del manifiesto con hash coincidente",
    )
    group.add_argument(
        "--merra-repetida",
        action="store_true",
        help="Examina la consulta repetida MERRA-2 sin confundirla con Work",
    )
    args = parser.parse_args()
    if args.todas:
        result = audit_all(args.cache, args.manifest)
    elif args.merra_repetida:
        result = audit_merra_repeat(args.cache, args.manifest)
    else:
        result = audit(args.cache, args.manifest)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
