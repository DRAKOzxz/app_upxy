# app_upxy

Aplicación web para compartir archivos, con perfiles y chat privado entre amigos (estilo Discord).

## Funciones

- Registro e inicio de sesión con usuario/contraseña.
- Menú de perfil con bio y usuario de Discord.
- Solicitudes de amistad y lista de amigos.
- Chat privado entre amigos (reemplaza el chat global).
- Subir archivos compartidos.
- Ver listado de archivos compartidos.
- Descargar archivos.

## Requisitos

- Python 3.10+

## Ejecutar

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python init_app_db.py
python app.py
```

Luego abre: `http://localhost:5000`

## Nota de datos

- Los archivos se guardan en `uploads/`.
- Los usuarios, amistades y mensajes privados se guardan en `app.db` (SQLite).
- Si ya tienes archivos en `uploads/`, se mantienen sin borrarse.

## Archivos importantes

- `schema.sql`: esquema de base de datos (usuarios, amistades, chat privado).
- `init_app_db.py`: genera/actualiza `app.db` usando el esquema.
- `templates/chat_panel.html`: bloque dedicado de la UI del chat privado.
