"""
FOTO SUPREMA - lanzador (es lo que se convierte en FotoSuprema.exe)

- Lleva Python, Pillow y todo lo necesario DENTRO del .exe: no hay que instalar nada.
- Al abrirse mira en GitHub si hay una versión nueva del código (version.json).
  Si la hay, la descarga sola y abre la app ya actualizada.
- Si no hay internet, abre la última versión descargada (o la que viene dentro del .exe).
- Si algún día una actualización necesita un .exe nuevo, también se lo baja y se reemplaza solo.

HECHO POR @BYALVARO__
"""
import os
import sys
import json
import time
import shutil
import tempfile
import threading
import subprocess
import importlib.util
import urllib.request
import tkinter as tk

# --- imports que la app necesita: así PyInstaller los mete dentro del .exe ---
import queue, re, datetime, ctypes  # noqa: F401,E401
from tkinter import ttk, filedialog, messagebox  # noqa: F401
from PIL import Image, ImageOps, ImageTk, ImageDraw  # noqa: F401
try:
    import pillow_heif  # noqa: F401
except Exception:
    pass

# ======================================================================
# CONFIGURACIÓN DEL REPOSITORIO (cámbialo si el repo se llama distinto)
# ======================================================================
USUARIO_GITHUB = "ByAlvaroo"
REPOSITORIO = "foto-suprema"
RAMA = "main"
VERSION_LANZADOR = 1   # súbelo solo si cambias ESTE archivo (lanzador.py)

RAW = f"https://raw.githubusercontent.com/{USUARIO_GITHUB}/{REPOSITORIO}/{RAMA}/"
EXE_ULTIMO = f"https://github.com/{USUARIO_GITHUB}/{REPOSITORIO}/releases/latest/download/FotoSuprema.exe"

BASE_DATOS = os.path.join(os.environ.get("LOCALAPPDATA") or os.path.expanduser("~"), "FotoSuprema")
CARPETA_APP = os.path.join(BASE_DATOS, "app")
VERSION_LOCAL = os.path.join(CARPETA_APP, "version.json")

BG, TEXTO, TEXTO2, ACENTO = "#121419", "#eceff4", "#9aa3b2", "#7c5cff"


def carpeta_empaquetada():
    return os.path.join(getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__))), "app")


