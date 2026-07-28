from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

from audit_neutral_gdelt_gkg_source import audit_gkg_sample


def _row(record_id: str, *, side: str) -> str:
    values = [""] * 27
    values[0] = record_id
    values[1] = "20260728183000"
    values[3] = "example.test"
    values[4] = f"https://example.test/{record_id}"
    values[8] = "ECON_CENTRALBANK,1;EPU_CATS_MONETARY_POLICY,1"
    values[13] = (
        "European Central Bank" if side == "ECB" else "Federal Reserve"
    )
    values[15] = "1.5,2.0,0.5"
    return "\t".join(values)


def test_source_audit_checks_hash_schema_and_strict_sides(
    tmp_path: Path,
) -> None:
    path = tmp_path / "20260728183000.gkg.csv.zip"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "20260728183000.gkg.csv",
            _row("one", side="ECB") + "\n" + _row("two", side="FED") + "\n",
        )
    payload = path.read_bytes()
    result = audit_gkg_sample(
        path,
        expected_md5=hashlib.md5(payload).hexdigest(),
        observed_at_utc="2026-07-28T18:32:10Z",
    )
    assert result["rows"] == 2
    assert result["field_count_distribution"] == {"27": 2}
    assert result["strict_central_bank_article_counts"] == {
        "ECB": 1,
        "FED": 1,
    }
    assert result["eurusd_outcomes_loaded"] is False
