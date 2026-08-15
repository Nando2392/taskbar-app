"""Verificación E2E del exe TaskBar: lanza el exe, captura su render real con
PrintWindow (aunque otra ventana lo tape), comprueba que las tareas se ven
con texto, y restaura los datos del usuario. Uso: python verify_exe.py"""
import os
import subprocess
import sys
import time
from pathlib import Path

APP_DIR = Path(r"C:\Users\fjmn2\Dev\taskbar-app")
DIST = APP_DIR / "dist"
EXE = DIST / "TaskBar.exe"
DATA = DIST / "tasks.json"
BACKUP = DIST / "tasks.json.verifybak"
PNG = APP_DIR / "verify.png"

def powershell(args):
    return subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", *args],
        capture_output=True, text=True, timeout=120)

def main() -> int:
    if not EXE.exists():
        print("FAIL: no existe dist/TaskBar.exe"); return 1

    # 1. Semilla con las tareas reales del usuario (respaldo previo)
    BACKUP.write_text(DATA.read_text(encoding="utf-8"), encoding="utf-8")
    DATA.write_text('[{"text": "llamar a labora", "done": false}, {"text": "hola", "done": true}]', encoding="utf-8")

    # 2. Lanzar el exe
    proc = subprocess.Popen([str(EXE)], cwd=str(DIST))
    ok = False
    try:
        time.sleep(7)
        # 3. Captura fiel (PrintWindow) + escaneo de píxeles de texto en la zona de filas
        r = powershell([str(APP_DIR / "capture_print.ps1"), str(PNG)])
        out = r.stdout
        print(out.strip())
        # 4. Escaneo fino de texto
        r2 = powershell([str(APP_DIR / "scan_rows.ps1"), str(PNG), str(APP_DIR / "scan_dummy.png")])
        for line in r2.stdout.splitlines():
            if "verify.png" in line or "print_capture" in line:
                print(line.strip())
        # 5. Verdict: buscar evidencia de texto y colores correctos
        if "PrintWindow ok: True" in out and "boton-add" in out and "RGB(94,234,212)" in out:
            ok = True
        else:
            print("FAIL: captura o colores incorrectos")
            return 1
    finally:
        subprocess.run(["powershell", "-NoProfile", "-Command",
                        "Stop-Process -Name TaskBar -Force -ErrorAction SilentlyContinue"],
                       capture_output=True)
        # 6. Restaurar los datos reales del usuario
        DATA.write_text(BACKUP.read_text(encoding="utf-8"), encoding="utf-8")
        BACKUP.unlink(missing_ok=True)

    # 7. Escaneo de texto sobre la captura (control del render de las filas)
    r3 = powershell([str(APP_DIR / "scan_text.ps1"), str(PNG)])
    print(r3.stdout.strip())
    total = 0
    for line in r3.stdout.splitlines():
        if "total texto" in line:
            total = int(line.split("total texto:")[1].strip())
    if total > 500:
        print(f"PASS: el exe renderiza las tareas con texto visible ({total} px de texto)")
        return 0
    print(f"FAIL: no se detectó texto en las filas ({total} px)")
    return 1

if __name__ == "__main__":
    sys.exit(main())
