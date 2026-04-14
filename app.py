from __future__ import annotations

import sqlite3
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable

from flask import (
    Flask,
    flash,
    g,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["SECRET_KEY"] = "cambia-esta-clave-en-produccion"

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
DB_PATH = BASE_DIR / "app.db"
UPLOAD_DIR.mkdir(exist_ok=True)


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_: Any) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    db = sqlite3.connect(DB_PATH)
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
    db.commit()
    db.close()


init_db()


def login_required(view: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(view)
    def wrapped_view(*args: Any, **kwargs: Any):
        if session.get("user_id") is None:
            flash("Inicia sesión para entrar a la app.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


def current_username() -> str | None:
    return session.get("username")


@app.route("/")
@login_required
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

    db = get_db()
    messages = db.execute(
        """
        SELECT m.content, m.created_at, u.username
        FROM messages m
        JOIN users u ON u.id = m.user_id
        ORDER BY m.id DESC
        LIMIT 50
        """
    ).fetchall()

    return render_template(
        "index.html",
        files=files,
        messages=reversed(messages),
        username=current_username(),
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if len(username) < 3 or len(password) < 6:
            flash("Usuario mínimo 3 caracteres y contraseña mínimo 6.", "error")
            return redirect(url_for("register"))

        db = get_db()
        exists = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if exists:
            flash("Ese nombre de usuario ya está en uso.", "error")
            return redirect(url_for("register"))

        db.execute(
            "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
            (username, generate_password_hash(password), datetime.utcnow().isoformat()),
        )
        db.commit()
        flash("Cuenta creada. Ahora inicia sesión.", "success")
        return redirect(url_for("login"))

    return render_template("auth.html", mode="register")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        db = get_db()
        user = db.execute(
            "SELECT id, username, password_hash FROM users WHERE username = ?", (username,)
        ).fetchone()

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Credenciales inválidas.", "error")
            return redirect(url_for("login"))

        session.clear()
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        flash(f"Bienvenido/a {user['username']}.", "success")
        return redirect(url_for("index"))

    return render_template("auth.html", mode="login")


@app.get("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada.", "success")
    return redirect(url_for("login"))


@app.post("/upload")
@login_required
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


@app.post("/chat")
@login_required
def send_message():
    content = request.form.get("content", "").strip()
    if not content:
        flash("No puedes enviar un mensaje vacío.", "error")
        return redirect(url_for("index"))

    db = get_db()
    db.execute(
        "INSERT INTO messages (user_id, content, created_at) VALUES (?, ?, ?)",
        (session["user_id"], content[:600], datetime.utcnow().isoformat()),
    )
    db.commit()
    return redirect(url_for("index"))


@app.get("/download/<path:filename>")
@login_required
def download_file(filename: str):
    return send_from_directory(UPLOAD_DIR, filename, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
