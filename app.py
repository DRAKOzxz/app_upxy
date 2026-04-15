from __future__ import annotations

import sqlite3
import time
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
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024 * 1024  # 1 GB por archivo

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
DB_PATH = BASE_DIR / "app.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"
UPLOAD_DIR.mkdir(exist_ok=True)


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


def console_event(title: str, detail: str = "") -> None:
    frames = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    for frame in frames[:6]:
        print(f"\r\033[96m{frame} {title}\033[0m", end="", flush=True)
        time.sleep(0.02)
    print(f"\r\033[92m✔ {title}\033[0m {detail}".rstrip())


@app.teardown_appcontext
def close_db(_: Any) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as db:
        if SCHEMA_PATH.exists():
            db.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        else:
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    bio TEXT DEFAULT '',
                    discord_handle TEXT DEFAULT '',
                    created_at TEXT NOT NULL
                )
                """
            )
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS friendships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    requester_id INTEGER NOT NULL,
                    addressee_id INTEGER NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('pending', 'accepted')),
                    created_at TEXT NOT NULL,
                    UNIQUE(requester_id, addressee_id),
                    FOREIGN KEY(requester_id) REFERENCES users(id),
                    FOREIGN KEY(addressee_id) REFERENCES users(id)
                )
                """
            )
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS direct_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender_id INTEGER NOT NULL,
                    receiver_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(sender_id) REFERENCES users(id),
                    FOREIGN KEY(receiver_id) REFERENCES users(id)
                )
                """
            )

        # Migración defensiva para instalaciones anteriores.
        user_cols = {row[1] for row in db.execute("PRAGMA table_info(users)").fetchall()}
        if "bio" not in user_cols:
            db.execute("ALTER TABLE users ADD COLUMN bio TEXT DEFAULT ''")
        if "discord_handle" not in user_cols:
            db.execute("ALTER TABLE users ADD COLUMN discord_handle TEXT DEFAULT ''")
        db.commit()
    console_event("Base de datos lista", str(DB_PATH))


init_db()


def login_required(view: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(view)
    def wrapped_view(*args: Any, **kwargs: Any):
        if session.get("user_id") is None:
            flash("Inicia sesión para entrar a la app.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


def current_user() -> sqlite3.Row | None:
    user_id = session.get("user_id")
    if not user_id:
        return None
    return get_db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def get_friends(user_id: int) -> list[sqlite3.Row]:
    db = get_db()
    return db.execute(
        """
        SELECT u.id, u.username, u.discord_handle
        FROM friendships f
        JOIN users u
          ON (u.id = f.requester_id AND f.addressee_id = ?)
          OR (u.id = f.addressee_id AND f.requester_id = ?)
        WHERE f.status = 'accepted'
        ORDER BY u.username COLLATE NOCASE
        """,
        (user_id, user_id),
    ).fetchall()


def are_friends(user_id: int, other_id: int) -> bool:
    db = get_db()
    row = db.execute(
        """
        SELECT id FROM friendships
        WHERE status = 'accepted'
          AND ((requester_id = ? AND addressee_id = ?) OR (requester_id = ? AND addressee_id = ?))
        """,
        (user_id, other_id, other_id, user_id),
    ).fetchone()
    return row is not None


@app.route("/")
@login_required
def index() -> str:
    user = current_user()
    assert user is not None
    user_id = int(user["id"])

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

    total_size_mb = round(sum(f["size_kb"] for f in files) / 1024, 2)

    db = get_db()
    pending_requests = db.execute(
        """
        SELECT f.id, u.username, u.discord_handle
        FROM friendships f
        JOIN users u ON u.id = f.requester_id
        WHERE f.addressee_id = ? AND f.status = 'pending'
        ORDER BY f.id DESC
        """,
        (user_id,),
    ).fetchall()

    friends = get_friends(user_id)

    selected_friend = None
    conversation: list[sqlite3.Row] = []
    selected_friend_id = request.args.get("friend", type=int)
    if selected_friend_id and are_friends(user_id, selected_friend_id):
        selected_friend = db.execute(
            "SELECT id, username, discord_handle FROM users WHERE id = ?", (selected_friend_id,)
        ).fetchone()
        conversation = db.execute(
            """
            SELECT m.*, s.username AS sender_username, r.username AS receiver_username
            FROM direct_messages m
            JOIN users s ON s.id = m.sender_id
            JOIN users r ON r.id = m.receiver_id
            WHERE (m.sender_id = ? AND m.receiver_id = ?)
               OR (m.sender_id = ? AND m.receiver_id = ?)
            ORDER BY m.id ASC
            LIMIT 200
            """,
            (user_id, selected_friend_id, selected_friend_id, user_id),
        ).fetchall()

    return render_template(
        "index.html",
        files=files,
        user=user,
        friends=friends,
        pending_requests=pending_requests,
        selected_friend=selected_friend,
        conversation=conversation,
        file_count=len(files),
        total_size_mb=total_size_mb,
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
        console_event("Registro", f"nuevo usuario: {username}")
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
        console_event("Login", f"usuario: {user['username']}")
        flash(f"Bienvenido/a {user['username']}.", "success")
        return redirect(url_for("index"))

    return render_template("auth.html", mode="login")


@app.get("/logout")
def logout():
    console_event("Logout")
    session.clear()
    flash("Sesión cerrada.", "success")
    return redirect(url_for("login"))


@app.post("/profile")
@login_required
def update_profile():
    user = current_user()
    assert user is not None

    bio = request.form.get("bio", "").strip()[:240]
    discord_handle = request.form.get("discord_handle", "").strip()[:64]

    db = get_db()
    db.execute(
        "UPDATE users SET bio = ?, discord_handle = ? WHERE id = ?",
        (bio, discord_handle, int(user["id"])),
    )
    db.commit()
    console_event("Perfil actualizado", f"usuario: {user['username']}")
    flash("Perfil actualizado.", "success")
    return redirect(url_for("index"))


@app.post("/friends/request")
@login_required
def send_friend_request():
    user = current_user()
    assert user is not None
    me = int(user["id"])

    username = request.form.get("username", "").strip()
    if not username:
        flash("Escribe un usuario para agregar.", "error")
        return redirect(url_for("index"))

    db = get_db()
    other = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    if other is None:
        flash("No existe ese usuario.", "error")
        return redirect(url_for("index"))

    other_id = int(other["id"])
    if other_id == me:
        flash("No puedes agregarte a ti mismo.", "error")
        return redirect(url_for("index"))

    existing = db.execute(
        """
        SELECT id, status FROM friendships
        WHERE (requester_id = ? AND addressee_id = ?) OR (requester_id = ? AND addressee_id = ?)
        """,
        (me, other_id, other_id, me),
    ).fetchone()

    if existing:
        flash("Ya existe una solicitud o amistad con ese usuario.", "error")
        return redirect(url_for("index"))

    db.execute(
        "INSERT INTO friendships (requester_id, addressee_id, status, created_at) VALUES (?, ?, 'pending', ?)",
        (me, other_id, datetime.utcnow().isoformat()),
    )
    db.commit()
    console_event("Solicitud de amistad", f"de {user['username']} para {username}")
    flash("Solicitud enviada.", "success")
    return redirect(url_for("index"))


@app.post("/friends/accept/<int:request_id>")
@login_required
def accept_friend_request(request_id: int):
    user = current_user()
    assert user is not None
    me = int(user["id"])

    db = get_db()
    request_row = db.execute(
        "SELECT id FROM friendships WHERE id = ? AND addressee_id = ? AND status = 'pending'",
        (request_id, me),
    ).fetchone()

    if request_row is None:
        flash("Solicitud no válida.", "error")
        return redirect(url_for("index"))

    db.execute("UPDATE friendships SET status = 'accepted' WHERE id = ?", (request_id,))
    db.commit()
    console_event("Amistad aceptada", f"usuario: {user['username']}")
    flash("Amistad aceptada. Ya puedes chatear en privado.", "success")
    return redirect(url_for("index"))


@app.post("/chat/private/<int:friend_id>")
@login_required
def send_private_message(friend_id: int):
    user = current_user()
    assert user is not None
    me = int(user["id"])

    if not are_friends(me, friend_id):
        flash("Solo puedes escribir a amigos aceptados.", "error")
        return redirect(url_for("index"))

    content = request.form.get("content", "").strip()
    if not content:
        flash("No puedes enviar un mensaje vacío.", "error")
        return redirect(url_for("index", friend=friend_id))

    db = get_db()
    db.execute(
        "INSERT INTO direct_messages (sender_id, receiver_id, content, created_at) VALUES (?, ?, ?, ?)",
        (me, friend_id, content[:800], datetime.utcnow().isoformat()),
    )
    db.commit()
    console_event("Mensaje privado", f"de {user['username']} para friend_id={friend_id}")
    return redirect(url_for("index", friend=friend_id))


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
    console_event("Archivo subido", filename)
    flash(f"Archivo '{filename}' subido correctamente.", "success")
    return redirect(url_for("index"))


@app.post("/files/delete/<path:filename>")
@login_required
def delete_file(filename: str):
    safe_name = secure_filename(filename)
    target = UPLOAD_DIR / safe_name

    if not target.exists() or not target.is_file():
        flash("El archivo no existe o ya fue eliminado.", "error")
        return redirect(url_for("index"))

    target.unlink(missing_ok=True)
    console_event("Archivo eliminado", safe_name)
    flash(f"Archivo '{safe_name}' eliminado.", "success")
    return redirect(url_for("index"))


@app.post("/chat/private/delete/<int:message_id>")
@login_required
def delete_private_message(message_id: int):
    user = current_user()
    assert user is not None
    me = int(user["id"])

    db = get_db()
    msg = db.execute(
        "SELECT id, sender_id, receiver_id FROM direct_messages WHERE id = ?",
        (message_id,),
    ).fetchone()

    if msg is None:
        flash("Mensaje no encontrado.", "error")
        return redirect(url_for("index"))

    if int(msg["sender_id"]) != me:
        flash("Solo puedes eliminar tus propios mensajes.", "error")
        return redirect(url_for("index", friend=int(msg["receiver_id"])))

    db.execute("DELETE FROM direct_messages WHERE id = ?", (message_id,))
    db.commit()
    console_event("Mensaje eliminado", f"id={message_id}")
    flash("Mensaje eliminado.", "success")
    return redirect(url_for("index", friend=int(msg["receiver_id"])))


@app.errorhandler(413)
def too_large_file(_: Any):
    flash("El archivo excede el límite permitido (1 GB).", "error")
    return redirect(url_for("index"))


@app.get("/download/<path:filename>")
@login_required
def download_file(filename: str):
    return send_from_directory(UPLOAD_DIR, filename, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
