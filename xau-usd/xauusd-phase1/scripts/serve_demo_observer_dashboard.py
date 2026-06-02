from __future__ import annotations

import argparse
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from generate_demo_observer_dashboard import (
    DEFAULT_LIVE_REFRESH_URL,
    DEFAULT_TERMINAL_DATA_DIR,
    DEFAULT_TERMINAL_EXE,
    generate_demo_observer_dashboard,
)
from generate_project_status_page import generate_project_status_page


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8777


class DemoDashboardServer(ThreadingHTTPServer):
    def __init__(
        self,
        server_address: tuple[str, int],
        repo_root: Path,
        terminal_data_dir: Path,
        terminal_exe: Path,
    ) -> None:
        super().__init__(server_address, DemoDashboardRequestHandler)
        self.repo_root = repo_root.resolve()
        self.terminal_data_dir = terminal_data_dir.resolve()
        self.terminal_exe = terminal_exe.resolve()


class DemoDashboardRequestHandler(BaseHTTPRequestHandler):
    server: DemoDashboardServer

    def do_GET(self) -> None:  # noqa: N802 - http.server API
        route = urlparse(self.path).path
        try:
            if route in {"/", "/demo-observer-dashboard.html"}:
                output = generate_demo_observer_dashboard(
                    repo_root=self.server.repo_root,
                    terminal_data_dir=self.server.terminal_data_dir,
                    terminal_exe=self.server.terminal_exe,
                )
                self._send_file(output.html_path, "text/html; charset=utf-8")
                return

            if route == "/api/demo-observer-dashboard.json":
                output = generate_demo_observer_dashboard(
                    repo_root=self.server.repo_root,
                    terminal_data_dir=self.server.terminal_data_dir,
                    terminal_exe=self.server.terminal_exe,
                )
                self._send_file(output.json_path, "application/json; charset=utf-8")
                return

            if route == "/status.html":
                output = generate_project_status_page(self.server.repo_root, self.server.repo_root / "status.html")
                self._send_file(output.output_path, "text/html; charset=utf-8")
                return

            static_path = _safe_static_path(self.server.repo_root, route)
            if static_path is not None:
                content_type = mimetypes.guess_type(static_path.name)[0] or "application/octet-stream"
                self._send_file(static_path, content_type)
                return

            self._send_json({"status": "NOT_FOUND", "route": route}, status=404)
        except Exception as exc:  # pragma: no cover - defensive server boundary
            self._send_json({"status": "ERROR", "error": f"{type(exc).__name__}: {exc}"}, status=500)

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send_file(self, path: Path, content_type: str) -> None:
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, payload: dict[str, object], status: int = 200) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def _safe_static_path(repo_root: Path, route: str) -> Path | None:
    if ".." in route.replace("\\", "/").split("/"):
        return None
    relative = route.lstrip("/")
    if not relative:
        return None
    candidate = (repo_root / relative).resolve()
    try:
        candidate.relative_to(repo_root.resolve())
    except ValueError:
        return None
    if candidate.is_file():
        return candidate
    return None


def serve(
    repo_root: Path,
    terminal_data_dir: Path = DEFAULT_TERMINAL_DATA_DIR,
    terminal_exe: Path = DEFAULT_TERMINAL_EXE,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
) -> None:
    server = DemoDashboardServer((host, port), repo_root, terminal_data_dir, terminal_exe)
    print(f"Live demo dashboard: http://{host}:{port}/demo-observer-dashboard.html")
    print("Every browser refresh regenerates MT5 actual broker history before serving the page.")
    print(f"Static fallback remains: {repo_root / 'demo-observer-dashboard.html'}")
    try:
        server.serve_forever()
    finally:
        server.server_close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve the demo observer dashboard with refresh-time MT5 regeneration.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--terminal-data-dir", type=Path, default=DEFAULT_TERMINAL_DATA_DIR)
    parser.add_argument("--terminal-exe", type=Path, default=DEFAULT_TERMINAL_EXE)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()
    serve(
        repo_root=args.repo_root,
        terminal_data_dir=args.terminal_data_dir,
        terminal_exe=args.terminal_exe,
        host=args.host,
        port=args.port,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
