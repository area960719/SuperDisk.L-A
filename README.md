# SuperDisk.L-A
<div align="center">

# 💽 SuperDisk

**Clonación y rescate de discos a nivel de sector.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey)]()
[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/Status-En%20desarrollo-orange)]()

</div>

---

## 📖 ¿Qué es SuperDisk?

**SuperDisk** es una herramienta de escritorio para **clonar discos duros completos** (sanos o dañados), leer sectores crudos y generar un **mapa visual de salud** del disco. Está pensada para:

- 🔧 **Rescatar datos** de discos con sectores defectuosos (bad sectors).
- 💾 **Clonar discos** byte a byte, sin importar el sistema de archivos.
- 📀 **Crear imágenes RAW** de cualquier disco o partición.
- 🩺 **Diagnosticar** la salud de un disco antes de que falle del todo.

A diferencia de los programas de copia normales, SuperDisk **no entiende de archivos**: trabaja directamente con sectores de 512 bytes, lo que le permite leer discos dañados que Windows ni siquiera puede montar.

## ✨ Características principales

- 🔄 **Lectura sector por sector** con reintentos inteligentes (hasta 3 intentos por sector).
- 🗺️ **Mapa visual de sectores:** muestra en ASCII qué zonas del disco están sanas (`█`) y cuáles están dañadas (`X`).
- 🛡️ **Omisión segura de errores:** si un sector no se puede leer tras los reintentos, se marca como `bad` y se escribe ceros para no romper la estructura del clon.
- 📊 **Estadísticas en tiempo real:** sectores leídos, fallidos y reintentados.
- 🖼️ **Generación de imágenes RAW:** puedes clonar un disco a un archivo `.img` o `.raw`.
- 🔍 **Compatible con discos físicos y archivos imagen.**
- 📝 **Exportación del mapa a JSON** para análisis posterior.

## 🛠️ Tecnologías utilizadas

- **Lenguaje:** Python 3.10+
- **Acceso a disco crudo:** `ctypes` + Windows API (`CreateFileW`, `ReadFile`) / `os.pread` en Unix.
- **Interfaz:** [Tkinter] *(o el que uses)*
- **Empaquetado:** PyInstaller

## ⚠️ Requisitos y advertencias

> **Lee esto antes de usar SuperDisk con discos reales:**

1. **Requiere permisos de Administrador** en Windows (o `sudo` en Linux) para acceder a discos físicos.
2. **Es una herramienta peligrosa:** si eliges mal el disco destino, puedes sobrescribir datos irrecuperables. El programa pedirá **doble confirmación** antes de escribir.
3. **Prueba primero con un archivo imagen** antes de usar discos físicos reales.
4. **La clonación es byte a byte:** un disco de 500 GB tarda aproximadamente 2 horas a 80 MB/s.
5. **No reemplaza a herramientas profesionales** como `ddrescue` o `TestDisk`, pero es una alternativa didáctica y personalizable.

## 📂 Estructura del Proyecto

```text
SuperDisk/
├── main.py               # Punto de entrada
├── core/                 # Lógica del negocio
│   ├── __init__.py
│   ├── disk_reader.py    # Lee sectores crudos (con permisos admin)
│   ├── disk_engine.py    # Orquesta el clonado con reintentos
│   └── sector_map.py     # Genera el mapa visual de sectores
└── ui/                   # Interfaz gráfica
    ├── __init__.py
    └── window.py         # Ventana principal