def descargar(url, timeout=8):
    sep = "&" if "?" in url else "?"
    req = urllib.request.Request(f"{url}{sep}t={int(time.time())}",  # evita la caché
                                 headers={"User-Agent": "FotoSuprema", "Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def comparar(v):
    try:
        return tuple(int(x) for x in str(v).split("."))
    except Exception:
        return (0,)


def leer_json(ruta):
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


class Pantallita:
    """Ventanita de carga mientras se busca actualización."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.configure(bg=BG)
        w, h = 420, 170
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        try:
            self.root.iconbitmap(os.path.join(getattr(sys, "_MEIPASS", ""), "icono.ico"))
        except Exception:
            pass
        tk.Label(self.root, text="📸 Foto Suprema", bg=BG, fg=TEXTO, font=("Segoe UI", 20, "bold")).pack(pady=(28, 4))
        self.estado = tk.Label(self.root, text="Buscando actualizaciones…", bg=BG, fg=TEXTO2, font=("Segoe UI", 11))
        self.estado.pack()
        tk.Label(self.root, text="HECHO POR @BYALVARO__", bg=BG, fg="#5b6474",
                 font=("Segoe UI", 8, "bold")).pack(side="bottom", pady=10)
        self.resultado = None
        self.texto_pendiente = None

    def poner(self, texto):
        self.texto_pendiente = texto

    def esperar(self, hilo):
        def tic():
            if self.texto_pendiente:
                self.estado.configure(text=self.texto_pendiente)
                self.texto_pendiente = None
            if hilo.is_alive():
                self.root.after(80, tic)
            else:
                self.root.destroy()
        self.root.after(80, tic)
        self.root.mainloop()


def instalar_carpeta_empaquetada():
    """Primera vez sin internet: usa la copia que viene dentro del .exe."""
    origen = carpeta_empaquetada()
    if not os.path.isdir(origen):
        return
    os.makedirs(CARPETA_APP, exist_ok=True)
    for n in os.listdir(origen):
        shutil.copy2(os.path.join(origen, n), os.path.join(CARPETA_APP, n))


def actualizar_exe(pant):
    """La actualización pide un lanzador más nuevo: se baja el .exe y se cambia solo."""
    if not getattr(sys, "frozen", False):
        return False
    pant.poner("Descargando nueva versión del programa…")
    datos = descargar(EXE_ULTIMO, timeout=120)
    if len(datos) < 1_000_000:
        return False
    actual = sys.executable
    nuevo = actual + ".nuevo"
    with open(nuevo, "wb") as f:
        f.write(datos)
    bat = os.path.join(tempfile.gettempdir(), "foto_suprema_actualizar.bat")
    with open(bat, "w", encoding="mbcs" if os.name == "nt" else "utf-8") as f:
        f.write(f'''@echo off
ping 127.0.0.1 -n 3 > nul
:otra
move /y "{nuevo}" "{actual}" > nul 2>&1
if exist "{nuevo}" (ping 127.0.0.1 -n 2 > nul & goto otra)
start "" "{actual}"
del "%~f0"
''')
    subprocess.Popen(["cmd", "/c", bat], creationflags=0x08000000)  # sin ventana negra
    return True


def comprobar(pant):
    """Se ejecuta en un hilo mientras se ve la ventanita."""
    local = leer_json(VERSION_LOCAL)
    try:
        remoto = json.loads(descargar(RAW + "version.json").decode("utf-8"))
    except Exception:
        remoto = None

    if remoto is None:
        if not local:
            pant.poner("Sin internet: abriendo la versión incluida…")
            instalar_carpeta_empaquetada()
        pant.resultado = "ok"
        return

    if int(remoto.get("lanzador_minimo", 1)) > VERSION_LANZADOR:
        try:
            if actualizar_exe(pant):
                pant.resultado = "reinicio"
                return
        except Exception:
            pass

    if not local or comparar(remoto.get("version")) > comparar(local.get("version")):
        pant.poner(f"Actualizando a la versión {remoto.get('version')}…")
        tmp = os.path.join(BASE_DATOS, "app_descarga")
        try:
            shutil.rmtree(tmp, ignore_errors=True)
            os.makedirs(tmp)
            for archivo in remoto.get("archivos", []):
                contenido = descargar(RAW + "app/" + archivo, timeout=30)
                if archivo.endswith(".py"):
                    compile(contenido, archivo, "exec")   # si el código está roto, no se instala
                with open(os.path.join(tmp, archivo), "wb") as f:
                    f.write(contenido)
            with open(os.path.join(tmp, "version.json"), "w", encoding="utf-8") as f:
                json.dump(remoto, f, ensure_ascii=False, indent=2)
            os.makedirs(CARPETA_APP, exist_ok=True)
            for n in os.listdir(tmp):
                shutil.copy2(os.path.join(tmp, n), os.path.join(CARPETA_APP, n))
            pant.poner("¡Actualizado!")
            time.sleep(0.4)
        except Exception:
            if not local:
                instalar_carpeta_empaquetada()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    pant.resultado = "ok"


def cargar_modulo(nombre, carpeta):
    ruta = os.path.join(carpeta, nombre + ".py")
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = mod
    spec.loader.exec_module(mod)
    return mod


def arrancar_app():
    carpeta = CARPETA_APP if os.path.isfile(os.path.join(CARPETA_APP, "foto_suprema.py")) else carpeta_empaquetada()
    try:
        cargar_modulo("nucleo", carpeta)
        app = cargar_modulo("foto_suprema", carpeta)
    except Exception:
        # la versión descargada falla: se usa la incluida en el .exe
        if carpeta != carpeta_empaquetada():
            for m in ("nucleo", "foto_suprema"):
                sys.modules.pop(m, None)
            carpeta = carpeta_empaquetada()
            cargar_modulo("nucleo", carpeta)
            app = cargar_modulo("foto_suprema", carpeta)
        else:
            raise
    app.App().mainloop()


def main():
    os.makedirs(BASE_DATOS, exist_ok=True)
    pant = Pantallita()
    hilo = threading.Thread(target=comprobar, args=(pant,), daemon=True)
    hilo.start()
    pant.esperar(hilo)
    if pant.resultado == "reinicio":
        return
    arrancar_app()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        with open(os.path.join(BASE_DATOS, "error.log"), "w", encoding="utf-8") as f:
            traceback.print_exc(file=f)
        try:
            r = tk.Tk()
            r.withdraw()
            messagebox.showerror("Foto Suprema", f"Ha habido un error al abrir:\n{e}\n\nDetalles en:\n{BASE_DATOS}\\error.log")
        except Exception:
            pass
