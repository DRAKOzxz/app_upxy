from __future__ import annotations

from datetime import datetime
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, send_from_directory, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["SECRET_KEY"] = "cambia-esta-clave-en-produccion"

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


@app.route("/")
def index() -> str:
    files = []
    for file_path in sorted(UPLOAD_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if file_path.is_file():
            stat = file_path.stat()
            files.append(
                {
                    "name": file_path.name,
                    "size_kb": round(stat.st_size / 1024, 2),
                    "updated": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

    return render_template("index.html", files=files)


@app.post("/upload")
def upload_file():
    file = request.files.get("file")

    if file is None or file.filename == "":
        flash("Selecciona un archivo para subir.", "error")
        return redirect(url_for("index"))

    filename = secure_filename(file.filename)
    destination = UPLOAD_DIR / filename

    if destination.exists():
        flash(f"El archivo '{filename}' ya existe. Usa otro nombre.", "error")
        return redirect(url_for("index"))

    file.save(destination)
    flash(f"Archivo '{filename}' subido correctamente.", "success")
    return redirect(url_for("index"))


@app.get("/download/<path:filename>")
def download_file(filename: str):
    return send_from_directory(UPLOAD_DIR, filename, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
