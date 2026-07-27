from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any, BinaryIO, Iterator
from xml.etree.ElementTree import Element, iterparse
from zipfile import ZipFile

import numpy as np
import pandas as pd


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _child_text(element: Element, name: str) -> str | None:
    for child in element:
        if _local_name(child.tag) == name:
            return child.text
    return None


def _float_text(element: Element, name: str) -> float:
    value = _child_text(element, name)
    try:
        return float(value) if value is not None else float("nan")
    except ValueError:
        return float("nan")


@contextmanager
def _open_span_xml(path: Path) -> Iterator[BinaryIO]:
    if not path.exists():
        raise FileNotFoundError(f"CME SPAN file is missing: {path}")
    if path.suffix.lower() != ".zip":
        with path.open("rb") as stream:
            yield stream
        return
    with ZipFile(path) as archive:
        members = [
            name
            for name in archive.namelist()
            if name.lower().endswith(".spn")
        ]
        if len(members) != 1:
            raise ValueError(
                "A CME SPAN ZIP must contain exactly one .spn file; "
                f"found {len(members)}"
            )
        with archive.open(members[0]) as stream:
            yield stream


def _parse_euu_product(
    product: Element,
    trade_date: pd.Timestamp,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    product_id = _child_text(product, "pfId")
    for series in product:
        if _local_name(series.tag) != "series":
            continue
        expiry_text = _child_text(series, "ldot")
        expiry = pd.to_datetime(
            expiry_text, format="%Y%m%d", utc=True, errors="coerce"
        )
        if pd.isna(expiry) or expiry <= trade_date:
            continue
        dte = (expiry - trade_date).total_seconds() / 86_400.0
        series_iv = _float_text(series, "v")
        reference_price = _float_text(series, "refPrice")
        underlying_pf_id: str | None = None
        underlying_contract_id: str | None = None
        for child in series:
            if _local_name(child.tag) == "undC":
                underlying_pf_id = _child_text(child, "pfId")
                underlying_contract_id = _child_text(child, "cId")
                break
        for option in series:
            if _local_name(option.tag) != "opt":
                continue
            quote_flag = _child_text(option, "pq")
            # pq=0 denotes a normal full premium. Cabinet/cash quote
            # representations are not interchangeable with that premium.
            if quote_flag != "0":
                continue
            put_call = _child_text(option, "o")
            if put_call not in ("C", "P"):
                continue
            strike = _float_text(option, "k")
            settlement = _float_text(option, "p")
            if (
                not np.isfinite(strike)
                or strike <= 0
                or not np.isfinite(settlement)
                or settlement < 0
            ):
                continue
            option_iv = _float_text(option, "v")
            if not np.isfinite(option_iv) or option_iv <= 0:
                option_iv = float("nan")
            reported_delta = _float_text(option, "d")
            if (
                not np.isfinite(reported_delta)
                or not 0 < abs(reported_delta) < 1
            ):
                reported_delta = float("nan")
            rows.append(
                {
                    "trade_date_utc": trade_date,
                    "expiry_date_utc": expiry,
                    "dte": dte,
                    "Put/Call": put_call,
                    "strike": strike,
                    "settlement": settlement,
                    "reported_delta": reported_delta,
                    "reported_iv": option_iv,
                    "series_iv": (
                        series_iv
                        if np.isfinite(series_iv) and series_iv > 0
                        else float("nan")
                    ),
                    "open_interest": 0.0,
                    "total_volume": 0.0,
                    "span_product_id": product_id,
                    "span_contract_id": _child_text(option, "cId"),
                    "span_quote_flag": quote_flag,
                    "underlying_pf_id": underlying_pf_id,
                    "underlying_contract_id": underlying_contract_id,
                    "series_reference_price": reference_price,
                }
            )
    return rows


def read_euu_span(
    path: Path,
    *,
    require_settlement: bool = True,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Read the EUU option surface from one CME PA2/XML SPAN file.

    Settlement files are required by default. Setting
    ``require_settlement=False`` is intended only for format/sample audits,
    never for a historical outcome pass.
    """

    created: str | None = None
    point_date: str | None = None
    is_settlement: str | None = None
    run: str | None = None
    rows: list[dict[str, Any]] = []
    product_seen = False
    stack: list[str] = []
    with _open_span_xml(path) as stream:
        for event, element in iterparse(
            stream, events=("start", "end")
        ):
            tag = _local_name(element.tag)
            if event == "start":
                stack.append(tag)
                continue
            parent = stack[-2] if len(stack) >= 2 else None
            if tag == "created" and parent == "spanFile":
                created = element.text
            elif tag == "date" and parent == "pointInTime":
                point_date = element.text
            elif tag == "isSetl" and parent == "pointInTime":
                is_settlement = element.text
            elif tag == "run" and parent == "pointInTime":
                run = element.text
            elif tag == "oofPf":
                if _child_text(element, "pfCode") == "EUU":
                    if point_date is None:
                        raise ValueError(
                            "CME SPAN point-in-time date precedes no EUU "
                            "surface"
                        )
                    trade_date = pd.to_datetime(
                        point_date,
                        format="%Y%m%d",
                        utc=True,
                        errors="raise",
                    )
                    rows.extend(_parse_euu_product(element, trade_date))
                    product_seen = True
                element.clear()
            elif tag in {"futPf", "phyPf", "saoPf", "oopPf"}:
                element.clear()
            elif parent == "definitions":
                element.clear()
            stack.pop()

    metadata = {
        "source_path": str(path),
        "created": created,
        "point_in_time_date": point_date,
        "is_settlement": is_settlement,
        "run": run,
        "product_code": "EUU",
        "product_seen": product_seen,
        "row_count": len(rows),
    }
    if not product_seen:
        raise ValueError("CME SPAN file contains no EUU option product")
    if require_settlement and is_settlement != "1":
        raise ValueError(
            "CME SPAN file is not a settlement file "
            f"(isSetl={is_settlement!r})"
        )
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise ValueError("CME SPAN EUU product contains no usable options")
    frame = (
        frame.sort_values(
            [
                "trade_date_utc",
                "expiry_date_utc",
                "strike",
                "Put/Call",
            ]
        )
        .drop_duplicates(
            [
                "trade_date_utc",
                "expiry_date_utc",
                "strike",
                "Put/Call",
            ],
            keep="last",
        )
        .reset_index(drop=True)
    )
    metadata["row_count"] = len(frame)
    metadata["expiry_count"] = int(frame["expiry_date_utc"].nunique())
    metadata["minimum_dte"] = float(frame["dte"].min())
    metadata["maximum_dte"] = float(frame["dte"].max())
    return frame, metadata
