import subprocess
import sys
import threading

import os


class StdioTransport:
    def __init__(
        self,
        command: list[str] | None = None,
        cwd=None,
        timeout: float = 10.0,
    ) -> None:
        self.command = command or [sys.executable]
        self.cwd = cwd
        self.timeout = timeout
        self._proc: subprocess.Popen[str] | None = None

    def start(self) -> None:
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        self._proc = subprocess.Popen(
            self.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self.cwd,
            env=env,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )

    def request(self, line: str) -> str:
        if self._proc is None or self._proc.stdin is None or self._proc.stdout is None:
            raise RuntimeError("transport not started")
        if not line.endswith("\n"):
            line = line + "\n"
        self._proc.stdin.write(line)
        self._proc.stdin.flush()

        box: list[str] = []

        def read() -> None:
            assert self._proc is not None and self._proc.stdout is not None
            box.append(self._proc.stdout.readline())

        worker = threading.Thread(target=read, daemon=True)
        worker.start()
        worker.join(self.timeout)
        if worker.is_alive():
            self._proc.kill()
            raise TimeoutError(f"mcp timeout after {self.timeout}s")

        out = box[0] if box else ""
        if out == "":
            raise RuntimeError("server closed stdout")
        return out.strip()

    def close(self) -> None:
        if self._proc is None:
            return
        if self._proc.stdin is not None:
            try:
                self._proc.stdin.close()
            except OSError:
                pass
        try:
            self._proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self._proc.kill()
            self._proc.wait()
        self._proc = None