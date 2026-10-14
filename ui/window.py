# ui/window.py
import os
import sys
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from core.disk_engine import DiskCloneEngine
from core.sector_map import SectorMap


class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("SuperDisk 💽")
        self.root.geometry("950x720")
        self.root.minsize(800, 600)

        self.engine = None
        self.sector_map = {}

        self._build_ui()

    # ================= UI =================
    def _build_ui(self):
        # --- Cabecera ---
        header = tk.Frame(self.root, bg="#1e1e2e", height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="💽 SuperDisk", font=("Segoe UI", 20, "bold"),
                 bg="#1e1e2e", fg="#cdd6f4").pack(side="left", padx=20)
        tk.Label(header, text="Clonación y rescate de discos a nivel de sector",
                 font=("Segoe UI", 10), bg="#1e1e2e", fg="#a6adc8").pack(side="left", padx=10)

        # --- Configuración ---
        config = ttk.LabelFrame(self.root, text="📋 Configuración del clonado", padding=10)
        config.pack(fill="x", padx=10, pady=5)

        src_row = ttk.Frame(config); src_row.pack(fill="x", pady=3)
        ttk.Label(src_row, text="Origen:", width=12).pack(side="left")
        self.src_var = tk.StringVar()
        ttk.Entry(src_row, textvariable=self.src_var).pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(src_row, text="📁 Imagen...", command=self._pick_src_file).pack(side="left", padx=2)
        ttk.Button(src_row, text="💽 Disco...", command=self._pick_src_disk).pack(side="left", padx=2)

        dst_row = ttk.Frame(config); dst_row.pack(fill="x", pady=3)
        ttk.Label(dst_row, text="Destino:", width=12).pack(side="left")
        self.dst_var = tk.StringVar()
        ttk.Entry(dst_row, textvariable=self.dst_var).pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(dst_row, text="📁 Guardar como...", command=self._pick_dst_file).pack(side="left", padx=2)
        ttk.Button(dst_row, text="💽 Disco...", command=self._pick_dst_disk).pack(side="left", padx=2)

        opts = ttk.Frame(config); opts.pack(fill="x", pady=3)
        ttk.Label(opts, text="Reintentos:").pack(side="left")
        self.retries_var = tk.StringVar(value="3")
        ttk.Spinbox(opts, from_=1, to=20, textvariable=self.retries_var, width=5).pack(side="left", padx=5)
        self.zeros_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opts, text="Rellenar sectores dañados con ceros",
                        variable=self.zeros_var).pack(side="left", padx=15)

        # --- Botones de acción ---
        actions = ttk.Frame(self.root, padding=5)
        actions.pack(fill="x", padx=10)
        self.btn_start = ttk.Button(actions, text="🚀 Iniciar clonado", command=self.start_clone)
        self.btn_start.pack(side="left", padx=2)
        self.btn_stop = ttk.Button(actions, text="⏹ Detener", command=self.stop_clone, state="disabled")
        self.btn_stop.pack(side="left", padx=2)
        ttk.Button(actions, text="🔄 Ver discos del sistema", command=self._show_disks).pack(side="left", padx=2)

        # --- Progreso ---
        prog = ttk.LabelFrame(self.root, text="📊 Progreso", padding=10)
        prog.pack(fill="x", padx=10, pady=5)
        self.progress_bar = ttk.Progressbar(prog, orient="horizontal", mode="determinate")
        self.progress_bar.pack(fill="x", pady=5)
        self.status_var = tk.StringVar(value="Esperando...")
        ttk.Label(prog, textvariable=self.status_var, font=("Consolas", 9)).pack(anchor="w")

        # --- Mapa visual ---
        map_frame = ttk.LabelFrame(self.root,
                                   text="🗺️  Mapa de sectores  (█ = sano, X = dañado)",
                                   padding=5)
        map_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.map_text = tk.Text(map_frame, font=("Consolas", 7), wrap="char",
                                bg="#1e1e2e", fg="#a6e3a1", insertbackground="white")
        self.map_text.pack(fill="both", expand=True, side="left")
        sb = ttk.Scrollbar(map_frame, orient="vertical", command=self.map_text.yview)
        sb.pack(side="right", fill="y")
        self.map_text.configure(yscrollcommand=sb.set)

        # --- Resumen ---
        self.summary_var = tk.StringVar(value="")
        ttk.Label(self.root, textvariable=self.summary_var, font=("Segoe UI", 10, "bold"),
                  foreground="#89b4fa").pack(anchor="w", padx=15, pady=5)

        # --- Barra inferior ---
        bottom = tk.Frame(self.root, bg="#1e1e2e", height=25)
        bottom.pack(fill="x", side="bottom")
        tk.Label(bottom,
                 text="⚠️  Requiere ejecutar como Administrador para acceder a discos físicos",
                 bg="#1e1e2e", fg="#f9e2af", font=("Segoe UI", 8)).pack(side="left", padx=10)

    # ================= Archivos y discos =================
    def _pick_src_file(self):
        f = filedialog.askopenfilename(title="Seleccionar imagen de disco")
        if f:
            self.src_var.set(f)

    def _pick_dst_file(self):
        f = filedialog.asksaveasfilename(
            title="Guardar clon como...", defaultextension=".img",
            filetypes=[("Imagen RAW", "*.img"), ("Todos", "*.*")])
        if f:
            self.dst_var.set(f)

    def _pick_src_disk(self):
        DiskPickerDialog(self.root, "Disco origen", self.src_var)

    def _pick_dst_disk(self):
        DiskPickerDialog(self.root, "Disco destino (¡CUIDADO!)", self.dst_var)

    def _show_disks(self):
        txt = self._list_disks()
        DiskListDialog(self.root, "Discos detectados en el sistema", txt)

    def _list_disks(self):
        try:
            if sys.platform == "win32":
                return subprocess.check_output(
                    ["wmic", "diskdrive", "get", "Index,Model,Size,InterfaceType", "/format:list"],
                    text=True, stderr=subprocess.DEVNULL)
            else:
                return subprocess.check_output(
                    ["lsblk", "-o", "NAME,SIZE,MODEL,TYPE"],
                    text=True, stderr=subprocess.DEVNULL)
        except Exception as e:
            return f"No se pudieron listar discos: {e}"

    # ================= Clonado =================
    def start_clone(self):
        src = self.src_var.get().strip()
        dst = self.dst_var.get().strip()

        if not src or not dst:
            messagebox.showwarning("Faltan datos", "Selecciona origen y destino.")
            return

        if os.path.abspath(src) == os.path.abspath(dst):
            messagebox.showerror("Error", "Origen y destino no pueden ser iguales.")
            return

        if not messagebox.askyesno(
                "⚠️ Confirmar clonado",
                f"Origen:  {src}\nDestino: {dst}\n\n"
                "Esto SOBRESCRIBIRÁ el destino. ¿Continuar?"):
            return

        try:
            retries = int(self.retries_var.get())
        except ValueError:
            retries = 3

        self.sector_map = {}
        self.map_text.delete("1.0", "end")
        self.progress_bar["value"] = 0
        self.summary_var.set("")
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")

        def progress(done, total, bad, retried):
            self.root.after(0, lambda: self._update_progress(done, total, bad, retried))

        def worker():
            try:
                self.engine = DiskCloneEngine(on_progress=progress)
                smap, stats = self.engine.clone(src, dst,
                                                max_retries=retries,
                                                write_zeros=self.zeros_var.get())
                self.root.after(0, lambda: self._on_finished(smap, dst))
            except Exception as e:
                self.root.after(0, lambda: self._on_error(str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _update_progress(self, done, total, bad, retried):
        pct = (done / total * 100) if total else 0
        self.progress_bar["value"] = pct
        self.status_var.set(
            f"[{done:,}/{total:,}] {pct:.1f}%  |  dañados: {bad}  |  reintentos: {retried}")

    def _on_finished(self, smap, dst):
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")
        self.status_var.set("✅ Clonado completado.")
        self.progress_bar["value"] = 100

        m = SectorMap(smap)
        self.map_text.delete("1.0", "end")
        self.map_text.insert("1.0", m.to_ascii(columns=100))

        resumen = m.summary()
        self.summary_var.set(
            f"📊 Total: {resumen['total_sectores']:,}  |  "
            f"OK: {resumen['ok']:,}  |  "
            f"Dañados: {resumen['bad']:,}  |  "
            f"Salud: {resumen['salud_%']}%"
        )

        try:
            m.to_json(dst + ".map.json")
        except Exception:
            pass

        messagebox.showinfo("Listo",
                            f"Clonado completado.\n\nSalud del disco: {resumen['salud_%']}%")

    def _on_error(self, msg):
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")
        self.status_var.set("❌ Error")
        messagebox.showerror("Error", msg)

    def stop_clone(self):
        if self.engine:
            self.engine.stop()
            self.status_var.set("⏹ Deteniendo...")

    def run(self):
        self.root.mainloop()


# ================= Diálogos auxiliares =================
class DiskPickerDialog:
    def __init__(self, parent, title, result_var):
        self.result_var = result_var
        self.top = tk.Toplevel(parent)
        self.top.title(title)
        self.top.geometry("620x420")
        self.top.transient(parent)
        self.top.grab_set()

        ttk.Label(self.top, text=title, font=("Segoe UI", 12, "bold")).pack(pady=10)

        txt = tk.Text(self.top, font=("Consolas", 9), wrap="none")
        txt.pack(fill="both", expand=True, padx=10, pady=5)
        txt.insert("1.0", self._list())
        txt.config(state="disabled")

        row = ttk.Frame(self.top); row.pack(fill="x", padx=10, pady=5)
        ttk.Label(row, text="Ruta exacta:").pack(side="left")
        self.entry_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.entry_var).pack(side="left", fill="x", expand=True, padx=5)

        btns = ttk.Frame(self.top); btns.pack(pady=10)
        ttk.Button(btns, text="Aceptar", command=self._accept).pack(side="left", padx=5)
        ttk.Button(btns, text="Cancelar", command=self.top.destroy).pack(side="left", padx=5)

    def _list(self):
        try:
            if sys.platform == "win32":
                return subprocess.check_output(
                    ["wmic", "diskdrive", "get", "Index,Model,Size,InterfaceType", "/format:list"],
                    text=True, stderr=subprocess.DEVNULL)
            return subprocess.check_output(["lsblk", "-o", "NAME,SIZE,MODEL,TYPE"],
                                           text=True, stderr=subprocess.DEVNULL)
        except Exception as e:
            return f"Error: {e}"

    def _accept(self):
        val = self.entry_var.get().strip()
        if val:
            self.result_var.set(val)
        self.top.destroy()


class DiskListDialog:
    def __init__(self, parent, title, content):
        top = tk.Toplevel(parent)
        top.title(title)
        top.geometry("620x420")
        txt = tk.Text(top, font=("Consolas", 9), wrap="none")
        txt.pack(fill="both", expand=True, padx=10, pady=10)
        txt.insert("1.0", content)
        txt.config(state="disabled")
        ttk.Button(top, text="Cerrar", command=top.destroy).pack(pady=5)
