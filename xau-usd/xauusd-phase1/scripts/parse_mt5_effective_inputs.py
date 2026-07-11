"""Parse effective EA inputs and native account metadata from an MT5 HTML report."""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any, Mapping


class EffectiveInputError(RuntimeError):
    """Raised when an MT5 report cannot prove its effective input contract."""


def read_mt5_report(path: Path) -> str:
    data = path.read_bytes()
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16")
    if data.count(b"\x00") > max(4, len(data) // 10):
        return data.decode("utf-16-le")
    return data.decode("utf-8-sig")


def clean_html(value: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", value)).strip().replace("\xa0", " ")


def report_rows(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for row_html in re.findall(r"<tr\b[^>]*>(.*?)</tr>", text, flags=re.I | re.S):
        cells = [
            clean_html(cell)
            for cell in re.findall(r"<t[dh]\b[^>]*>(.*?)</t[dh]>", row_html, flags=re.I | re.S)
        ]
        if cells:
            rows.append(cells)
    return rows


def parse_effective_inputs(path: Path) -> dict[str, str]:
    rows = report_rows(read_mt5_report(path))
    collecting = False
    inputs: dict[str, str] = {}
    for cells in rows:
        label = cells[0].rstrip(":").strip()
        value = cells[-1].strip()
        if label == "Inputs":
            collecting = True
        elif collecting and label:
            break
        if not collecting or "=" not in value:
            continue
        key, input_value = value.split("=", 1)
        key = key.strip()
        if not key:
            raise EffectiveInputError(f"Empty effective-input key in {path}")
        if key in inputs:
            raise EffectiveInputError(f"Duplicate effective input {key!r} in {path}")
        inputs[key] = input_value.strip()
    if not inputs:
        raise EffectiveInputError(f"No effective MT5 inputs found in {path}")
    return inputs


def parse_native_environment(path: Path) -> dict[str, str | None]:
    text = read_mt5_report(path)
    labels: dict[str, str] = {}
    for cells in report_rows(text):
        if len(cells) < 2:
            continue
        label = cells[0].rstrip(":").strip()
        if label in {"Expert", "Symbol", "Period", "Company", "Currency", "Initial Deposit", "Leverage"}:
            labels[label] = cells[-1].strip()
    header_matches = re.findall(r"<div\b[^>]*><b>(.*?)</b>", text, flags=re.I | re.S)
    server = None
    build = None
    for raw in header_matches:
        value = clean_html(raw)
        match = re.fullmatch(r"(.+?)\s*\(Build\s+(\d+)\)", value)
        if match:
            server, build = match.group(1).strip(), match.group(2)
            break
    return {
        "server": server,
        "build": build,
        "company": labels.get("Company"),
        "currency": labels.get("Currency"),
        "initial_deposit": labels.get("Initial Deposit"),
        "leverage": labels.get("Leverage"),
        "expert": labels.get("Expert"),
        "symbol": labels.get("Symbol"),
        "period": labels.get("Period"),
        "margin_mode": None,
    }


def parse_tester_ini_inputs(path: Path) -> dict[str, str]:
    section = ""
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith((";", "#")):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1]
            continue
        if section == "TesterInputs" and "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    if not values:
        raise EffectiveInputError(f"No TesterInputs found in {path}")
    return values


def compare_inputs(expected: Mapping[str, str], actual: Mapping[str, str]) -> dict[str, Any]:
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    unequal = {
        key: {"expected": expected[key], "actual": actual[key]}
        for key in sorted(set(expected) & set(actual))
        if expected[key] != actual[key]
    }
    return {
        "pass": not missing and not extra and not unequal,
        "expected_count": len(expected),
        "actual_count": len(actual),
        "missing": missing,
        "extra": extra,
        "unequal": unequal,
    }


def require_equal_inputs(expected: Mapping[str, str], actual: Mapping[str, str], *, label: str) -> dict[str, Any]:
    comparison = compare_inputs(expected, actual)
    if not comparison["pass"]:
        raise EffectiveInputError(f"{label} effective-input mismatch: {comparison}")
    return comparison
