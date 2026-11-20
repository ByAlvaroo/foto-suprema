"""
FOTO SUPREMA - lanzador (se convierte en FotoSuprema.exe)

- Lleva Python, Qt (con reproductor de vídeo), Pillow y todo lo necesario DENTRO del .exe.
- Al abrirse mira en GitHub si hay versión nueva del código (version.json) y se la descarga sola.
- Sin internet abre la última versión descargada (o la que viene dentro del .exe).
- Si una actualización necesita un .exe más nuevo, se lo baja y se reemplaza solo.

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

# --- todo lo que usa la app, para que PyInstaller lo meta dentro del .exe ---
import queue, re, datetime, ctypes  # noqa: F401,E401
from PySide6 import QtCore, QtGui, QtWidgets, QtMultimedia, QtMultimediaWidgets  # noqa: F401
from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import QPainter, QColor, QLinearGradient, QBrush, QFont, QIcon
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QProgressBar, QMessageBox
from PIL import Image, ImageOps, ImageDraw  # noqa: F401
try:
    import pillow_heif  # noqa: F401
except Exception:
    pass

# ======================================================================
# CONFIGURACIÓN DEL REPOSITORIO
# ======================================================================
USUARIO_GITHUB = "ByAlvaroo"
REPOSITORIO = "foto-suprema"
RAMA = "main"
VERSION_LANZADOR = 2   # súbelo solo si cambias ESTE archivo o hace falta una librería nueva

RAW = f"https://raw.githubusercontent.com/{USUARIO_GITHUB}/{REPOSITORIO}/{RAMA}/"
EXE_ULTIMO = f"https://github.com/{USUARIO_GITHUB}/{REPOSITORIO}/releases/latest/download/FotoSuprema.exe"

BASE_DATOS = os.path.join(os.environ.get("LOCALAPPDATA") or os.path.expanduser("~"), "FotoSuprema")
CARPETA_APP = os.path.join(BASE_DATOS, "app")
VERSION_LOCAL = os.path.join(CARPETA_APP, "version.json")


def carpeta_empaquetada():
    return os.path.join(getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__))), "app")


def descargar(url, timeout=8):
    sep = "&" if "?" in url else "?"
    req = urllib.request.Request(f"{url}{sep}t={int(time.time())}",
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


# ----------------------------------------------------------------------
# pantalla de carga
# ----------------------------------------------------------------------
class Logo(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(64, 64)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(0, 0, 64, 64)
        g = QLinearGradient(r.topLeft(), r.bottomRight())
        g.setColorAt(0, QColor("#ffb627"))
        g.setColorAt(1, QColor("#ff8a00"))
        p.setBrush(QBrush(g))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(r, 18, 18)
        f = QFont()
        f.setFamilies(["Segoe Fluent Icons", "Segoe MDL2 Assets"])
        f.setPixelSize(30)
        p.setFont(f)
        p.setPen(QColor("#1c1d20"))
        p.drawText(r, Qt.AlignmentFlag.AlignCenter, "")
        p.end()


class Pantallita(QWidget):
    def __init__(self):
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(440, 250)
        caja = QWidget(self)
        caja.setGeometry(0, 0, 440, 250)
        caja.setObjectName("caja")
        caja.setStyleSheet("""
            #caja { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #31353b, stop:1 #26292e);
                    border: 1px solid #3a3e45; border-radius: 22px; }
            QLabel { color: #eceef2; font-family: "Segoe UI"; background: transparent; }
            QProgressBar { background: #1e2125; border: none; border-radius: 3px; }
            QProgressBar::chunk { border-radius: 3px; background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #ffb627, stop:1 #ff8a00); }
        """)
        L = QVBoxLayout(caja)
        L.setContentsMargins(36, 30, 36, 22)
        L.setSpacing(8)
        L.addWidget(Logo(), 0, Qt.AlignmentFlag.AlignHCenter)
        t = QLabel("Foto Suprema")
        t.setStyleSheet("font-size: 24px; font-weight: 700;")
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        L.addWidget(t)
        self.estado = QLabel("Buscando actualizaciones…")
        self.estado.setStyleSheet("font-size: 13px; color: #9ba1ad;")
        self.estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        L.addWidget(self.estado)
        barra = QProgressBar()
        barra.setRange(0, 0)
        barra.setFixedHeight(6)
        barra.setTextVisible(False)
        L.addWidget(barra)
        L.addStretch()
        f = QLabel("HECHO POR @BYALVARO__")
        f.setStyleSheet("font-size: 10px; color: #6b717c; font-weight: 700;")
        f.setAlignment(Qt.AlignmentFlag.AlignCenter)
        L.addWidget(f)
        self.texto_pendiente = None
        self.resultado = None
        pantalla = QApplication.primaryScreen().availableGeometry()
        self.move(pantalla.center().x() - 220, pantalla.center().y() - 125)

    def poner(self, texto):
        self.texto_pendiente = texto


# ----------------------------------------------------------------------
# actualización
# ----------------------------------------------------------------------
def instalar_carpeta_empaquetada():
    origen = carpeta_empaquetada()
    if not os.path.isdir(origen):
        return
    os.makedirs(CARPETA_APP, exist_ok=True)
    for n in os.listdir(origen):
        if os.path.isfile(os.path.join(origen, n)):
            shutil.copy2(os.path.join(origen, n), os.path.join(CARPETA_APP, n))


def version_empaquetada():
    return leer_json(os.path.join(carpeta_empaquetada(), "version.json"))


def actualizar_exe(pant):
    """Cambia el .exe por el de la última Release. Con protecciones para que nunca
    entre en bucle (p. ej. si GitHub aún está compilando el .exe nuevo)."""
    if not getattr(sys, "frozen", False) or "--recien-actualizado" in sys.argv:
        return False
    import hashlib
    marca = os.path.join(BASE_DATOS, "intento_exe.json")
    previo = leer_json(marca)
    if time.time() - previo.get("t", 0) < 30 * 60:   # como mucho un intento cada 30 min
        return False
    with open(marca, "w", encoding="utf-8") as f:
        json.dump({"t": time.time()}, f)
    pant.poner("Descargando la nueva versión del programa…")
    datos = descargar(EXE_ULTIMO, timeout=300)
    if len(datos) < 5_000_000:
        return False
    actual = sys.executable
    with open(actual, "rb") as f:
        if hashlib.sha256(f.read()).digest() == hashlib.sha256(datos).digest():
            return False   # la Release todavía es este mismo .exe: no hay nada que cambiar
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
start "" "{actual}" --recien-actualizado
del "%~f0"
''')
    subprocess.Popen(["cmd", "/c", bat], creationflags=0x08000000)
    return True


def comprobar(pant):
    local = leer_json(VERSION_LOCAL)
    # si el .exe trae una versión más nueva que la descargada, se usa esa
    emp = version_empaquetada()
    if emp and comparar(emp.get("version")) > comparar(local.get("version")):
        instalar_carpeta_empaquetada()
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
        pant.resultado = "ok"   # no se ha podido: se sigue con lo que hay
        return

    if not local or comparar(remoto.get("version")) > comparar(local.get("version")):
        pant.poner(f"Actualizando a la versión {remoto.get('version')}…")
        tmp = os.path.join(BASE_DATOS, "app_descarga")
        try:
            shutil.rmtree(tmp, ignore_errors=True)
            os.makedirs(tmp)
            for archivo in remoto.get("archivos", []):
                contenido = descargar(RAW + "app/" + archivo, timeout=30)
                if archivo.endswith(".py"):
                    compile(contenido, archivo, "exec")
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


def cargar_app():
    carpeta = CARPETA_APP if os.path.isfile(os.path.join(CARPETA_APP, "foto_suprema.py")) else carpeta_empaquetada()
    try:
        cargar_modulo("nucleo", carpeta)
        return cargar_modulo("foto_suprema", carpeta)
    except Exception:
        if carpeta == carpeta_empaquetada():
            raise
        for m in ("nucleo", "foto_suprema"):
            sys.modules.pop(m, None)
        carpeta = carpeta_empaquetada()
        cargar_modulo("nucleo", carpeta)
        return cargar_modulo("foto_suprema", carpeta)


def main():
    os.makedirs(BASE_DATOS, exist_ok=True)
    if os.name == "nt":
        try:  # icono propio en la barra de tareas
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ByAlvaro.FotoSuprema")
        except Exception:
            pass
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(os.path.join(getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__))), "icono.ico")))
    pant = Pantallita()
    pant.show()
    hilo = threading.Thread(target=comprobar, args=(pant,), daemon=True)
    hilo.start()

    estado = {"ventana": None}

    def tic():
        if pant.texto_pendiente:
            pant.estado.setText(pant.texto_pendiente)
            pant.texto_pendiente = None
        if hilo.is_alive():
            return
        timer.stop()
        if pant.resultado == "reinicio":
            app.quit()
            return
        try:
            mod = cargar_app()
            estado["ventana"] = mod.iniciar(app)
        except Exception as e:
            guardar_error()
            QMessageBox.critical(None, "Foto Suprema", f"Ha habido un error al abrir:\n{e}\n\nDetalles en:\n{BASE_DATOS}\\error.log")
            app.quit()
        finally:
            pant.close()

    timer = QTimer()
    timer.timeout.connect(tic)
    timer.start(80)
    sys.exit(app.exec())


def guardar_error():
    import traceback
    try:
        with open(os.path.join(BASE_DATOS, "error.log"), "w", encoding="utf-8") as f:
            traceback.print_exc(file=f)
    except Exception:
        pass


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        guardar_error()
        try:
            _app = QApplication.instance() or QApplication(sys.argv)
            QMessageBox.critical(None, "Foto Suprema", f"Ha habido un error al abrir:\n{e}")
        except Exception:
            pass
