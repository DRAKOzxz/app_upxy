from __future__ import annotations

import subprocess
import sys
import time
import webbrowser

URL = "http://127.0.0.1:5000"


def main() -> None:
    process = subprocess.Popen([sys.executable, "app.py"])
    time.sleep(1.3)
    webbrowser.open(URL)
    print(f"UPXY - PRIVATE ejecutándose en {URL}")

    try:
        process.wait()
    except KeyboardInterrupt:
        process.terminate()
        process.wait(timeout=5)


if __name__ == "__main__":
    main()
