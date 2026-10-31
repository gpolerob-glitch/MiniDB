"""GUI de escritorio MiniDB Studio (CustomTkinter + tabla ttk)."""
from __future__ import annotations

import os
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime
from tkinter import ttk
import tkinter as tk

import customtkinter as ctk
from dotenv import load_dotenv

from .nosql_manager import MongoManager
from .result_manager import QueryResult
from .sql_manager import SQLManager

load_dotenv()

BG = "#0B1220"
CARD = "#152238"
CARD_2 = "#192A43"
BORDER = "#263A55"
TEXT = "#F0F5FC"
MUTED = "#9EADC3"
ACCENT = "#18B6A4"
ACCENT_HOVER = "#119989"
SUCCESS = "#66D6A2"
ERROR = "#FF9B9B"
FONT = "Segoe UI"

EXAMPLES = {
    "sql": {
        "Crear tabla (DDL)": """CREATE TABLE IF NOT EXISTS estudiantes (\n    id SERIAL PRIMARY KEY,\n    nombre VARCHAR(100) NOT NULL,\n    carrera VARCHAR(100) NOT NULL\n);""",
        "Insertar (DML)": "INSERT INTO estudiantes (nombre, carrera) VALUES ('Ana', 'Sistemas');",
        "Consultar (DML)": "SELECT * FROM estudiantes ORDER BY id;",
        "Modificar tabla (DDL)": "ALTER TABLE estudiantes ADD COLUMN IF NOT EXISTS edad INTEGER;",
        "Actualizar (DML)": "UPDATE estudiantes SET carrera = 'Ingeniería en Sistemas' WHERE nombre = 'Ana';",
        "Eliminar dato (DML)": "DELETE FROM estudiantes WHERE nombre = 'Ana';",
        "Eliminar tabla (DDL)": "DROP TABLE IF EXISTS estudiantes;",
        "Consultar versión": "SELECT version();",
    },
    "mongo": {
        "Crear colección": 'db.createCollection("estudiantes")',
        "Insertar documento": 'db.estudiantes.insertOne({nombre: "Ana", carrera: "Sistemas", edad: 19})',
        "Consultar documentos": "db.estudiantes.find({})",
        "Actualizar documento": 'db.estudiantes.updateOne({nombre: "Ana"}, {$set: {carrera: "Ingeniería en Sistemas"}})',
        "Eliminar documento": 'db.estudiantes.deleteOne({nombre: "Ana"})',
        "Crear índice": "db.estudiantes.createIndex({nombre: 1})",
        "Eliminar índice": 'db.estudiantes.dropIndex("nombre_1")',
        "Listar colecciones": "db.listCollections()",
        "Eliminar colección": "db.estudiantes.drop()",
        "Formato JSON": '{\n  "operation": "find",\n  "collection": "estudiantes",\n  "filter": {},\n  "limit": 50\n}',
    },
}


