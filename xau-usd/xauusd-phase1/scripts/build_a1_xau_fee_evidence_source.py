from __future__ import annotations

"""Build the pinned, instrumentation-only DEAL_FEE evidence EA source.

The generated source is not a strategy variant.  It is the exact Router V1/base EA
blob from the frozen commit with a high-precision DEAL_FEE field and an inert-in-
tester, fail-closed Strategy Tester guard.  The reversible transformation is verified
byte-for-byte before any source is written.
"""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Sequence


PINNED_COMMIT = "006824cde421ea61a0bcdb074804f9ccf95c17a9"
PINNED_SOURCE_RELATIVE = Path(
    "xau-usd/xauusd-phase1/mt5/Experts/A1XauM5MomentumContinuationExecutor.mq5"
)
PINNED_SOURCE_SHA256 = "3372d8e751141f1d397d9967b8c14272046e1a733a64f67e63fcc3f56e53d355"
GENERATED_EXPERT_NAME = "A1XauM5MomentumFeeEvidencePinned006824"
FEE_DECIMAL_PLACES = 16

ORIGINAL_HEADER = (
    'FileWrite(handle, "timestamp_broker", "timestamp_local", "run_id", "account", "symbol", "magic", '
    '"deal_ticket", "position_id", "entry_code", "type_code", "reason_code", "direction", "volume", '
    '"price", "profit", "commission", "swap", "order_ticket", "comment");'
)
INSTRUMENTED_HEADER = (
    'FileWrite(handle, "timestamp_broker", "timestamp_local", "run_id", "account", "symbol", "magic", '
    '"deal_ticket", "position_id", "entry_code", "type_code", "reason_code", "direction", "volume", '
    '"price", "profit", "commission", "swap", "fee", "order_ticket", "comment");'
)

ORIGINAL_DEAL_BLOCK = """   ArrayResize(values, 19);
   values[0] = Timestamp();
   values[1] = TimeToString(TimeLocal(), TIME_DATE | TIME_SECONDS);
   values[2] = InpRunId;
   values[3] = IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN));
   values[4] = InpTargetSymbol;
   values[5] = IntegerToString((int)InpMagicNumber);
   values[6] = IntegerToString((long)deal_ticket);
   values[7] = IntegerToString((long)HistoryDealGetInteger(deal_ticket, DEAL_POSITION_ID));
   values[8] = IntegerToString((int)entry);
   values[9] = IntegerToString((int)type);
   values[10] = IntegerToString((int)HistoryDealGetInteger(deal_ticket, DEAL_REASON));
   values[11] = DealDirection(entry, type);
   values[12] = DoubleToString(HistoryDealGetDouble(deal_ticket, DEAL_VOLUME), 2);
   values[13] = DoubleToString(HistoryDealGetDouble(deal_ticket, DEAL_PRICE), _Digits);
   values[14] = DoubleToString(HistoryDealGetDouble(deal_ticket, DEAL_PROFIT), 2);
   values[15] = DoubleToString(HistoryDealGetDouble(deal_ticket, DEAL_COMMISSION), 2);
   values[16] = DoubleToString(HistoryDealGetDouble(deal_ticket, DEAL_SWAP), 2);
   values[17] = IntegerToString((long)HistoryDealGetInteger(deal_ticket, DEAL_ORDER));
   values[18] = HistoryDealGetString(deal_ticket, DEAL_COMMENT);
"""
INSTRUMENTED_DEAL_BLOCK = """   ArrayResize(values, 20);
   values[0] = Timestamp();
   values[1] = TimeToString(TimeLocal(), TIME_DATE | TIME_SECONDS);
   values[2] = InpRunId;
   values[3] = IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN));
   values[4] = InpTargetSymbol;
   values[5] = IntegerToString((int)InpMagicNumber);
   values[6] = IntegerToString((long)deal_ticket);
   values[7] = IntegerToString((long)HistoryDealGetInteger(deal_ticket, DEAL_POSITION_ID));
   values[8] = IntegerToString((int)entry);
   values[9] = IntegerToString((int)type);
   values[10] = IntegerToString((int)HistoryDealGetInteger(deal_ticket, DEAL_REASON));
   values[11] = DealDirection(entry, type);
   values[12] = DoubleToString(HistoryDealGetDouble(deal_ticket, DEAL_VOLUME), 2);
   values[13] = DoubleToString(HistoryDealGetDouble(deal_ticket, DEAL_PRICE), _Digits);
   values[14] = DoubleToString(HistoryDealGetDouble(deal_ticket, DEAL_PROFIT), 2);
   values[15] = DoubleToString(HistoryDealGetDouble(deal_ticket, DEAL_COMMISSION), 2);
   values[16] = DoubleToString(HistoryDealGetDouble(deal_ticket, DEAL_SWAP), 2);
   values[17] = DoubleToString(HistoryDealGetDouble(deal_ticket, DEAL_FEE), 16);
   values[18] = IntegerToString((long)HistoryDealGetInteger(deal_ticket, DEAL_ORDER));
   values[19] = HistoryDealGetString(deal_ticket, DEAL_COMMENT);
"""

ORIGINAL_ONINIT = """int OnInit()
  {
   if(_Symbol != InpTargetSymbol)
"""
INSTRUMENTED_ONINIT = """int OnInit()
  {
   if(!(bool)MQLInfoInteger(MQL_TESTER))
     {
      Print("A1_XAU_FEE_EVIDENCE: Strategy Tester only");
      return INIT_FAILED;
     }
   if(_Symbol != InpTargetSymbol)
"""

