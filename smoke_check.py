"""Smoke check for TaskBar.

Run after Auto Research/build finishes:

    python smoke_check.py

It validates the Python app self-test and the packaged executable. The script
exits non-zero when the app does not start, render, or persist basic data.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path


APP_DIR = Path(__file__).resolve().parent
APP_PY = APP_DIR / "taskbar.py"
EXE = APP_DIR / "dist" / "TaskBar.exe"
CAPTURE_SCRIPT = APP_DIR / "capture_print.ps1"
SMOKE_DATA = APP_DIR / "dist" / "smoke_tasks.json"
SMOKE_PNG = APP_DIR / "dist" / "smoke_window.png"


def fail(message: str) -> None:
    safe_print(f"FAIL {message}")
    raise SystemExit(1)


def pass_(message: str) -> None:
    safe_print(f"PASS {message}")


def safe_print(message: str, *, stderr: bool = False) -> None:
    stream = sys.stderr if stderr else sys.stdout
    encoding = stream.encoding or "utf-8"
    data = str(message).encode(encoding, errors="backslashreplace").decode(encoding, errors="replace")
    print(data, file=stream)


def run_checked(cmd: list[str], *, env: dict[str, str], timeout: int = 30) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        cmd,
        cwd=str(APP_DIR),
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        safe_print((result.stdout or "").strip())
        safe_print((result.stderr or "").strip(), stderr=True)
        fail(f"command failed: {' '.join(cmd)}")
    return result


def build_env(data_file: Path) -> dict[str, str]:
    env = dict(os.environ)
    env["TASKBAR_DATA_FILE"] = str(data_file)
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def write_fixture(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            [
                {"text": "llamar a labora", "done": False},
                {"text": "hola", "done": True},
            ],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def check_python_selftest() -> None:
    selftest_data = APP_DIR / "dist" / "smoke_selftest_tasks.json"
    selftest_data.unlink(missing_ok=True)
    env = build_env(selftest_data)
    run_checked([sys.executable, "-m", "py_compile", str(APP_PY)], env=env)
    pass_("taskbar.py compiles")

    result = run_checked([sys.executable, str(APP_PY), "--test"], env=env, timeout=20)
    if "ALL TESTS PASSED" not in result.stdout:
        safe_print(result.stdout)
        fail("python self-test did not report success")
    pass_("python UI self-test passed")


def capture_window(env: dict[str, str], pid: int) -> str:
    if not CAPTURE_SCRIPT.exists():
        fail(f"missing capture script: {CAPTURE_SCRIPT}")

    result = run_checked(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(CAPTURE_SCRIPT),
            str(SMOKE_PNG),
            str(pid),
        ],
        env=env,
        timeout=20,
    )
    if not SMOKE_PNG.exists() or SMOKE_PNG.stat().st_size < 10_000:
        fail("window capture was not created or is too small")
    return result.stdout


def check_packaged_exe() -> None:
    if not EXE.exists():
        fail(f"missing executable: {EXE}")

    stop_existing_project_exe()
    write_fixture(SMOKE_DATA)
    env = build_env(SMOKE_DATA)
    proc = subprocess.Popen([str(EXE)], cwd=str(APP_DIR), env=env)
    try:
        deadline = time.time() + 12
        output = ""
        light_pixels = -1
        while time.time() < deadline:
            if proc.poll() is not None:
                fail(f"TaskBar.exe exited early with code {proc.returncode}")
            time.sleep(1)
            try:
                output = capture_window(env, proc.pid)
                match = re.search(r"Banda de filas: (\d+) px claros", output)
                if match:
                    light_pixels = int(match.group(1))
                    if light_pixels > 0:
                        break
            except SystemExit:
                if time.time() >= deadline:
                    raise
        else:
            fail("TaskBar.exe did not expose a visible TaskBar window")

        match = re.search(r"Banda de filas: (\d+) px claros", output)
        if not match:
            safe_print(output)
            fail("capture output did not include row-band pixel metric")
        light_pixels = int(match.group(1))
        if light_pixels <= 0:
            safe_print(output)
            fail("window capture did not contain visible task text")
        pass_(f"packaged exe rendered visible task rows ({light_pixels} light pixels)")
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)

    data = json.loads(SMOKE_DATA.read_text(encoding="utf-8"))
    if len(data) != 2 or data[0]["text"] != "llamar a labora" or data[1]["done"] is not True:
        fail("packaged exe did not load/preserve smoke fixture")
    pass_("packaged exe loaded smoke data")


def stop_existing_project_exe() -> None:
    ps = (
        "$exe = $args[0]; "
        "Get-CimInstance Win32_Process -Filter \"name = 'TaskBar.exe'\" | "
        "Where-Object { $_.ExecutablePath -eq $exe } | "
        "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps, str(EXE)],
        cwd=str(APP_DIR),
        text=True,
        capture_output=True,
        timeout=10,
    )


def main() -> None:
    check_python_selftest()
    check_packaged_exe()
    safe_print("SMOKE CHECK PASSED")


if __name__ == "__main__":
    main()
