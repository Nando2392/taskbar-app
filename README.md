# TaskBar App

App de escritorio en Tkinter para Windows que añade una barra flotante sobre
el escritorio con accesos rápidos (estilo dock), con tema oscuro, color de
acento y barra de progreso. Se distribuye como `.exe` (PyInstaller).

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
