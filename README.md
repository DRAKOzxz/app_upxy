# app_upxy

Aplicación web simple para compartir archivos en una red/local:

- Subir archivos.
- Ver listado de archivos compartidos.
- Descargar archivos.

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

## Nota

Los archivos se guardan en la carpeta `uploads/` del proyecto.