ORIGINAL_SWITCH_CASES = """      case 19: FileWrite(handle, values[0], values[1], values[2], values[3], values[4], values[5], values[6], values[7], values[8], values[9], values[10], values[11], values[12], values[13], values[14], values[15], values[16], values[17], values[18]); break;
      case 21: FileWrite(handle, values[0], values[1], values[2], values[3], values[4], values[5], values[6], values[7], values[8], values[9], values[10], values[11], values[12], values[13], values[14], values[15], values[16], values[17], values[18], values[19], values[20]); break;
"""
INSTRUMENTED_SWITCH_CASES = """      case 19: FileWrite(handle, values[0], values[1], values[2], values[3], values[4], values[5], values[6], values[7], values[8], values[9], values[10], values[11], values[12], values[13], values[14], values[15], values[16], values[17], values[18]); break;
      case 20: FileWrite(handle, values[0], values[1], values[2], values[3], values[4], values[5], values[6], values[7], values[8], values[9], values[10], values[11], values[12], values[13], values[14], values[15], values[16], values[17], values[18], values[19]); break;
      case 21: FileWrite(handle, values[0], values[1], values[2], values[3], values[4], values[5], values[6], values[7], values[8], values[9], values[10], values[11], values[12], values[13], values[14], values[15], values[16], values[17], values[18], values[19], values[20]); break;
"""


class FeeEvidenceSourceError(ValueError):
    pass


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def read_source(repo_root: Path, *, commit: str = PINNED_COMMIT, expected_sha256: str = PINNED_SOURCE_SHA256) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "show", f"{commit}:{PINNED_SOURCE_RELATIVE.as_posix()}"],
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        raise FeeEvidenceSourceError(result.stderr.decode("utf-8", errors="replace").strip())
    if sha256_bytes(result.stdout) != expected_sha256:
        raise FeeEvidenceSourceError("source SHA256 mismatch")
    return result.stdout


def read_pinned_source(repo_root: Path) -> bytes:
    return read_source(repo_root)


def _replace_exact_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise FeeEvidenceSourceError(f"{label} replacement expected once, found {count}")
    return source.replace(old, new, 1)


def instrument_deal_fee(source_bytes: bytes, *, expected_sha256: str = PINNED_SOURCE_SHA256) -> bytes:
    if sha256_bytes(source_bytes) != expected_sha256:
        raise FeeEvidenceSourceError("instrumentation input is not the pinned source blob")
    source = source_bytes.decode("utf-8")
    source = _replace_exact_once(source, ORIGINAL_HEADER, INSTRUMENTED_HEADER, "deal header")
    source = _replace_exact_once(source, ORIGINAL_DEAL_BLOCK, INSTRUMENTED_DEAL_BLOCK, "deal logger")
    source = _replace_exact_once(source, ORIGINAL_ONINIT, INSTRUMENTED_ONINIT, "tester-only guard")
    source = _replace_exact_once(source, ORIGINAL_SWITCH_CASES, INSTRUMENTED_SWITCH_CASES, "20-field writer")
    instrumented = source.encode("utf-8")
    if remove_deal_fee_instrumentation(instrumented) != source_bytes:
        raise FeeEvidenceSourceError("fee instrumentation is not exactly reversible")
    return instrumented


def remove_deal_fee_instrumentation(source_bytes: bytes) -> bytes:
    source = source_bytes.decode("utf-8")
    source = _replace_exact_once(source, INSTRUMENTED_HEADER, ORIGINAL_HEADER, "instrumented deal header")
    source = _replace_exact_once(
        source, INSTRUMENTED_DEAL_BLOCK, ORIGINAL_DEAL_BLOCK, "instrumented deal logger"
    )
    source = _replace_exact_once(source, INSTRUMENTED_ONINIT, ORIGINAL_ONINIT, "instrumented tester-only guard")
    source = _replace_exact_once(
        source, INSTRUMENTED_SWITCH_CASES, ORIGINAL_SWITCH_CASES, "instrumented 20-field writer"
    )
    return source.encode("utf-8")


def build_fee_evidence_source(
    repo_root: Path,
    output_source: Path,
    manifest_path: Path,
    *,
    source_commit: str = PINNED_COMMIT,
    source_sha256: str = PINNED_SOURCE_SHA256,
    generated_expert_name: str = GENERATED_EXPERT_NAME,
) -> dict[str, Any]:
    pinned = read_source(repo_root.resolve(), commit=source_commit, expected_sha256=source_sha256)
    instrumented = instrument_deal_fee(pinned, expected_sha256=source_sha256)
    output_source.parent.mkdir(parents=True, exist_ok=True)
    output_source.write_bytes(instrumented)
    manifest = {
        "schema_version": "a1_xau_fee_evidence_source_v1",
        "purpose": "instrumentation_only_deal_fee_reproduction",
        "strategy_change": False,
        "pinned_commit": source_commit,
        "pinned_source": PINNED_SOURCE_RELATIVE.as_posix(),
        "pinned_source_sha256": source_sha256,
        "generated_expert_name": generated_expert_name,
        "instrumented_source_sha256": sha256_bytes(instrumented),
        "reversible_to_pinned_source": remove_deal_fee_instrumentation(instrumented) == pinned,
        "instrumentation": {
            "deal_fee_appended_at_decimal_places": FEE_DECIMAL_PLACES,
            "strategy_tester_only_guard": True,
        },
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the pinned instrumentation-only DEAL_FEE EA source")
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--output-source", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    manifest = build_fee_evidence_source(args.repo_root, args.output_source, args.manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
