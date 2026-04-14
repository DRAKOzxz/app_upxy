from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

from flask import Flask, abort, flash, redirect, render_template, request, send_from_directory, url_for
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
DB_PATH = BASE_DIR / "files.db"
ALLOWED_EXTENSIONS = {
    "txt",
    "pdf",
    "png",
    "jpg",
    "jpeg",
    "gif",
    "zip",
    "rar",
    "7z",
    "doc",
    "docx",
    "xls",
    "xlsx",
    "ppt",
    "pptx",
    "mp3",
    "mp4",
}

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB
app.config["SECRET_KEY"] = "cambia-esta-clave-en-produccion"


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    UPLOAD_DIR.mkdir(exist_ok=True)
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_name TEXT NOT NULL,
                stored_name TEXT NOT NULL UNIQUE,
                uploaded_by TEXT NOT NULL,
                uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def allowed_file(filename: str) -> bool:
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def list_files() -> Iterable[sqlite3.Row]:
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT id, original_name, stored_name, uploaded_by, uploaded_at
            FROM files
            ORDER BY uploaded_at DESC
            """
        ).fetchall()
    return rows


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", files=list_files(), allowed=", ".join(sorted(ALLOWED_EXTENSIONS)))


@app.route("/upload", methods=["POST"])
def upload_file():
    username = request.form.get("username", "").strip()
    file = request.files.get("file")

    if not username:
        flash("Debes ingresar tu nombre.", "error")
        return redirect(url_for("index"))

    if file is None or file.filename == "":
        flash("Debes seleccionar un archivo.", "error")
        return redirect(url_for("index"))

    if not allowed_file(file.filename):
        flash("Formato no permitido.", "error")
        return redirect(url_for("index"))

    clean_name = secure_filename(file.filename)
    file_path = UPLOAD_DIR / clean_name

    counter = 1
    while file_path.exists():
        stem = Path(clean_name).stem
        suffix = Path(clean_name).suffix
        new_name = f"{stem}_{counter}{suffix}"
        file_path = UPLOAD_DIR / new_name
        counter += 1

    file.save(file_path)

    with get_db() as conn:
        conn.execute(
            "INSERT INTO files (original_name, stored_name, uploaded_by) VALUES (?, ?, ?)",
            (file.filename, file_path.name, username),
        )

    flash("Archivo subido correctamente.", "ok")
    return redirect(url_for("index"))


@app.route("/download/<int:file_id>", methods=["GET"])
def download_file(file_id: int):
    with get_db() as conn:
        row = conn.execute(
            "SELECT original_name, stored_name FROM files WHERE id = ?",
            (file_id,),
        ).fetchone()

    if row is None:
        abort(404)

    return send_from_directory(
        UPLOAD_DIR,
        row["stored_name"],
        as_attachment=True,
        download_name=row["original_name"],
    )


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
