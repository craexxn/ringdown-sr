"""Check warm concurrent starts while another process owns a CondaPkg lock."""

import shutil
import subprocess
import sys
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from queue import Empty, Queue

from run_python import ROOT, prepare_runtime


def check_copy(root: Path, environment: dict[str, str]) -> str:
    result = subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "run_python.py"),
            str(root / "scripts" / "check_environment.py"),
        ],
        env=environment,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    if "Technical environment check passed." not in result.stdout:
        raise RuntimeError("The repeated startup did not finish its environment check.")
    if "CondaPkg policy: Null; PythonCall extension loaded." not in result.stdout:
        raise RuntimeError(
            "The repeated startup did not verify the PythonCall extension."
        )
    if "ERROR:" in result.stderr or "Waiting for lock" in result.stderr:
        raise RuntimeError(result.stderr)
    return result.stdout


def main() -> None:
    environment = prepare_runtime(ROOT)
    with tempfile.TemporaryDirectory(prefix="ringdown startup check ") as directory:
        root = Path(directory)
        paths = (
            ".python-version",
            "julia/Project.toml",
            "julia/Manifest.toml",
            "src/ringdown_sr/juliapkg.json",
            "scripts/run_python.py",
            "scripts/check_environment.py",
        )
        for relative in paths:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        lock_path = root / "julia" / ".CondaPkg" / "lock"
        lock_path.parent.mkdir()
        helper = subprocess.Popen(
            [
                environment["PYTHON_JULIACALL_EXE"],
                "--startup-file=no",
                f"--project={root / 'julia'}",
                "-e",
                (
                    "using FileWatching; "
                    "lock=FileWatching.Pidfile.mkpidlock(ARGS[1]); "
                    'println("held"); flush(stdout); readline(stdin); close(lock)'
                ),
                str(lock_path),
            ],
            env=environment,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
        )
        try:
            ready: Queue[str] = Queue()
            reader = threading.Thread(
                target=lambda: ready.put(helper.stdout.readline()), daemon=True
            )
            reader.start()
            try:
                message = ready.get(timeout=30)
            except Empty as error:
                raise RuntimeError(
                    "The CondaPkg lock helper did not start within 30 s."
                ) from error
            if message.strip() != "held":
                raise RuntimeError(
                    "The CondaPkg lock helper failed to acquire its lock."
                )
            original = lock_path.read_bytes()
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(check_copy, root, environment) for _ in range(2)]
                for index, future in enumerate(futures, start=1):
                    future.result()
                    print(f"Concurrent warm startup {index}: passed.")
            if helper.poll() is not None or lock_path.read_bytes() != original:
                raise RuntimeError(
                    "A startup disturbed the other process's CondaPkg lock."
                )
            if set(lock_path.parent.iterdir()) != {lock_path}:
                raise RuntimeError("A startup created CondaPkg environment files.")
            print(
                "Active CondaPkg lock retained unchanged; no Conda environment created."
            )
        finally:
            try:
                helper.stdin.close()
            except OSError:
                pass
            try:
                helper.wait(timeout=10)
            except subprocess.TimeoutExpired:
                helper.terminate()
                try:
                    helper.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    helper.kill()
                    helper.wait()
            helper.stdout.close()
    print("Repeated/concurrent Julia startup check passed.")


if __name__ == "__main__":
    main()
