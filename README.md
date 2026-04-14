# App de archivos compartidos

Aplicación web simple para que las personas puedan:

- Ver archivos que otros subieron.
- Descargar archivos disponibles.
- Subir sus propios archivos.

## Requisitos

- Python 3.10+

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Ejecutar

```bash
python app.py
```

Luego abre `http://localhost:5000`.

## Notas

- La app guarda metadatos en SQLite (`files.db`).
- Los archivos se guardan en la carpeta `uploads/`.
- Tamaño máximo por archivo: 50 MB.
