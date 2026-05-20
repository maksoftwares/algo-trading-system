from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class LoggingSetup:
    log_path: Path


def configure_run_logging(root: str | Path, command: str | None = None) -> LoggingSetup:
    project_root = Path(root).resolve()
    logs_dir = project_root / "outputs" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    log_path = _unique_log_path(logs_dir / f"phase0_run_{stamp}.log")

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    _remove_phase0_file_handlers(logger)

    formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.set_name("phase0_run_file")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    if not any(handler.get_name() == "phase0_console" for handler in logger.handlers):
        console_handler = logging.StreamHandler()
        console_handler.set_name("phase0_console")
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.WARNING)
        logger.addHandler(console_handler)

    logging.getLogger(__name__).info("Phase 0 command started: %s", command or "unknown")
    return LoggingSetup(log_path)


def log_command_success(command: str | None, log_path: Path) -> None:
    logging.getLogger(__name__).info("Phase 0 command completed: %s; log=%s", command, log_path)


def log_command_failure(command: str | None, exc: BaseException, log_path: Path | None) -> None:
    logging.getLogger(__name__).info(
        "Phase 0 command failed: %s; log=%s; error=%s",
        command,
        log_path or "",
        exc,
    )


def _remove_phase0_file_handlers(logger: logging.Logger) -> None:
    for handler in list(logger.handlers):
        if handler.get_name() == "phase0_run_file":
            logger.removeHandler(handler)
            handler.close()


def _unique_log_path(path: Path) -> Path:
    if not path.exists():
        return path
    for index in range(2, 1000):
        candidate = path.with_name(f"{path.stem}_{index}{path.suffix}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"Could not allocate unique log path under {path.parent}.")
