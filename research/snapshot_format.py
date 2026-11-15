"""Canonical DS-03 snapshot identity and integrity helpers."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def dataset_id_for_input_fingerprint(input_fingerprint: dict[str, Any]) -> str:
    return "imerg-2005-point-" + hashlib.sha256(canonical_json(input_fingerprint)).hexdigest()[:20]


def snapshot_sha256(snapshot: dict[str, Any]) -> str:
    content = {key: value for key, value in snapshot.items() if key != "snapshot_sha256"}
    return hashlib.sha256(canonical_json(content)).hexdigest()