class MiniDBApp(ctk.CTk):
    """Interfaz con controles aislados de las operaciones de red.

    La única tarea concurrente se ejecuta en ThreadPoolExecutor; los widgets
    siempre se actualizan en el hilo principal mediante sondeo con after().
    """

    def __init__(self) -> None:
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        super().__init__()
        self.title("MiniDB Studio · SQL + NoSQL")
        self.geometry("1240x820")
        self.minsize(980, 680)
        self.configure(fg_color=BG)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.sql = SQLManager()
        self.mongo = MongoManager()
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="minidb")
        self._pending: tuple[Future, callable] | None = None
        self.controls: dict[str, dict] = {}
        self._buttons: list[ctk.CTkButton] = []
        self._closed = False

        self._configure_tree_style()
        self._make_header()
        self.tabview = ctk.CTkTabview(
            self, fg_color=BG, segmented_button_fg_color=CARD,
            segmented_button_selected_color=ACCENT,
            segmented_button_selected_hover_color=ACCENT_HOVER,
            segmented_button_unselected_color=CARD,
            segmented_button_unselected_hover_color=CARD_2,
            text_color=TEXT, corner_radius=14,
        )
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 8))
        for kind, label in (("sql", "PostgreSQL · SQL"), ("mongo", "MongoDB · NoSQL")):
            tab = self.tabview.add(label)
            self._make_tab(tab, kind)
        ctk.CTkLabel(self, text="MINIDB STUDIO  •  Ctrl + Enter: ejecutar  •  Máximo 500 filas por consulta",
                     text_color=MUTED, font=(FONT, 11)).grid(row=2, column=0, pady=(0, 9))
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _configure_tree_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("DB.Treeview", background=CARD, foreground=TEXT,
                        fieldbackground=CARD, rowheight=30, font=(FONT, 11), borderwidth=0)
        style.configure("DB.Treeview.Heading", background=CARD_2,
                        foreground=TEXT, font=(FONT, 11, "bold"), padding=(12, 9), borderwidth=0)
        style.map("DB.Treeview", background=[("selected", "#235A73")], foreground=[("selected", "#FFFFFF")])
        style.map("DB.Treeview.Heading", background=[("active", BORDER)])
        style.configure("DB.Vertical.TScrollbar", gripcount=0, background=BORDER,
                        troughcolor=CARD, arrowcolor=TEXT)
        style.configure("DB.Horizontal.TScrollbar", gripcount=0, background=BORDER,
                        troughcolor=CARD, arrowcolor=TEXT)

    def _make_header(self) -> None:
        head = ctk.CTkFrame(self, fg_color=BG, corner_radius=0, height=84)
        head.grid(row=0, column=0, sticky="ew", padx=24, pady=(14, 8))
        head.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(head, text="◈  MiniDB Studio", text_color=TEXT,
                     font=(FONT, 28, "bold")).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(head, text="Tu mini IDE educativo para bases de datos relacionales y documentales",
                     text_color=MUTED, font=(FONT, 13)).grid(row=1, column=0, sticky="w", pady=(2, 0))
        ctk.CTkLabel(head, text="PROYECTO ACADÉMICO  ·  PYTHON", text_color=ACCENT,
                     font=(FONT, 11, "bold")).grid(row=0, column=1, rowspan=2, sticky="e")

    def _make_tab(self, tab: ctk.CTkFrame, kind: str) -> None:
        tab.configure(fg_color=BG)
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(0, weight=1)
        self.controls[kind] = {}
        self._make_sidebar(tab, kind)
        self._make_workspace(tab, kind)

    def _make_sidebar(self, tab: ctk.CTkFrame, kind: str) -> None:
        side = ctk.CTkScrollableFrame(tab, width=250, fg_color=CARD,
                                      corner_radius=12, scrollbar_button_color=BORDER)
        side.grid(row=0, column=0, sticky="ns", padx=(0, 12), pady=5)
        ctk.CTkLabel(side, text="01  CONEXIÓN", text_color=ACCENT,
                     font=(FONT, 12, "bold")).pack(anchor="w", padx=12, pady=(14, 9))
        entries: dict[str, ctk.CTkEntry] = {}
        if kind == "sql":
            specs = [
                ("Servidor", "host", os.getenv("PG_HOST", "localhost"), False),
                ("Puerto", "port", os.getenv("PG_PORT", "15432"), False),
                ("Base de datos", "dbname", os.getenv("PG_DB", "miniide"), False),
                ("Usuario", "user", os.getenv("PG_USER", "ide_user"), False),
                ("Contraseña", "password", os.getenv("PG_PASSWORD", "ide_demo_2026"), True),
            ]
        else:
            specs = [
                ("URI de MongoDB", "uri", os.getenv("MONGO_URI", "mongodb://ide_admin:ide_demo_2026@localhost:27018/?authSource=admin"), False),
                ("Base de datos", "database", os.getenv("MONGO_DB", "miniide"), False),
            ]
        for label, name, initial, secret in specs:
            ctk.CTkLabel(side, text=label, text_color=MUTED,
                         font=(FONT, 12)).pack(anchor="w", padx=12, pady=(7, 1))
            entry = ctk.CTkEntry(side, fg_color=BG, border_color=BORDER,
                                 text_color=TEXT, height=36, font=(FONT, 12), show="●" if secret else "")
            entry.pack(fill="x", padx=12)
            entry.insert(0, initial)
            entries[name] = entry
        self.controls[kind]["entries"] = entries
        status = ctk.CTkLabel(side, text="●  Desconectado", text_color=MUTED,
                              font=(FONT, 12, "bold"), wraplength=220, justify="left")
        status.pack(anchor="w", padx=12, pady=(16, 7))
        self.controls[kind]["status"] = status

        connect = ctk.CTkButton(side, text="Conectar", fg_color=ACCENT,
                                hover_color=ACCENT_HOVER, text_color=BG,
                                font=(FONT, 13, "bold"), height=37,
                                command=lambda k=kind: self._connect(k))
        connect.pack(fill="x", padx=12, pady=(0, 8))
        disconnect = ctk.CTkButton(side, text="Desconectar", fg_color=CARD_2,
                                   hover_color=BORDER, text_color=TEXT,
                                   height=35, command=lambda k=kind: self._disconnect(k))
        disconnect.pack(fill="x", padx=12)
        self._buttons.extend([connect, disconnect])

        ctk.CTkFrame(side, height=1, fg_color=BORDER).pack(fill="x", padx=12, pady=19)
        ctk.CTkLabel(side, text="02  EJEMPLOS", text_color=ACCENT,
                     font=(FONT, 12, "bold")).pack(anchor="w", padx=12, pady=(0, 9))
        names = list(EXAMPLES[kind])
        selected = tk.StringVar(value=names[0])
        menu = ctk.CTkOptionMenu(side, values=names, variable=selected,
                                 fg_color=CARD_2, button_color=BORDER,
                                 button_hover_color="#355272", text_color=TEXT,
                                 font=(FONT, 12), height=36)
        menu.pack(fill="x", padx=12)
        ctk.CTkButton(side, text="Cargar ejemplo en editor", fg_color=CARD_2,
                      hover_color=BORDER, text_color=TEXT, height=35,
                      command=lambda k=kind, v=selected: self._load_example(k, v.get())
                      ).pack(fill="x", padx=12, pady=(8, 13))
        ctk.CTkLabel(side, text=("Puerto Docker: 15432" if kind == "sql" else "Puerto Docker: 27018")
                     + "\nSolo para entorno local de pruebas.",
                     text_color=MUTED, font=(FONT, 11), justify="left").pack(anchor="w", padx=12, pady=(3, 16))

    def _make_workspace(self, tab: ctk.CTkFrame, kind: str) -> None:
        work = ctk.CTkFrame(tab, fg_color=BG, corner_radius=0)
        work.grid(row=0, column=1, sticky="nsew", pady=5)
        work.grid_columnconfigure(0, weight=1)
        work.grid_rowconfigure(1, weight=1)

        editor_card = ctk.CTkFrame(work, fg_color=CARD, corner_radius=12)
        editor_card.grid(row=0, column=0, sticky="nsew", pady=(0, 11))
        editor_card.grid_columnconfigure(0, weight=1)
        editor_card.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(editor_card, text="03  EDITOR DE CONSULTAS", text_color=ACCENT,
                     font=(FONT, 12, "bold")).grid(row=0, column=0, sticky="w", padx=17, pady=(13, 8))
        editor = ctk.CTkTextbox(editor_card, fg_color=BG, text_color="#D4E7F8",
                                font=("Consolas", 14), border_color=BORDER,
                                border_width=1, corner_radius=9, wrap="none", height=185)
        editor.grid(row=1, column=0, sticky="nsew", padx=16)
        editor.insert("1.0", EXAMPLES[kind]["Consultar (DML)" if kind == "sql" else "Consultar documentos"])
        editor.bind("<Control-Return>", lambda event, k=kind: self._shortcut_execute(k))
        self.controls[kind]["editor"] = editor
        actions = ctk.CTkFrame(editor_card, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="ew", padx=16, pady=11)
        ctk.CTkLabel(actions, text=("SQL · PostgreSQL" if kind == "sql" else "JSON / mongosh básico"),
                     text_color=MUTED, font=(FONT, 11)).pack(side="left")
        execute = ctk.CTkButton(actions, text="▶  Ejecutar  (Ctrl+Enter)",
                                fg_color=ACCENT, hover_color=ACCENT_HOVER,
                                text_color=BG, font=(FONT, 12, "bold"),
                                width=202, height=36, command=lambda k=kind: self._execute(k))
        execute.pack(side="right")
        self._buttons.append(execute)
        ctk.CTkButton(actions, text="Limpiar", width=77, height=36, fg_color=CARD_2,
                      hover_color=BORDER, command=lambda k=kind: self._clear(k)
                      ).pack(side="right", padx=(0, 9))

        results_card = ctk.CTkFrame(work, fg_color=CARD, corner_radius=12)
        results_card.grid(row=1, column=0, sticky="nsew", pady=(0, 11))
        results_card.grid_columnconfigure(0, weight=1)
        results_card.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(results_card, text="04  RESULTADOS", text_color=ACCENT,
                     font=(FONT, 12, "bold")).grid(row=0, column=0, sticky="w", padx=17, pady=(12, 7))
        table_box = tk.Frame(results_card, bg=CARD, highlightthickness=0)
        table_box.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 12))
        table_box.grid_columnconfigure(0, weight=1)
        table_box.grid_rowconfigure(0, weight=1)
        tree = ttk.Treeview(table_box, columns=(), show="headings", style="DB.Treeview")
        tree.grid(row=0, column=0, sticky="nsew")
        scroll_y = ttk.Scrollbar(table_box, orient="vertical", command=tree.yview,
                                 style="DB.Vertical.TScrollbar")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x = ttk.Scrollbar(table_box, orient="horizontal", command=tree.xview,
                                 style="DB.Horizontal.TScrollbar")
        scroll_x.grid(row=1, column=0, sticky="ew")
        tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        self.controls[kind]["tree"] = tree

        console_card = ctk.CTkFrame(work, fg_color=CARD, corner_radius=12)
        console_card.grid(row=2, column=0, sticky="ew")
        console_card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(console_card, text="05  CONSOLA / ESTADO", text_color=ACCENT,
                     font=(FONT, 12, "bold")).grid(row=0, column=0, sticky="w", padx=17, pady=(10, 3))
        log = ctk.CTkTextbox(console_card, fg_color=CARD, text_color=MUTED,
                             font=("Consolas", 11), height=79, wrap="word", border_width=0)
        log.grid(row=1, column=0, sticky="ew", padx=13, pady=(0, 9))
        log.insert("1.0", "Lista para conectar y ejecutar comandos.\n")
        log.configure(state="disabled")
        self.controls[kind]["log"] = log

    def _shortcut_execute(self, kind: str) -> str:
        self._execute(kind)
        return "break"

    def _load_example(self, kind: str, name: str) -> None:
        self._set_editor(kind, EXAMPLES[kind][name])

    def _set_editor(self, kind: str, value: str) -> None:
        editor = self.controls[kind]["editor"]
        editor.delete("1.0", "end")
        editor.insert("1.0", value)
        editor.focus_set()

    def _clear(self, kind: str) -> None:
        self._set_editor(kind, "")

    def _connect(self, kind: str) -> None:
        entries = self.controls[kind]["entries"]
        values = {name: entry.get() for name, entry in entries.items()}
        if kind == "sql":
            try:
                values["port"] = int(values["port"])
                if not (1 <= values["port"] <= 65535):
                    raise ValueError()
            except ValueError:
                self._fail(kind, "El puerto debe ser un número entre 1 y 65535.")
                return
            task = lambda: self.sql.connect(**values)
        else:
            task = lambda: self.mongo.connect(**values)

        def finished(message: str) -> None:
            self.controls[kind]["status"].configure(text="●  Conectado", text_color=SUCCESS)
            self._log(kind, message, True)
        self._start(kind, task, finished)

    def _disconnect(self, kind: str) -> None:
        manager = self.sql if kind == "sql" else self.mongo
        def task() -> str:
            manager.disconnect()
            return "Conexión cerrada."
        def finished(message: str) -> None:
            self.controls[kind]["status"].configure(text="●  Desconectado", text_color=MUTED)
            self._log(kind, message, True)
        self._start(kind, task, finished)

    def _execute(self, kind: str) -> None:
        source = self.controls[kind]["editor"].get("1.0", "end-1c")
        if not source.strip():
            self._fail(kind, "Escriba una instrucción antes de ejecutar.")
            return
        manager = self.sql if kind == "sql" else self.mongo
        self._start(kind, lambda: manager.execute(source), lambda r: self._show_result(kind, r))

    def _start(self, kind: str, func: callable, on_success: callable) -> None:
        if self._pending is not None:
            self._log(kind, "Otra operación está en proceso.", False)
            return
        self._set_busy(True)
        future = self.executor.submit(func)
        self._pending = (future, lambda result, error: self._finish(kind, on_success, result, error))
        self.after(90, self._poll)

    def _poll(self) -> None:
        if self._closed or self._pending is None:
            return
        future, cb = self._pending
        if not future.done():
            self.after(90, self._poll)
            return
        self._pending = None
        self._set_busy(False)
        try:
            cb(future.result(), None)
        except Exception as error:
            cb(None, error)

    def _finish(self, kind: str, callback: callable, result: object, error: Exception | None) -> None:
        if error is not None:
            # Nunca imprimir URI ni contraseña: los errores se muestran sin datos de conexión.
            msg = str(error)
            entries = self.controls[kind]["entries"]
            for secret_name in ("password", "uri"):
                if secret_name in entries:
                    secret = entries[secret_name].get()
                    if secret:
                        msg = msg.replace(secret, "[oculto]")
            self._fail(kind, msg)
            manager = self.sql if kind == "sql" else self.mongo
            if not manager.is_connected:
                self.controls[kind]["status"].configure(text="●  Desconectado", text_color=MUTED)
            return
        callback(result)

    def _set_busy(self, busy: bool) -> None:
        for btn in self._buttons:
            btn.configure(state="disabled" if busy else "normal")

    def _show_result(self, kind: str, result: QueryResult) -> None:
        tree = self.controls[kind]["tree"]
        tree.delete(*tree.get_children())
        # Treeview trata algunos nombres reservados especialmente; identificadores internos únicos.
        identifiers = [f"col_{i}" for i in range(len(result.columns))]
        tree.configure(columns=identifiers)
        for i, heading in enumerate(result.columns):
            col_id = identifiers[i]
            tree.heading(col_id, text=heading)
            tree.column(col_id, width=max(130, min(260, len(heading) * 13 + 75)), stretch=True, anchor="w")
        for row in result.rows:
            tree.insert("", "end", values=row)
        suffix = " · Resultados limitados para proteger la interfaz." if result.truncated else ""
        self._log(kind, result.message + suffix, True)

    def _log(self, kind: str, message: str, success: bool) -> None:
        log = self.controls[kind]["log"]
        log.configure(state="normal")
        timestamp = datetime.now().strftime("%H:%M:%S")
        log.insert("end", f"[{timestamp}] {'OK' if success else 'ERROR'} · {message}\n")
        log.see("end")
        log.configure(state="disabled")

    def _fail(self, kind: str, message: str) -> None:
        self._log(kind, message, False)

    def _on_close(self) -> None:
        self._closed = True
        self.executor.shutdown(wait=False, cancel_futures=True)
        if self._pending is None:
            self.sql.disconnect()
            self.mongo.disconnect()
        self.destroy()
