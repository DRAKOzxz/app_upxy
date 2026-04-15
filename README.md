# UPXY - PRIVATE

Aplicación web para compartir archivos, con perfiles y chat privado entre amigos (estilo Discord/futurista).

## Funciones

- Registro e inicio de sesión con usuario/contraseña.
- Menú de perfil con bio y usuario de Discord.
- Solicitudes de amistad y lista de amigos.
- Chat privado entre amigos (reemplaza el chat global).
- Subir archivos compartidos (hasta 1 GB por archivo).
- Ver listado de archivos compartidos.
- Descargar archivos.
- Eliminar archivos desde la tabla.
- Eliminar tus propios mensajes del chat privado.
- Llamadas privadas entre amigos.
- Transmisión de pantalla con selección de 30/60/120 FPS y calidad 720p/1080p (según soporte del navegador/equipo).
- Animaciones/eventos en consola cuando ocurren acciones importantes (login, subida, chat, etc.).
- Fondo reactivo al mouse + interfaz con animaciones futuristas.
- Redes sociales del creador integradas en el footer.

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

### Ejecutar como programa (launcher)

```bash
python run_as_program.py
```

Este launcher abre la app automáticamente en el navegador para usarla como programa local.

## Nota de datos

- Los archivos se guardan en `uploads/`.
- Los usuarios, amistades y mensajes privados se guardan en `app.db` (SQLite).
- Si ya tienes archivos en `uploads/`, se mantienen sin borrarse.
- Límite de tamaño de subida: **1 GB** por archivo.

## Archivos importantes

- `schema.sql`: esquema de base de datos (usuarios, amistades, chat privado).
- `init_app_db.py`: genera/actualiza `app.db` usando el esquema.
- `templates/chat_panel.html`: bloque dedicado de la UI del chat privado.
- `run_as_program.py`: inicia el servidor y abre la app automáticamente.
- `templates/call_room.html` y `static/calls.js`: sala WebRTC para llamadas privadas y compartir pantalla.
