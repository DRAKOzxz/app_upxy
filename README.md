# app_upxy

Aplicación web para compartir archivos con registro de usuarios y chat común.

## Funciones

- Registro e inicio de sesión con usuario/contraseña.
- Subir archivos.
- Ver listado de archivos compartidos.
- Descargar archivos.
- Chat global para que todos los usuarios hablen entre sí.

## Requisitos

- Python 3.10+

## Ejecutar

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Luego abre: `http://localhost:5000`

## Nota de datos

- Los archivos se guardan en `uploads/`.
- Los usuarios y mensajes del chat se guardan en `app.db` (SQLite).
- Si ya tienes archivos en `uploads/`, se mantienen sin borrarse.
