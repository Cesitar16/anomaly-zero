"""Genera un snapshot IMERG SINTETICO para probar `/explore` contra FastAPI sin datos NASA.

Reutiliza el generador de DS-03 (`research.build_ful116_snapshot`) y los granulos de prueba de
`research/tests/test_ful116_snapshot.py`: 12 meses de 2005 con un cero valido (enero) y meses faltantes
(febrero y marzo). Los valores son ficticios; el backend responde con `synthetic: true`.

Uso (desde la raiz del repositorio):

    uv run --group dev python scripts/make_synthetic_imerg_snapshot.py data/processed/ful116-sintetico

Luego, en el proceso del backend:

    ANOMALY_ZERO_IMERG_SNAPSHOT=data/processed/ful116-sintetico/processed/imerg_2005_point_snapshot.json \
        uv run uvicorn backend.app.main:app --port 8000

No se versiona nada: `data/processed/` esta ignorado por Git y no se mezcla con el snapshot real.
"""

import sys
from pathlib import Path

import pytest

# `python scripts/...` pone `scripts/` en el path, no la raiz del repositorio.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research import build_ful116_snapshot as builder
from research.tests.test_ful116_snapshot import _write_granules


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    out = Path(argv[1])
    patch = pytest.MonkeyPatch()
    try:
        inputs, point = _write_granules(out / "inputs", patch, include_missing=True)
        snapshot = out / "processed" / "imerg_2005_point_snapshot.json"
        builder.build_snapshot(inputs, point, snapshot.parent)
    finally:
        patch.undo()
    print(snapshot)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
