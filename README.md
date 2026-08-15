# TaskBar App

App de escritorio en Tkinter para Windows que añade una barra flotante sobre
el escritorio con accesos rápidos (estilo dock), con tema oscuro, color de
acento y barra de progreso. Se distribuye como `.exe` (PyInstaller).

## ⬇️ Descargar y ejecutar (sin instalar nada)

**[Descarga el .exe desde Releases](https://github.com/Nando2392/taskbar-app/releases/latest)**
y haz doble clic. Funciona en Windows 10/11 sin Python ni dependencias.

> El .exe se compila automáticamente con GitHub Actions al publicar una versión
> (tag `v*`); también puedes lanzar el build a mano desde la pestaña Actions →
> *build-exe* → *Run workflow*.

## Estructura

| Archivo | Rol |
|---|---|
| `taskbar.py` | App principal (ventana, botones, arrastre) |
| `make_icon.py` | Genera `icon.ico` |
| `smoke_check.py` | Smoke test de la app |
| `verify_exe.py` | Verifica el `.exe` empaquetado |
| `TaskBar.spec` | Spec de PyInstaller |

## Requisitos

- Python 3.11+
- Pillow

## Ejecutar

```bash
python taskbar.py
```

## Build del .exe

```bash
pyinstaller --noconfirm --clean TaskBar.spec
```

## Verificación

```bash
python smoke_check.py
python verify_exe.py
```
