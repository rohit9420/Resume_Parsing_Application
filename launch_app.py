import json
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

PROJECT_ROOT = Path(__file__).resolve().parent
API_URL = "http://127.0.0.1:8000"


def wait_for_api(process: subprocess.Popen[bytes], timeout: float = 30) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"FastAPI exited with status {process.returncode}.")
        try:
            with urlopen(f"{API_URL}/health", timeout=1) as response:
                if json.load(response).get("status") == "ok":
                    return
        except (OSError, URLError, ValueError):
            time.sleep(0.25)
    raise TimeoutError(f"FastAPI did not become ready at {API_URL}.")


def main() -> int:
    api_process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "parsingapplication.api:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
        ],
        cwd=PROJECT_ROOT,
    )
    try:
        wait_for_api(api_process)
        print("API is ready. Starting Streamlit...")
        environment = dict(os.environ)
        environment["RESUME_API_URL"] = API_URL
        return subprocess.call(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "streamlit_app.py",
            ],
            cwd=PROJECT_ROOT,
            env=environment,
        )
    except KeyboardInterrupt:
        return 0
    finally:
        if api_process.poll() is None:
            api_process.terminate()
            try:
                api_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                api_process.kill()
                api_process.wait()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, TimeoutError) as error:
        print(f"Could not start the application: {error}", file=sys.stderr)
        raise SystemExit(1) from error
