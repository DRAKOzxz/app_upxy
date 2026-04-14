# 🚀 app_upxy — Comparte archivos + Chat en tiempo real

<p align="center">
  <img src="./banner.png" alt="app_upxy banner" width="100%">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/status-active-success?style=for-the-badge&color=00C853">
  <img src="https://img.shields.io/badge/python-3.10+-blue?style=for-the-badge">
  <img src="https://img.shields.io/badge/auth-enabled-green?style=for-the-badge">
  <img src="https://img.shields.io/badge/chat-real--time-purple?style=for-the-badge">
  <img src="https://img.shields.io/badge/database-sqlite-lightgrey?style=for-the-badge">
  <img src="https://img.shields.io/badge/license-MIT-purple?style=for-the-badge">
</p>

<p align="center">
  ⚡ Comparte archivos + chatea en tiempo real dentro de tu red
</p>

---

## 🔥 ¿Qué es app_upxy?

**app_upxy** es una aplicación web que permite:

📁 Compartir archivos  
💬 Chatear en tiempo real  
🔐 Gestionar usuarios  

Todo dentro de tu red local, sin depender de servicios externos.

---

## 🚀 Nuevas mejoras

✨ Sistema completo de autenticación  
💬 Chat global persistente  
🔐 Seguridad básica con hash de contraseñas  
🗄️ Base de datos SQLite integrada  

---

## 🎯 Funcionalidades

### 🔐 Autenticación
- Registro de usuarios
- Login / Logout
- Protección de rutas (solo usuarios autenticados)

### 📁 Archivos
- 📤 Subir archivos
- 📄 Ver archivos disponibles
- 📥 Descargar archivos
- 📂 Persistencia en `/uploads` (no se eliminan)

### 💬 Chat global
- Chat en tiempo real entre usuarios
- Mensajes guardados en base de datos
- Comunicación simple y directa

---

## 🖥️ Interfaz

- 🧭 Barra de sesión (usuario activo)
- 📁 Panel de archivos
- 💬 Panel de chat
- 🔐 Vista de autenticación (login/register)

---

## ⚡ Instalación rápida

```bash
python -m venv .venv

# Activar entorno
source .venv/bin/activate   # Linux / Mac
.venv\Scripts\activate      # Windows

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar app
python app.py
