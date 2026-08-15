"""TaskBar — gestor de tareas estilizado con persistencia local.

App de escritorio (tkinter): añade tareas, márcalas como completadas
con un clic, elimínalas y se guarda todo automáticamente en tasks.json
junto al ejecutable.
"""
import json
import os
import sys
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import font as tkfont, messagebox, ttk

APP_TITLE = "TaskBar"

# Paleta (tema oscuro)
BG = "#14161c"
BG_PANEL = "#1b1e26"
BG_INPUT = "#232733"
FG = "#e8eaf0"
FG_MUTED = "#8b93a3"
ACCENT = "#5eead4"
ACCENT_ACTIVE = "#2dd4bf"
DONE_FG = "#7f8b9d"
SELECT = "#2b3242"

CHECK_OFF = "\u2610"  # ☐
CHECK_ON = "\u2611"   # ☑

DAYS_ES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MONTHS_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
             "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def app_dir() -> Path:
    """Directorio de datos: junto al exe cuando está empaquetado."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


DATA_FILE = (Path(os.environ["TASKBAR_DATA_FILE"])
             if os.environ.get("TASKBAR_DATA_FILE")
             else app_dir() / "tasks.json")


def load_tasks() -> list:
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        tasks = []
        for item in data if isinstance(data, list) else []:
            if isinstance(item, dict):
                tasks.append({"text": str(item.get("text", "")).strip(),
                              "done": bool(item.get("done", False))})
            else:
                tasks.append({"text": str(item).strip(), "done": False})
        return [t for t in tasks if t["text"]]
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_tasks(tasks: list) -> None:
    tmp = DATA_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(DATA_FILE)


class TaskBarApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.tasks = load_tasks()
        root.title(APP_TITLE)
        root.configure(bg=BG)
        root.geometry("580x660")
        root.minsize(440, 500)
        self._center()
        self._fonts()
        self._build_style()
        self._build_ui()
        self.refresh()
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        root.bind("<Control-q>", lambda e: self.on_close())

    # ---------- helpers ----------

    def _center(self) -> None:
        self.root.update_idletasks()
        w, h = 580, 660
        x = (self.root.winfo_screenwidth() - w) // 2
        y = max(20, (self.root.winfo_screenheight() - h) // 3)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _fonts(self) -> None:
        family = "Segoe UI"
        self.f_title = tkfont.Font(family=family, size=16, weight="bold")
        self.f_sub = tkfont.Font(family=family, size=9)
        self.f_task = tkfont.Font(family=family, size=11)
        self.f_task_done = tkfont.Font(family=family, size=11, overstrike=1)

    def _build_style(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("Treeview",
                        background=BG_PANEL, fieldbackground=BG_PANEL,
                        foreground=FG, rowheight=38,
                        borderwidth=0, relief="flat")
        style.map("Treeview", background=[("selected", SELECT)],
                  foreground=[("selected", FG)])
        style.configure("Vertical.TScrollbar", background=BG_INPUT,
                        troughcolor=BG_PANEL, bordercolor=BG_PANEL,
                        arrowcolor=FG_MUTED, relief="flat")
        style.configure("TEntry", fieldbackground=BG_INPUT, foreground=FG,
                        bordercolor=BG_INPUT, padding=8, insertcolor=FG)
        style.map("TEntry", fieldbackground=[("focus", BG_INPUT)])
        style.configure("Accent.TButton", background=ACCENT, foreground="#0b0f14",
                        padding=(16, 9), font=self.f_task, borderwidth=0)
        style.map("Accent.TButton",
                  background=[("active", ACCENT_ACTIVE), ("pressed", ACCENT_ACTIVE)],
                  foreground=[("pressed", "#0b0f14")])
        style.configure("Ghost.TButton", background=BG_INPUT, foreground=FG_MUTED,
                        padding=(12, 8), font=self.f_sub, borderwidth=0)
        style.map("Ghost.TButton",
                  background=[("active", SELECT), ("pressed", SELECT)],
                  foreground=[("active", FG), ("pressed", FG)])
        style.configure("TProgressbar", background=ACCENT, troughcolor=BG_INPUT,
                        bordercolor=BG_INPUT, thickness=6)

    # ---------- UI ----------

    def _build_ui(self) -> None:
        top = tk.Frame(self.root, bg=BG)
        top.pack(fill="x", padx=18, pady=(16, 4))
        tk.Label(top, text="\u2713 TaskBar", bg=BG, fg=ACCENT,
                 font=self.f_title).pack(side="left")
        self.date_lbl = tk.Label(top, text="", bg=BG, fg=FG_MUTED, font=self.f_sub)
        self.date_lbl.pack(side="right")
        self._update_date()

        prog = tk.Frame(self.root, bg=BG)
        prog.pack(fill="x", padx=18, pady=(4, 12))
        self.progress = ttk.Progressbar(prog, style="TProgressbar", maximum=100)
        self.progress.pack(side="left", fill="x", expand=True)
        self.counter_lbl = tk.Label(prog, text="", bg=BG, fg=FG_MUTED,
                                    font=self.f_sub, width=14, anchor="e")
        self.counter_lbl.pack(side="right", padx=(10, 0))

        inp = tk.Frame(self.root, bg=BG)
        inp.pack(fill="x", padx=18, pady=(0, 12))
        self.entry_var = tk.StringVar()
        self.entry = tk.Entry(inp, textvariable=self.entry_var,
                              font=self.f_task, bg=BG_INPUT, fg=FG,
                              insertbackground=FG, relief="flat",
                              highlightthickness=2,
                              highlightbackground=BG_INPUT,
                              highlightcolor=ACCENT)
        self.entry.pack(side="left", fill="x", expand=True, ipady=8)
        self.entry.bind("<Return>", lambda e: self.add_task())
        ttk.Button(inp, text="Añadir", style="Accent.TButton",
                   command=self.add_task).pack(side="left", padx=(10, 0))

        list_frame = tk.Frame(self.root, bg=BG_PANEL)
        list_frame.pack(fill="both", expand=True, padx=18)
        self.tree = ttk.Treeview(list_frame, columns=("task",), show="",
                                 selectmode="browse", style="Treeview")
        self.tree.column("task", width=200, anchor="w", stretch=True)
        vsb = ttk.Scrollbar(list_frame, orient="vertical",
                            command=self.tree.yview, style="Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self.tree.tag_configure("done", foreground=DONE_FG, font=self.f_task_done)
        self.tree.tag_configure("pending", foreground=FG, font=self.f_task)
        self.tree.bind("<Button-1>", self.on_click)
        self.tree.bind("<Double-1>", lambda e: self.toggle_selected() or "break")
        self.tree.bind("<space>", lambda e: self.toggle_selected() or "break")
        self.tree.bind("<Delete>", lambda e: self.delete_selected() or "break")

        bottom = tk.Frame(self.root, bg=BG)
        bottom.pack(fill="x", padx=18, pady=(12, 14))
        ttk.Button(bottom, text="Marcar / desmarcar", style="Ghost.TButton",
                   command=self.toggle_selected).pack(side="left")
        ttk.Button(bottom, text="Eliminar", style="Ghost.TButton",
                   command=self.delete_selected).pack(side="left", padx=(8, 0))
        ttk.Button(bottom, text="Limpiar completadas", style="Ghost.TButton",
                   command=self.clear_done).pack(side="left", padx=(8, 0))
        tk.Label(bottom, text="Clic en \u2610 para completar · Doble clic alterna · Del elimina",
                 bg=BG, fg=FG_MUTED, font=self.f_sub).pack(side="right")

        self.entry.focus_set()

    def _update_date(self) -> None:
        now = datetime.now()
        text = f"{DAYS_ES[now.weekday()]}, {now.day} de {MONTHS_ES[now.month - 1]} de {now.year}"
        self.date_lbl.config(text=text.capitalize())

    # ---------- lógica ----------

    def refresh(self) -> None:
        self.tree.delete(*self.tree.get_children())
        for i, t in enumerate(self.tasks):
            glyph = CHECK_ON if t["done"] else CHECK_OFF
            tag = "done" if t["done"] else "pending"
            self.tree.insert("", "end", iid=str(i),
                             values=(f"{glyph}  {t['text']}",), tags=(tag,))
        done = sum(1 for t in self.tasks if t["done"])
        total = len(self.tasks)
        pct = int(done / total * 100) if total else 0
        self.counter_lbl.config(text=f"{done}/{total}  \u00b7  {pct}%")
        self.progress["value"] = pct
        self.save()

    def add_task(self) -> None:
        text = self.entry_var.get().strip()
        if not text:
            return
        self.tasks.append({"text": text, "done": False})
        self.entry_var.set("")
        self.refresh()
        self.tree.see(str(len(self.tasks) - 1))
        self.entry.focus_set()

    def on_click(self, event) -> None:
        # Clic sobre el área del checkbox (borde izquierdo de la fila)
        if event.x < 36:
            iid = self.tree.identify_row(event.y)
            if iid:
                self.toggle_task(iid)

    def toggle_task(self, iid: str) -> None:
        idx = int(iid)
        if 0 <= idx < len(self.tasks):
            self.tasks[idx]["done"] = not self.tasks[idx]["done"]
            self.refresh()

    def toggle_selected(self, _event=None):
        sel = self.tree.selection()
        if sel:
            self.toggle_task(sel[0])

    def delete_selected(self, _event=None):
        sel = self.tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        if 0 <= idx < len(self.tasks):
            del self.tasks[idx]
            self.refresh()

    def clear_done(self):
        remaining = [t for t in self.tasks if not t["done"]]
        removed = len(self.tasks) - len(remaining)
        if removed and messagebox.askyesno(
                APP_TITLE, f"¿Eliminar {removed} tarea(s) completada(s)?"):
            self.tasks = remaining
            self.refresh()

    def save(self) -> None:
        try:
            save_tasks(self.tasks)
        except OSError as e:
            messagebox.showwarning(APP_TITLE, f"No se pudo guardar: {e}")

    def on_close(self) -> None:
        self.save()
        self.root.destroy()


def run_selftest() -> None:
    """Autotest real: añadir, alternar, guardar, recargar y comprobar la UI."""
    root = tk.Tk()
    app = TaskBarApp(root)
    results = []

    def check(name: str, cond: bool, detail: str = "") -> None:
        results.append((name, cond, detail))
        print(("PASS" if cond else "FAIL"), name, detail)

    # 1. Añadir dos tareas por el mismo camino que el usuario (entry + Enter)
    for text in ["Comprar leche", "Llamar al dentista"]:
        app.entry_var.set(text)
        app.add_task()
    children = app.tree.get_children()
    check("2 tareas en la lista", len(children) == 2, f"got {len(children)}")
    visible = [app.tree.item(i, "values") for i in children]
    check("tarea 1 visible con texto",
          visible[0] and CHECK_OFF in visible[0][0] and "Comprar leche" in visible[0][0],
          str(visible[0]))
    check("tarea 2 visible con texto",
          visible[1] and CHECK_OFF in visible[1][0] and "Llamar al dentista" in visible[1][0],
          str(visible[1]))

    # 2. Completar la primera (clic en el checkbox = toggle_task)
    app.toggle_task(children[0])
    visible = [app.tree.item(i, "values") for i in app.tree.get_children()]
    check("tarea 1 marcada ☑", CHECK_ON in visible[0][0], str(visible[0]))
    check("contador 1/2 · 50%", "1/2" in app.counter_lbl.cget("text")
          and "50%" in app.counter_lbl.cget("text"),
          app.counter_lbl.cget("text"))

    # 3. Persistencia: el archivo existe y tiene el estado correcto
    app.save()
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    check("tasks.json guardado", DATA_FILE.exists() and len(data) == 2,
          str(DATA_FILE))
    check("done=true persistido", data[0]["done"] is True
          and data[0]["text"] == "Comprar leche", str(data[0]))

    # 4. Recarga en una instancia nueva (como al reabrir la app)
    root.destroy()
    root2 = tk.Tk()
    app2 = TaskBarApp(root2)
    children2 = app2.tree.get_children()
    check("recarga: 2 tareas", len(children2) == 2)
    visible2 = [app2.tree.item(i, "values") for i in children2]
    check("recarga: texto y estado intactos",
          CHECK_ON in visible2[0][0] and "Comprar leche" in visible2[0][0]
          and CHECK_OFF in visible2[1][0],
          str(visible2))
    root2.destroy()

    failed = [r for r in results if not r[1]]
    print("ALL TESTS PASSED" if not failed else f"{len(failed)} TEST(S) FAILED")
    raise SystemExit(1 if failed else 0)


def main() -> None:
    if "--test" in sys.argv:
        run_selftest()
        return
    root = tk.Tk()
    app = TaskBarApp(root)
    if "--smoke-test" in sys.argv:
        app.entry_var.set("Tarea de prueba")
        app.add_task()
        app.toggle_task(str(len(app.tasks) - 1))
        root.after(1200, root.destroy)
        root.mainloop()
        print("SMOKE_OK")
        return
    root.mainloop()


if __name__ == "__main__":
    main()
