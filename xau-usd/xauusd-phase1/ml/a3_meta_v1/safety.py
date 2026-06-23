from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

from .mt5_readonly import FORBIDDEN_MT5_CALLS


ALLOWED_MT5_IMPORT_FILES = {"mt5_readonly.py"}
MT5_IMPORT_TOKEN = "Meta" + "Trader5"


@dataclass(frozen=True)
class SafetyFinding:
    file: str
    symbol: str
    detail: str


def scan_c02_python_safety(root: Path) -> list[SafetyFinding]:
    findings: list[SafetyFinding] = []
    for path in sorted(root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        findings.extend(_scan_python_file(path, root))
    return findings


def _scan_python_file(path: Path, root: Path) -> list[SafetyFinding]:
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(path))
    findings: list[SafetyFinding] = []
    rel = str(path.relative_to(root))
    if path.name not in ALLOWED_MT5_IMPORT_FILES and MT5_IMPORT_TOKEN in text:
        findings.append(SafetyFinding(rel, MT5_IMPORT_TOKEN, "MT5 package may only be loaded by mt5_readonly.py"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in FORBIDDEN_MT5_CALLS:
                findings.append(SafetyFinding(rel, node.func.attr, "forbidden MT5 method call"))
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in FORBIDDEN_MT5_CALLS:
                findings.append(SafetyFinding(rel, node.func.id, "forbidden MT5 function call"))
    return findings
