"""
FOTO SUPREMA 2 - organizador de fotos (interfaz Qt)
HECHO POR @BYALVARO__
"""
import os
import sys
import time
import queue
import threading
import subprocess

from PySide6.QtCore import (Qt, QTimer, QUrl, QPointF, QRectF, QSize, Signal,
                            QPropertyAnimation, QEasingCurve, QEvent, QObject)
from PySide6.QtGui import (QPixmap, QImage, QPainter, QColor, QFont, QIcon, QKeyEvent,
                           QCursor, QLinearGradient, QBrush, QPen)
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QFrame, QLabel, QPushButton,
                               QVBoxLayout, QHBoxLayout, QGridLayout, QStackedWidget, QScrollArea,
                               QProgressBar, QSlider, QFileDialog, QMessageBox, QSizePolicy,
                               QGraphicsDropShadowEffect, QGraphicsOpacityEffect)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

from PIL import Image, ImageOps

import nucleo as N

VERSION_APP = "2.0.0"
FIRMA = "HECHO POR @BYALVARO__"

# ----------------------------------------------------------------------
# tema (estilo neumórfico oscuro con acento naranja)
# ----------------------------------------------------------------------
FONDO = "#26292e"
FONDO_VISOR = "#1b1d21"
CARTA_A = "#31353b"
CARTA_B = "#282b30"
BORDE = "#363a41"
TEXTO = "#eceef2"
TEXTO2 = "#9ba1ad"
TEXTO3 = "#6b717c"
NAR_A = "#ffb627"
NAR_B = "#ff8a00"
ROJO = "#ff5a5f"
VERDE = "#3ccf8e"
AZUL = "#4aa8ff"
GRIS = "#7a808b"

ICONOS = ["Segoe Fluent Icons", "Segoe MDL2 Assets"]
G = {  # glifos de Segoe MDL2 / Fluent Icons
    "atras": "", "borrar": "", "estrella": "", "check": "",
    "deshacer": "", "abajo": "", "subir": "", "carpeta": "",
    "foto": "", "calendario": "", "play": "", "pausa": "",
    "volumen": "", "mute": "", "abrir": "", "zoom": "",
    "video": "", "mas": "", "cerrar": "", "ajustes": "",
}

QSS = f"""
* {{ font-family: "Segoe UI", "Segoe UI Variable", Arial; color: {TEXTO}; font-size: 14px; }}
QMainWindow, #raiz, #pagina, QScrollArea, #scrollInterior {{ background: {FONDO}; border: none; }}
QToolTip {{ background: {CARTA_A}; color: {TEXTO}; border: 1px solid {BORDE}; padding: 6px; border-radius: 6px; }}

#card {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {CARTA_A}, stop:1 {CARTA_B});
    border: 1px solid {BORDE}; border-top-color: #3f444c; border-radius: 18px;
}}
#accion {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {CARTA_A}, stop:1 {CARTA_B});
    border: 1px solid {BORDE}; border-top-color: #3f444c; border-radius: 18px;
}}
#accion:hover {{ border: 1px solid {NAR_B}; }}
#accion:disabled {{ background: #2a2d32; border: 1px solid #2f3238; }}
#visor {{ background: {FONDO_VISOR}; border-radius: 18px; border: 1px solid #22252a; }}

#titulo {{ font-size: 30px; font-weight: 700; }}
#subtitulo {{ color: {TEXTO2}; font-size: 14px; }}
#h2 {{ font-size: 18px; font-weight: 700; }}
#h3 {{ font-size: 16px; font-weight: 600; }}
#tenue {{ color: {TEXTO2}; }}
#muytenue {{ color: {TEXTO3}; font-size: 12px; }}
#firma {{ color: {TEXTO3}; font-size: 11px; font-weight: 700; letter-spacing: 1px; }}
#numero {{ font-size: 30px; font-weight: 700; }}
#grande {{ font-size: 34px; font-weight: 700; }}
#pct {{ font-size: 22px; font-weight: 700; color: {NAR_A}; }}

#chip {{ background: #2e3238; border: 1px solid {BORDE}; border-radius: 10px; padding: 5px 11px; color: {TEXTO2}; font-size: 13px; }}
#tecla {{ background: #1f2226; border: 1px solid #3a3e45; border-bottom: 2px solid #3a3e45; border-radius: 6px;
          padding: 1px 8px; color: {TEXTO2}; font-size: 12px; font-weight: 600; }}
#ruta {{ background: #202327; border: 1px solid {BORDE}; border-radius: 12px; padding: 9px 14px; color: {TEXTO}; }}

QPushButton {{ border: none; }}
QPushButton#primario {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {NAR_A}, stop:1 {NAR_B});
    color: #1c1d20; border-radius: 12px; padding: 11px 24px; font-weight: 700; font-size: 14px;
}}
QPushButton#primario:hover {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ffc552, stop:1 #ff9d2e); }}
QPushButton#primario:disabled {{ background: #34373d; color: {TEXTO3}; }}
QPushButton#secundario {{
    background: #30343a; border: 1px solid #3c4048; border-radius: 12px; padding: 10px 20px; font-weight: 600;
}}
QPushButton#secundario:hover {{ border: 1px solid {NAR_B}; color: white; }}
QPushButton#peligro {{
    background: #3a2a2d; border: 1px solid #5a3438; color: #ff8a8e; border-radius: 12px; padding: 10px 20px; font-weight: 600;
}}
QPushButton#peligro:hover {{ background: #4a2c30; border: 1px solid {ROJO}; color: white; }}
QPushButton#peligro:disabled {{ background: #2c2e33; border-color: #33363c; color: {TEXTO3}; }}

QProgressBar {{ background: #1e2125; border: 1px solid #2f3238; border-radius: 9px; height: 18px; text-align: center; color: transparent; }}
QProgressBar::chunk {{ border-radius: 8px; background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {NAR_A}, stop:1 {NAR_B}); }}
QProgressBar#fina {{ height: 6px; border-radius: 3px; border: none; }}
QProgressBar#fina::chunk {{ border-radius: 3px; }}

QSlider::groove:horizontal {{ height: 8px; background: #1e2125; border-radius: 4px; border: 1px solid #2f3238; }}
QSlider::sub-page:horizontal {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {NAR_A}, stop:1 {NAR_B}); border-radius: 4px; }}
QSlider::handle:horizontal {{ background: white; width: 18px; height: 18px; margin: -6px 0; border-radius: 9px; }}
QSlider::handle:horizontal:hover {{ background: #fff3dc; }}

QScrollBar:vertical {{ background: transparent; width: 10px; margin: 4px; }}
QScrollBar::handle:vertical {{ background: #3a3e45; border-radius: 4px; min-height: 40px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}

QMessageBox {{ background: {CARTA_A}; }}
QMessageBox QPushButton {{ background: #3a3e45; border-radius: 8px; padding: 7px 18px; min-width: 70px; }}
QMessageBox QPushButton:hover {{ background: {NAR_B}; color: #1c1d20; }}
#toast {{ background: rgba(20, 22, 25, 225); border: 1px solid #3a3e45; border-radius: 14px; padding: 10px 18px;
          font-size: 15px; font-weight: 600; }}
"""


# ----------------------------------------------------------------------
# utilidades
# ----------------------------------------------------------------------
def recurso(nombre):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, nombre)


def abrir_en_sistema(ruta):
    try:
        if os.name == "nt":
            os.startfile(ruta)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", ruta])
        else:
            subprocess.Popen(["xdg-open", ruta])
    except Exception as e:
        QMessageBox.warning(None, "Foto Suprema", f"No se ha podido abrir:\n{e}")


def fuente_iconos(px):
    f = QFont()
    f.setFamilies(ICONOS)
    f.setPixelSize(px)
    return f


def sombra(widget, blur=28, dy=8, alpha=150):
    ef = QGraphicsDropShadowEffect(widget)
    ef.setBlurRadius(blur)
    ef.setOffset(0, dy)
    ef.setColor(QColor(10, 11, 13, alpha))
    widget.setGraphicsEffect(ef)


def etiqueta(texto="", nombre=None, wrap=False):
    l = QLabel(texto)
    if nombre:
        l.setObjectName(nombre)
    if wrap:
        l.setWordWrap(True)
    return l


def boton(texto, estilo="secundario", cmd=None, icono=None):
    b = QPushButton(texto if not icono else f"  {texto}")
    b.setObjectName(estilo)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    if icono:
        b.setIcon(icono_glifo(icono, "#1c1d20" if estilo == "primario" else TEXTO, 18))
        b.setIconSize(QSize(18, 18))
    if cmd:
        b.clicked.connect(cmd)
    return b


def icono_glifo(glifo, color, px=20):
    """Convierte un glifo de la fuente de iconos de Windows en QIcon."""
    pm = QPixmap(px * 2, px * 2)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setFont(fuente_iconos(int(px * 1.6)))
    p.setPen(QColor(color))
    p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, glifo)
    p.end()
    pm.setDevicePixelRatio(2.0)
    return QIcon(pm)


def pil_a_qimage(im):
    if im.mode != "RGBA":
        im = im.convert("RGBA")
    datos = im.tobytes("raw", "RGBA")
    qi = QImage(datos, im.width, im.height, im.width * 4, QImage.Format.Format_RGBA8888)
    return qi.copy()


def abrir_preparada(ruta, max_w=None, max_h=None):
    """Abre la foto girada según su EXIF (solo lectura, el archivo no se modifica)."""
    im = Image.open(ruta)
    if max_w and max_h and im.format == "JPEG":
        try:
            lado = max(max_w, max_h)
            im.draft("RGB", (lado, lado))
        except Exception:
            pass
    im = ImageOps.exif_transpose(im)
    if im.mode not in ("RGB", "RGBA"):
        im = im.convert("RGBA" if ("A" in im.getbands() or im.mode == "P") else "RGB")
    if max_w and max_h:
        im.thumbnail((max_w, max_h), Image.LANCZOS)
    else:
        im.load()
    return im


def _v(x):
    """Valor entero de un enum de Qt (sirve en todas las versiones de PySide6)."""
    return x.value if hasattr(x, "value") else int(x)


K_IZQ, K_DER, K_ARR, K_ABA = (_v(Qt.Key.Key_Left), _v(Qt.Key.Key_Right), _v(Qt.Key.Key_Up), _v(Qt.Key.Key_Down))
K_RET, K_Z, K_ESC, K_V, K_ESP, K_SUP = (_v(Qt.Key.Key_Backspace), _v(Qt.Key.Key_Z), _v(Qt.Key.Key_Escape),
                                        _v(Qt.Key.Key_V), _v(Qt.Key.Key_Space), _v(Qt.Key.Key_Delete))


def fmt_ms(ms):
    s = max(0, int(ms // 1000))
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


# ----------------------------------------------------------------------
# carga en segundo plano
# ----------------------------------------------------------------------
class Cargador:
    def __init__(self):
        self.cola = queue.Queue()
        self.previas = {}
        self.minis = {}
        self.infos = {}
        self.lock = threading.Lock()
        threading.Thread(target=self._bucle, daemon=True).start()

    def pedir_previa(self, ruta, w, h):
        self.cola.put(("previa", ruta, w, h))

    def pedir_mini(self, ruta):
        self.cola.put(("mini", ruta, 0, 0))

    def pedir_info(self, ruta):
        self.cola.put(("info", ruta, 0, 0))

    def limpiar(self, mantener):
        with self.lock:
            for k in list(self.previas):
                if k[0] not in mantener:
                    del self.previas[k]
            for d in (self.minis, self.infos):
                if len(d) > 500:
                    for k in list(d)[:250]:
                        if k not in mantener:
                            del d[k]

    def _bucle(self):
        while True:
            tipo, ruta, w, h = self.cola.get()
            try:
                if tipo == "previa":
                    if (ruta, w, h) in self.previas or N.es_video(ruta):
                        continue
                    im = abrir_preparada(ruta, w, h)
                    with self.lock:
                        self.previas[(ruta, w, h)] = im
                elif tipo == "mini":
                    if ruta in self.minis:
                        continue
                    im = None if N.es_video(ruta) else abrir_preparada(ruta, 240, 160)
                    with self.lock:
                        self.minis[ruta] = im
                elif tipo == "info":
                    if ruta in self.infos:
                        continue
                    inf = N.info_archivo(ruta)
                    with self.lock:
                        self.infos[ruta] = inf
            except Exception:
                with self.lock:
                    if tipo == "mini":
                        self.minis[ruta] = None
                    elif tipo == "previa":
                        self.previas[(ruta, w, h)] = None


# ----------------------------------------------------------------------
# componentes
# ----------------------------------------------------------------------
class Carta(QFrame):
    def __init__(self, nombre="card", con_sombra=True):
        super().__init__()
        self.setObjectName(nombre)
        if con_sombra:
            sombra(self)


class CartaClic(Carta):
    def __init__(self, cmd):
        super().__init__()
        self.cmd = cmd
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.cmd()


class Circulo(QPushButton):
    """Botón redondo con icono (como los del diseño)."""

    def __init__(self, glifo, color=TEXTO, tam=64, relleno=False, color_relleno=None, tip=""):
        super().__init__()
        self.glifo = glifo
        self.color = color
        self.tam = tam
        self.relleno = relleno
        self.color_relleno = color_relleno or color
        self.encendido = False
        self.setFixedSize(tam, tam)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setToolTip(tip)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self.badge = ""

    def destello(self):
        self.encendido = True
        self.update()
        QTimer.singleShot(160, self._apagar)

    def _apagar(self):
        self.encendido = False
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(3, 3, self.tam - 6, self.tam - 6)
        activo = self.isEnabled()
        caliente = activo and (self.underMouse() or self.isDown() or self.encendido)
        if (self.relleno or caliente) and activo:
            g = QLinearGradient(r.topLeft(), r.bottomRight())
            base = QColor(self.color_relleno)
            g.setColorAt(0, base.lighter(118))
            g.setColorAt(1, base.darker(108))
            p.setBrush(QBrush(g))
            p.setPen(Qt.PenStyle.NoPen)
            col_icono = QColor("#1c1d20") if QColor(self.color_relleno).lightness() > 140 else QColor("white")
        else:
            g = QLinearGradient(r.topLeft(), r.bottomRight())
            g.setColorAt(0, QColor("#363a41"))
            g.setColorAt(1, QColor("#2a2d32"))
            p.setBrush(QBrush(g))
            p.setPen(QPen(QColor("#40444c"), 1))
            col_icono = QColor(self.color if activo else "#555a63")
        p.drawEllipse(r)
        p.setPen(col_icono)
        p.setFont(fuente_iconos(int(self.tam * 0.36)))
        p.drawText(r, Qt.AlignmentFlag.AlignCenter, self.glifo)
        if self.badge and activo:
            br = QRectF(self.tam - 26, 0, 26, 20)
            p.setBrush(QColor(NAR_B))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(br, 10, 10)
            p.setPen(QColor("#1c1d20"))
            f = QFont("Segoe UI")
            f.setPixelSize(11)
            f.setBold(True)
            p.setFont(f)
            p.drawText(br, Qt.AlignmentFlag.AlignCenter, self.badge)
        p.end()


class BotonAccion(QWidget):
    """Círculo grande + nombre + tecla."""

    def __init__(self, glifo, texto, tecla, color, cmd, tam=74, relleno=False):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(6, 0, 6, 0)
        lay.setSpacing(5)
        self.circulo = Circulo(glifo, color, tam, relleno=relleno, color_relleno=color, tip=f"{texto} ({tecla})")
        self.circulo.clicked.connect(cmd)
        lay.addWidget(self.circulo, 0, Qt.AlignmentFlag.AlignHCenter)
        self.lbl = etiqueta(texto, "h3")
        self.lbl.setStyleSheet("font-size: 13px;")
        self.lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.lbl)
        t = etiqueta(tecla, "tecla")
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(t, 0, Qt.AlignmentFlag.AlignHCenter)

    def set_activo(self, a):
        self.circulo.setEnabled(a)
        self.lbl.setStyleSheet(f"font-size: 13px; color: {TEXTO if a else TEXTO3};")


class Logo(QWidget):
    def __init__(self, tam=52):
        super().__init__()
        self.tam = tam
        self.setFixedSize(tam, tam)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(0, 0, self.tam, self.tam)
        g = QLinearGradient(r.topLeft(), r.bottomRight())
        g.setColorAt(0, QColor(NAR_A))
        g.setColorAt(1, QColor(NAR_B))
        p.setBrush(QBrush(g))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(r, self.tam * 0.28, self.tam * 0.28)
        p.setPen(QColor("#1c1d20"))
        p.setFont(fuente_iconos(int(self.tam * 0.48)))
        p.drawText(r, Qt.AlignmentFlag.AlignCenter, G["foto"])
        p.end()


class IconoCirculo(QWidget):
    """Círculo naranja con icono (decorativo)."""

    def __init__(self, glifo, tam=48, color_a=NAR_A, color_b=NAR_B):
        super().__init__()
        self.glifo, self.tam, self.ca, self.cb = glifo, tam, color_a, color_b
        self.setFixedSize(tam, tam)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(1, 1, self.tam - 2, self.tam - 2)
        activo = self.isEnabled()
        g = QLinearGradient(r.topLeft(), r.bottomRight())
        g.setColorAt(0, QColor(self.ca if activo else "#3a3d43"))
        g.setColorAt(1, QColor(self.cb if activo else "#33363b"))
        p.setBrush(QBrush(g))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(r)
        p.setPen(QColor("#1c1d20" if activo else "#5c616b"))
        p.setFont(fuente_iconos(int(self.tam * 0.42)))
        p.drawText(r, Qt.AlignmentFlag.AlignCenter, self.glifo)
        p.end()


class Toast(QLabel):
    def __init__(self, padre):
        super().__init__(padre)
        self.setObjectName("toast")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.efecto = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.efecto)
        self.anim = QPropertyAnimation(self.efecto, b"opacity", self)
        self.anim.setDuration(500)
        self.anim.setEasingCurve(QEasingCurve.Type.InQuad)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._ocultar)
        self.hide()

    def mostrar(self, texto, color=TEXTO):
        self.anim.stop()
        self.setText(texto)
        self.setStyleSheet(f"color: {color};")
        self.adjustSize()
        pw = self.parentWidget().width()
        self.move((pw - self.width()) // 2, 18)
        self.efecto.setOpacity(1.0)
        self.show()
        self.raise_()
        self.timer.start(700)

    def _ocultar(self):
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)
        self.anim.start()


class VisorImagen(QWidget):
    """Muestra la foto ajustada; rueda = zoom hacia el cursor, arrastrar = mover, doble clic = ajustar."""
    zoom_cambiado = Signal(str)
    redimensionado = Signal()

    def __init__(self):
        super().__init__()
        self.previa = None
        self.full = None
        self.mensaje = ""
        self.zoom = 1.0
        self.centro = QPointF(0, 0)
        self.cargar_full = None
        self._arr = None
        self.setMinimumSize(200, 150)
        self.setMouseTracking(True)

    def poner(self, pixmap, mensaje=""):
        self.previa = pixmap
        self.full = None
        self.zoom = 1.0
        self.mensaje = mensaje
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.zoom_cambiado.emit("")
        self.update()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.redimensionado.emit()

    def _ajuste(self):
        W, H = self.full.width(), self.full.height()
        dpr = self.devicePixelRatioF()
        return min(self.width() / W, self.height() / H, 1.0 / dpr)

    def _escala(self):
        return self._ajuste() * self.zoom

    def _limitar(self):
        s = self._escala()
        W, H = self.full.width(), self.full.height()
        vw, vh = self.width() / s, self.height() / s
        cx = W / 2 if vw >= W else min(max(self.centro.x(), vw / 2), W - vw / 2)
        cy = H / 2 if vh >= H else min(max(self.centro.y(), vh / 2), H - vh / 2)
        self.centro = QPointF(cx, cy)

    def aplicar_zoom(self, factor, punto=None):
        if self.full is None:
            if not self.cargar_full:
                return
            self.full = self.cargar_full()
            if self.full is None:
                return
            self.centro = QPointF(self.full.width() / 2, self.full.height() / 2)
        if punto is None:
            punto = QPointF(self.width() / 2, self.height() / 2)
        ajuste = self._ajuste()
        s_old = ajuste * self.zoom
        max_zoom = max(1.0, (4.0 / self.devicePixelRatioF()) / ajuste)
        nuevo = min(max(self.zoom * factor, 1.0), max_zoom)
        if abs(nuevo - self.zoom) < 1e-6:
            return
        mx, my = punto.x() - self.width() / 2, punto.y() - self.height() / 2
        px, py = self.centro.x() + mx / s_old, self.centro.y() + my / s_old
        self.zoom = nuevo
        s_new = ajuste * self.zoom
        self.centro = QPointF(px - mx / s_new, py - my / s_new)
        if self.zoom <= 1.0001:
            self.reset_zoom()
            return
        self._limitar()
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.zoom_cambiado.emit(f"{s_new * self.devicePixelRatioF() * 100:.0f} %")
        self.update()

    def reset_zoom(self):
        self.zoom = 1.0
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.zoom_cambiado.emit("")
        self.update()

    def wheelEvent(self, e):
        d = e.angleDelta().y()
        if d:
            self.aplicar_zoom(1.25 if d > 0 else 1 / 1.25, e.position())

    def mousePressEvent(self, e):
        if self.zoom > 1.0 and e.button() == Qt.MouseButton.LeftButton:
            self._arr = e.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, e):
        if self._arr is not None and self.full is not None and self.zoom > 1.0:
            s = self._escala()
            d = e.position() - self._arr
            self._arr = e.position()
            self.centro = QPointF(self.centro.x() - d.x() / s, self.centro.y() - d.y() / s)
            self._limitar()
            self.update()

    def mouseReleaseEvent(self, e):
        self._arr = None
        if self.zoom > 1.0:
            self.setCursor(Qt.CursorShape.OpenHandCursor)

    def mouseDoubleClickEvent(self, e):
        if self.zoom > 1.0:
            self.reset_zoom()
        else:
            self.aplicar_zoom(2.5, e.position())

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        if self.zoom > 1.0 and self.full is not None:
            s = self._escala()
            self._limitar()
            W, H = self.full.width(), self.full.height()
            vw, vh = w / s, h / s
            cx, cy = self.centro.x(), self.centro.y()
            src = QRectF(cx - vw / 2, cy - vh / 2, vw, vh).intersected(QRectF(0, 0, W, H))
            dst = QRectF(w / 2 + (src.x() - cx) * s, h / 2 + (src.y() - cy) * s, src.width() * s, src.height() * s)
            p.drawPixmap(dst, self.full, src)
        elif self.previa is not None and not self.previa.isNull():
            tam = self.previa.deviceIndependentSize()
            pw, ph = tam.width(), tam.height()
            f = min(1.0, w / pw, h / ph)
            pw, ph = pw * f, ph * f
            p.drawPixmap(QRectF((w - pw) / 2, (h - ph) / 2, pw, ph), self.previa,
                         QRectF(0, 0, self.previa.width(), self.previa.height()))
        if self.mensaje:
            p.setPen(QColor(TEXTO2))
            f = QFont("Segoe UI")
            f.setPixelSize(16)
            p.setFont(f)
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.mensaje)
        p.end()


# ======================================================================
# PÁGINA: INICIO
# ======================================================================
class TarjetaAccion(QFrame):
    def __init__(self, glifo, titulo, texto, cmd, activo=True, colores=(NAR_A, NAR_B)):
        super().__init__()
        self.setObjectName("accion")
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self.setCursor(Qt.CursorShape.PointingHandCursor if activo else Qt.CursorShape.ArrowCursor)
        self.cmd = cmd
        sombra(self, 24, 6, 120)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(16)
        ic = IconoCirculo(glifo, 52, *colores)
        lay.addWidget(ic, 0, Qt.AlignmentFlag.AlignTop)
        col = QVBoxLayout()
        col.setSpacing(4)
        t = etiqueta(titulo, "h3")
        d = etiqueta(texto, "tenue", wrap=True)
        d.setStyleSheet("font-size: 13px;")
        col.addWidget(t)
        col.addWidget(d)
        col.addStretch()
        lay.addLayout(col, 1)
        self.setEnabled(activo)
        if not activo:
            t.setStyleSheet(f"color: {TEXTO3};")
        self.setMinimumHeight(110)

    def mouseReleaseEvent(self, e):
        if self.isEnabled() and e.button() == Qt.MouseButton.LeftButton and self.rect().contains(e.position().toPoint()):
            self.cmd()


class PaginaInicio(QWidget):
    def __init__(self, ventana):
        super().__init__()
        self.v = ventana
        self.setObjectName("pagina")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        lay.addWidget(self.scroll)

    def refrescar(self):
        bib = self.v.bib
        interior = QWidget()
        interior.setObjectName("scrollInterior")
        L = QVBoxLayout(interior)
        L.setContentsMargins(44, 32, 44, 18)
        L.setSpacing(22)

        # cabecera
        cab = QHBoxLayout()
        cab.setSpacing(16)
        cab.addWidget(Logo(56))
        tt = QVBoxLayout()
        tt.setSpacing(0)
        tt.addWidget(etiqueta("Foto Suprema", "titulo"))
        tt.addWidget(etiqueta("Organiza miles de fotos en minutos", "subtitulo"))
        cab.addLayout(tt)
        cab.addStretch()
        ruta = etiqueta(f"📁  {bib.raiz}", "ruta")
        ruta.setToolTip("Carpeta de la biblioteca")
        ruta.setMaximumWidth(520)
        cab.addWidget(ruta)
        cab.addWidget(boton("Cambiar", "secundario", self.v.cambiar_biblioteca))
        cab.addWidget(boton("Abrir", "secundario", lambda: abrir_en_sistema(bib.raiz), G["carpeta"]))
        L.addLayout(cab)

        # contadores
        n = {k: bib.contar(k) for k in N.CARPETAS}
        fila = QHBoxLayout()
        fila.setSpacing(18)
        for clave, titulo, glifo, ca, cb in [
                ("pend", "Por revisar", G["foto"], NAR_A, NAR_B),
                ("keep", "Mantener", G["check"], "#5fe0a8", VERDE),
                ("fav", "Favoritos", G["estrella"], "#ffd166", NAR_A),
                ("draft", "Borrador", G["borrar"], "#ff8a8e", ROJO)]:
            r = bib.ruta(clave)
            c = CartaClic(lambda r=r: abrir_en_sistema(r))
            c.setToolTip(f"Abrir la carpeta «{N.CARPETAS[clave]}»")
            hl = QHBoxLayout(c)
            hl.setContentsMargins(20, 16, 20, 16)
            vl = QVBoxLayout()
            vl.setSpacing(0)
            vl.addWidget(etiqueta(N.num(n[clave]), "numero"))
            vl.addWidget(etiqueta(titulo, "tenue"))
            hl.addLayout(vl)
            hl.addStretch()
            hl.addWidget(IconoCirculo(glifo, 46, ca, cb))
            fila.addWidget(c, 1)
        L.addLayout(fila)

        # acciones
        L.addWidget(etiqueta("¿Qué quieres hacer?", "h2"))
        grid = QGridLayout()
        grid.setSpacing(18)
        acciones = [
            (G["subir"], "Subir una carpeta",
             "Copia todas las fotos y vídeos de la carpeta y de TODAS sus subcarpetas. Los originales no se tocan.",
             self.v.subir_carpeta, True),
            (G["foto"], f"Revisar fotos  ·  {N.num(n['pend'])}",
             "Una a una a pantalla completa.  ← eliminar   ↑ favorito   → mantener   ↓ saltar",
             lambda: self.v.ir_revision("pend"), n["pend"] > 0),
            (G["borrar"], f"Confirmar borradores  ·  {N.num(n['draft'])}",
             "Repasa lo que mandaste al borrador: bórralo para siempre o restáuralo.",
             lambda: self.v.ir_revision("draft"), n["draft"] > 0),
            (G["mas"], "Subir fotos sueltas", "Elige una o varias fotos o vídeos concretos.",
             self.v.subir_sueltas, True),
            (G["calendario"], "Organizar por años",
             "Copia lo de «Mantener» en carpetas 2007, 2008… Solo se crean los años que tengan fotos.",
             lambda: self.v.organizar(False), n["keep"] > 0),
            (G["calendario"], "Organizar por años y meses",
             "Igual, pero dentro de cada año: 01 - Enero, 02 - Febrero… Misma resolución, copias exactas.",
             lambda: self.v.organizar(True), n["keep"] > 0),
        ]
        for i, (gl, t, d, cmd, act) in enumerate(acciones):
            grid.addWidget(TarjetaAccion(gl, t, d, cmd, act), i // 3, i % 3)
        for c in range(3):
            grid.setColumnStretch(c, 1)
        L.addLayout(grid)

        # estadísticas
        s = bib.stats
        est = Carta()
        el = QVBoxLayout(est)
        el.setContentsMargins(22, 16, 22, 18)
        el.addWidget(etiqueta("Tus estadísticas", "h3"))
        g2 = QHBoxLayout()
        g2.setSpacing(10)
        for t, val, col in [
                ("Subidas", N.num(s["subidas"]), NAR_A),
                ("Mantenidas", N.num(s["mantenidas"] + s["favoritas"]), VERDE),
                ("Favoritas", N.num(s["favoritas"]), "#ffd166"),
                ("Al borrador", N.num(s["eliminadas"]), "#ff8a8e"),
                ("Borradas del todo", N.num(s["borradas_def"]), ROJO),
                ("Espacio liberado", N.tamano_legible(s["bytes_liberados"]), VERDE),
                ("Organizadas", N.num(s["organizadas"]), AZUL)]:
            b = QVBoxLayout()
            b.setSpacing(0)
            lv = etiqueta(val)
            lv.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {col};")
            b.addWidget(lv)
            b.addWidget(etiqueta(t, "muytenue"))
            g2.addLayout(b, 1)
        el.addLayout(g2)
        L.addWidget(est)

        L.addStretch()
        pie = etiqueta(f"{FIRMA}   ·   v{VERSION_APP}", "firma")
        pie.setAlignment(Qt.AlignmentFlag.AlignCenter)
        L.addWidget(pie)

        viejo = self.scroll.takeWidget()
        if viejo:
            viejo.deleteLater()
        self.scroll.setWidget(interior)


# ======================================================================
# PÁGINA: PROGRESO (subir / organizar)
# ======================================================================
class PaginaProgreso(QWidget):
    def __init__(self, ventana):
        super().__init__()
        self.v = ventana
        self.setObjectName("pagina")
        self.tarea = None
        ext = QVBoxLayout(self)
        ext.addStretch()
        fila = QHBoxLayout()
        fila.addStretch()
        self.carta = Carta()
        self.carta.setMinimumWidth(760)
        self.carta.setMaximumWidth(900)
        fila.addWidget(self.carta)
        fila.addStretch()
        ext.addLayout(fila)
        ext.addStretch()
        pie = etiqueta(FIRMA, "firma")
        pie.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ext.addWidget(pie)

        L = QVBoxLayout(self.carta)
        L.setContentsMargins(46, 34, 46, 34)
        L.setSpacing(10)
        top = QHBoxLayout()
        self.icono = IconoCirculo(G["subir"], 56)
        top.addWidget(self.icono)
        tl = QVBoxLayout()
        tl.setSpacing(0)
        self.l_titulo = etiqueta("", "h2")
        self.l_origen = etiqueta("", "muytenue", wrap=True)
        tl.addWidget(self.l_titulo)
        tl.addWidget(self.l_origen)
        top.addSpacing(12)
        top.addLayout(tl, 1)
        L.addLayout(top)
        L.addSpacing(18)
        fila_n = QHBoxLayout()
        self.l_grande = etiqueta("", "grande")
        self.l_pct = etiqueta("", "pct")
        fila_n.addWidget(self.l_grande)
        fila_n.addStretch()
        fila_n.addWidget(self.l_pct, 0, Qt.AlignmentFlag.AlignBottom)
        L.addLayout(fila_n)
        self.barra = QProgressBar()
        self.barra.setRange(0, 1000)
        self.barra.setFixedHeight(20)
        L.addWidget(self.barra)
        L.addSpacing(6)
        self.l_eta = etiqueta("", "h3")
        L.addWidget(self.l_eta)
        chips = QHBoxLayout()
        chips.setSpacing(8)
        self.c_vel = etiqueta("", "chip")
        self.c_tiempo = etiqueta("", "chip")
        self.c_tam = etiqueta("", "chip")
        self.c_extra = etiqueta("", "chip")
        for c in (self.c_vel, self.c_tiempo, self.c_tam, self.c_extra):
            chips.addWidget(c)
        chips.addStretch()
        L.addLayout(chips)
        self.l_det = etiqueta("", "tenue", wrap=True)
        L.addWidget(self.l_det)
        L.addSpacing(16)
        self.botones = QHBoxLayout()
        self.botones.addStretch()
        L.addLayout(self.botones)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refrescar)

    def _limpiar_botones(self):
        while self.botones.count() > 1:
            it = self.botones.takeAt(1)
            if it.widget():
                it.widget().deleteLater()

    def empezar(self, tarea, titulo, origen, glifo):
        self.tarea = tarea
        self.icono.glifo = glifo
        self.icono.update()
        self.l_titulo.setText(titulo)
        self.l_origen.setText(origen)
        self.l_grande.setText("Buscando fotos…")
        self.l_pct.setText("")
        self.l_eta.setText("")
        self.l_det.setText("")
        for c in (self.c_vel, self.c_tiempo, self.c_tam, self.c_extra):
            c.hide()
        self.barra.setRange(0, 0)  # animación "buscando"
        self._limpiar_botones()
        b = boton("Cancelar", "secundario", self._cancelar)
        self.botones.addWidget(b)
        tarea.iniciar()
        self.timer.start(120)

    def _cancelar(self):
        if self.tarea and QMessageBox.question(self, "Foto Suprema",
                                               "¿Cancelar? Lo que ya se ha copiado se queda.") == QMessageBox.StandardButton.Yes:
            self.tarea.cancelar()

    def refrescar(self):
        t = self.tarea
        if t is None:
            return
        if t.fase == "escaneando":
            self.l_grande.setText(f"Buscando…  {N.num(t.encontradas_escaneo)}")
            self.l_eta.setText("Analizando la carpeta y todas sus subcarpetas")
        else:
            if self.barra.maximum() == 0:
                self.barra.setRange(0, 1000)
            self.barra.setValue(int(t.porcentaje() * 10))
            self.l_grande.setText(f"{t.verbo} {N.num(t.hechos)} de {N.num(t.total)}")
            self.l_pct.setText(f"{t.porcentaje():.1f} %".replace(".", ","))
            if t.fase != "fin":
                self.l_eta.setText(f"⏱  Tiempo estimado restante:  {N.tiempo_legible(t.eta())}")
            self.c_vel.setText(f"⚡ {t.por_segundo():.0f} archivos/s · {t.mb_por_segundo():.1f} MB/s".replace(".", ","))
            self.c_tiempo.setText(f"Transcurrido {N.tiempo_legible(t.transcurrido())}")
            self.c_tam.setText(f"{N.tamano_legible(t.bytes_hechos)} de {N.tamano_legible(t.bytes_total)}")
            extra = []
            if t.repetidas:
                extra.append(f"Ya existían: {N.num(t.repetidas)}")
            if t.errores:
                extra.append(f"Errores: {N.num(t.errores)}")
            self.c_extra.setText("  ·  ".join(extra))
            for c in (self.c_vel, self.c_tiempo, self.c_tam):
                c.show()
            self.c_extra.setVisible(bool(extra))
        if t.fase == "fin":
            self.timer.stop()
            self._fin()

    def _fin(self):
        t = self.tarea
        self.tarea = None
        self._limpiar_botones()
        if self.barra.maximum() == 0:
            self.barra.setRange(0, 1000)
        if t.error_fatal:
            self.l_grande.setText("Ha habido un problema")
            self.l_eta.setText(t.error_fatal)
        elif t.cancelado:
            self.l_grande.setText(f"Cancelado · {t.verbo.lower()} {N.num(t.copiadas)}")
            self.l_eta.setText("")
        else:
            self.barra.setValue(1000)
            self.l_pct.setText("100 %")
            self.l_grande.setText("¡Listo!")
            if isinstance(t, N.Organizador):
                años = sorted({k.split("/")[0] for k in t.carpetas_creadas})
                self.l_eta.setText(f"✅  {N.num(t.copiadas)} copiadas en {len(t.carpetas_creadas)} carpetas")
                det = ("Años: " + ", ".join(años)) if años else ""
                if t.origenes.get("archivo"):
                    det += f"\n{N.num(t.origenes['archivo'])} no tenían fecha en sus propiedades: se ha usado la fecha del archivo."
                self.l_det.setText(det)
            else:
                self.l_eta.setText(f"✅  Se han subido {N.num(t.copiadas)} archivos en {N.tiempo_legible(t.transcurrido())}")
        self.botones.addWidget(boton("Inicio", "secundario", self.v.ir_inicio))
        if isinstance(t, N.Organizador):
            self.botones.addWidget(boton("Abrir carpeta", "primario", lambda: abrir_en_sistema(t.destino), G["carpeta"]))
        elif self.v.bib.contar("pend"):
            self.botones.addWidget(boton("Empezar a revisar", "primario", lambda: self.v.ir_revision("pend"), G["foto"]))


# ======================================================================
# PÁGINA: REVISIÓN
# ======================================================================
class PaginaRevision(QWidget):
    def __init__(self, ventana):
        super().__init__()
        self.v = ventana
        self.setObjectName("pagina")
        self.cargador = ventana.cargador
        self.modo = None
        self.lista = []
        self.pos = 0
        self.historial = []
        self.saltadas = 0
        self._ultima_tecla = 0.0
        self._ruta_mostrada = None

        L = QVBoxLayout(self)
        L.setContentsMargins(26, 18, 26, 10)
        L.setSpacing(12)

        # --- barra superior
        top = QHBoxLayout()
        top.setSpacing(14)
        self.b_inicio = Circulo(G["atras"], TEXTO, 44, tip="Volver al inicio (Esc)")
        self.b_inicio.clicked.connect(self.v.ir_inicio)
        top.addWidget(self.b_inicio)
        self.l_titulo = etiqueta("", "h2")
        top.addWidget(self.l_titulo)
        top.addStretch()
        self.l_contador = etiqueta("", "chip")
        top.addWidget(self.l_contador)
        self.b_todo = boton("Borrar todo el borrador", "peligro", self.borrar_todo, G["borrar"])
        top.addWidget(self.b_todo)
        L.addLayout(top)
        self.barra = QProgressBar()
        self.barra.setObjectName("fina")
        self.barra.setFixedHeight(6)
        self.barra.setRange(0, 1000)
        L.addWidget(self.barra)

        # --- visor (foto / vídeo / final)
        self.marco = QFrame()
        self.marco.setObjectName("visor")
        ml = QVBoxLayout(self.marco)
        ml.setContentsMargins(8, 8, 8, 8)
        self.pila = QStackedWidget()
        ml.addWidget(self.pila)
        self.visor = VisorImagen()
        self.visor.cargar_full = self._cargar_full
        self.visor.zoom_cambiado.connect(self._zoom_cambiado)
        self.visor.redimensionado.connect(lambda: self.t_redim.start(140))
        self.pila.addWidget(self.visor)
        # vídeo
        cont_video = QWidget()
        cv = QVBoxLayout(cont_video)
        cv.setContentsMargins(0, 0, 0, 0)
        cv.setSpacing(8)
        self.video = QVideoWidget()
        self.video.setStyleSheet("background: black;")
        cv.addWidget(self.video, 1)
        controles = QHBoxLayout()
        controles.setContentsMargins(8, 2, 8, 4)
        controles.setSpacing(12)
        self.b_play = Circulo(G["pausa"], "#1c1d20", 50, relleno=True, color_relleno=NAR_B, tip="Reproducir / pausa (Espacio)")
        self.b_play.clicked.connect(self.play_pausa)
        controles.addWidget(self.b_play)
        self.l_t = etiqueta("0:00", "tenue")
        controles.addWidget(self.l_t)
        self.s_pos = QSlider(Qt.Orientation.Horizontal)
        self.s_pos.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.s_pos.sliderMoved.connect(lambda v: self.player.setPosition(v))
        self.s_pos.sliderPressed.connect(lambda: self.player.setPosition(self.s_pos.value()))
        controles.addWidget(self.s_pos, 1)
        self.l_dur = etiqueta("0:00", "tenue")
        controles.addWidget(self.l_dur)
        self.b_mute = Circulo(G["volumen"], TEXTO, 40, tip="Silenciar")
        self.b_mute.clicked.connect(self.silenciar)
        controles.addWidget(self.b_mute)
        self.s_vol = QSlider(Qt.Orientation.Horizontal)
        self.s_vol.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.s_vol.setRange(0, 100)
        self.s_vol.setFixedWidth(110)
        self.s_vol.valueChanged.connect(self._volumen)
        controles.addWidget(self.s_vol)
        cv.addLayout(controles)
        self.pila.addWidget(cont_video)
        # final
        self.fin = QWidget()
        fl = QVBoxLayout(self.fin)
        fl.addStretch()
        self.fin_icono = IconoCirculo(G["check"], 84, "#5fe0a8", VERDE)
        fl.addWidget(self.fin_icono, 0, Qt.AlignmentFlag.AlignHCenter)
        fl.addSpacing(10)
        self.fin_titulo = etiqueta("", "titulo")
        self.fin_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fl.addWidget(self.fin_titulo)
        self.fin_sub = etiqueta("", "tenue", wrap=True)
        self.fin_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fl.addWidget(self.fin_sub)
        fl.addSpacing(14)
        self.fin_botones = QHBoxLayout()
        self.fin_botones.addStretch()
        self.fin_botones.addStretch()
        fl.addLayout(self.fin_botones)
        fl.addStretch()
        self.pila.addWidget(self.fin)
        L.addWidget(self.marco, 1)
        self.toast = Toast(self.marco)

        # reproductor
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.player.setAudioOutput(self.audio)
        self.player.setVideoOutput(self.video)
        self.player.positionChanged.connect(self._pos_video)
        self.player.durationChanged.connect(self._dur_video)
        self.player.playbackStateChanged.connect(self._estado_video)
        self.player.errorOccurred.connect(self._error_video)
        vol = int(self.v.cfg.get("volumen", 70))
        self.s_vol.setValue(vol)
        self.audio.setVolume(vol / 100)

        # --- info
        info = QHBoxLayout()
        info.setSpacing(8)
        self.c_nombre = etiqueta("", "chip")
        self.c_res = etiqueta("", "chip")
        self.c_tam = etiqueta("", "chip")
        self.c_fecha = etiqueta("", "chip")
        self.c_cam = etiqueta("", "chip")
        for c in (self.c_nombre, self.c_res, self.c_tam, self.c_fecha, self.c_cam):
            info.addWidget(c)
        info.addStretch()
        self.c_zoom = etiqueta("", "chip")
        self.c_zoom.setStyleSheet(f"color: {NAR_A};")
        info.addWidget(self.c_zoom)
        info.addWidget(boton("Abrir en visor", "secundario", self.abrir_visor, G["abrir"]))
        L.addLayout(info)

        # --- miniaturas
        self.tira = QHBoxLayout()
        self.tira.setSpacing(10)
        self.minis = []
        for _ in range(12):
            m = QLabel()
            m.setFixedSize(108, 72)
            m.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.minis.append(m)
            self.tira.addWidget(m)
        self.tira.addStretch()
        L.addLayout(self.tira)

        # --- acciones
        acc = QHBoxLayout()
        acc.setSpacing(16)
        acc.addStretch()
        self.b_atras = BotonAccion(G["deshacer"], "Volver atrás", "Retroceso", TEXTO, self.volver_atras, 62)
        acc.addWidget(self.b_atras)
        sep = QFrame()
        sep.setFixedSize(1, 70)
        sep.setStyleSheet(f"background: {BORDE};")
        acc.addSpacing(14)
        acc.addWidget(sep)
        acc.addSpacing(14)
        self.b_elim = BotonAccion(G["borrar"], "Eliminar", "←", ROJO, lambda: self.accion("eliminar"))
        self.b_fav = BotonAccion(G["estrella"], "Favorito", "↑", NAR_A, lambda: self.accion("favorito"), relleno=True)
        self.b_mant = BotonAccion(G["check"], "Mantener", "→", VERDE, lambda: self.accion("mantener"))
        self.b_borrar = BotonAccion(G["borrar"], "Borrar para siempre", "←", ROJO, lambda: self.accion("borrar"))
        self.b_rest = BotonAccion(G["deshacer"], "Restaurar", "→", VERDE, lambda: self.accion("restaurar"))
        for b in (self.b_elim, self.b_fav, self.b_mant, self.b_borrar, self.b_rest):
            acc.addWidget(b)
        acc.addSpacing(14)
        sep2 = QFrame()
        sep2.setFixedSize(1, 70)
        sep2.setStyleSheet(f"background: {BORDE};")
        acc.addWidget(sep2)
        acc.addSpacing(14)
        self.b_saltar = BotonAccion(G["abajo"], "Saltar", "↓", GRIS, lambda: self.accion("saltar"), 62)
        acc.addWidget(self.b_saltar)
        acc.addStretch()
        L.addLayout(acc)
        pie = etiqueta(f"Rueda del ratón: zoom   ·   Espacio: reproducir vídeo   ·   V: abrir en visor   ·   Esc: inicio        {FIRMA}", "muytenue")
        pie.setAlignment(Qt.AlignmentFlag.AlignCenter)
        L.addWidget(pie)

        self.t_redim = QTimer(self)
        self.t_redim.setSingleShot(True)
        self.t_redim.timeout.connect(self.mostrar)
        self.t_minis = QTimer(self)
        self.t_minis.setSingleShot(True)
        self.t_minis.timeout.connect(self._pintar_minis)

    # ------------------------------------------------------------------
    def empezar(self, modo):
        self.modo = modo
        self.lista = self.v.bib.listar(modo)
        self.pos = 0
        self.historial = []
        self.saltadas = 0
        borr = modo == "draft"
        self.l_titulo.setText("Confirmar borradores" if borr else "Revisar fotos")
        self.b_todo.setVisible(borr)
        for b in (self.b_elim, self.b_fav, self.b_mant):
            b.setVisible(not borr)
        for b in (self.b_borrar, self.b_rest):
            b.setVisible(borr)
        self._ruta_mostrada = None
        QTimer.singleShot(0, self.mostrar)

    def salir(self):
        self._soltar_video()
        if self.modo == "draft":
            self.v.bib.purgar()
        self.modo = None

    def _actual(self):
        return self.lista[self.pos] if 0 <= self.pos < len(self.lista) else None

    def _tam_previa(self):
        dpr = self.visor.devicePixelRatioF()
        return max(200, int(self.visor.width() * dpr)), max(150, int(self.visor.height() * dpr))

    def mostrar(self):
        if self.modo is None:
            return
        total = len(self.lista)
        hechas = min(self.pos, total)
        self.l_contador.setText(f"{N.num(min(self.pos + 1, total))} / {N.num(total)}   ·   quedan {N.num(total - hechas)}")
        self.barra.setValue(int(hechas * 1000 / total) if total else 1000)
        self.b_atras.set_activo(bool(self.historial))
        self.b_atras.circulo.badge = str(len(self.historial)) if self.historial else ""
        self.b_atras.circulo.update()
        if self.modo == "draft":
            self.b_todo.setEnabled(self.v.bib.contar("draft") > 0)
        ruta = self._actual()
        for b in (self.b_elim, self.b_fav, self.b_mant, self.b_borrar, self.b_rest, self.b_saltar):
            b.set_activo(ruta is not None)

        if ruta is None:
            self._soltar_video()
            self._pantalla_final()
            self._pintar_minis()
            self._ruta_mostrada = None
            return

        if N.es_video(ruta):
            if self._ruta_mostrada != ruta:
                self.pila.setCurrentIndex(1)
                self.player.setSource(QUrl.fromLocalFile(ruta))
                self.player.play()
        else:
            if self._ruta_mostrada != ruta:
                self._soltar_video()
            self.pila.setCurrentIndex(0)
            w, h = self._tam_previa()
            im = self.cargador.previas.get((ruta, w, h))
            if im is None and (ruta, w, h) not in self.cargador.previas:
                try:
                    im = abrir_preparada(ruta, w, h)
                    with self.cargador.lock:
                        self.cargador.previas[(ruta, w, h)] = im
                except Exception:
                    im = None
            if im is None:
                self.visor.poner(None, "No se puede mostrar esta imagen\n(igualmente puedes clasificarla)")
            else:
                pm = QPixmap.fromImage(pil_a_qimage(im))
                pm.setDevicePixelRatio(self.visor.devicePixelRatioF())
                if self._ruta_mostrada == ruta and self.visor.zoom > 1.0:
                    self.visor.previa = pm  # solo cambió el tamaño de la ventana
                    self.visor.update()
                else:
                    self.visor.poner(pm)
        self._ruta_mostrada = ruta
        self._info(ruta)
        w, h = self._tam_previa()
        for r in self.lista[self.pos + 1:self.pos + 4]:
            self.cargador.pedir_previa(r, w, h)
            self.cargador.pedir_info(r)
        self.cargador.limpiar(set(self.lista[max(0, self.pos - 2):self.pos + 14]))
        self._pintar_minis()

    def _info(self, ruta):
        inf = self.cargador.infos.get(ruta)
        if inf is None:
            inf = N.info_archivo(ruta)
            with self.cargador.lock:
                self.cargador.infos[ruta] = inf
        nombre = inf["nombre"] if len(inf["nombre"]) < 42 else inf["nombre"][:39] + "…"
        self.c_nombre.setText(("🎬  " if inf["video"] else "📄  ") + nombre)
        self.c_nombre.setToolTip(ruta)
        self.c_res.setVisible(bool(inf["ancho"]))
        if inf["ancho"]:
            self.c_res.setText(f"{inf['ancho']} × {inf['alto']}")
        self.c_tam.setText(N.tamano_legible(inf["bytes"]))
        if inf["fecha"]:
            f = inf["fecha"]
            txt = f"📅  {f.day} {N.MESES[f.month - 1][:3].lower()} {f.year}"
            if inf["origen_fecha"] == "exif":
                txt += f"  {f:%H:%M}"
            elif inf["origen_fecha"] == "archivo":
                txt += "  (archivo)"
            self.c_fecha.setText(txt)
            self.c_fecha.show()
        else:
            self.c_fecha.hide()
        self.c_cam.setVisible(bool(inf["camara"]))
        self.c_cam.setText(f"📷  {inf['camara']}")

    def _pantalla_final(self):
        self.pila.setCurrentIndex(2)
        for c in (self.c_nombre, self.c_res, self.c_tam, self.c_fecha, self.c_cam):
            c.hide()
        self.c_zoom.hide()
        if self.modo == "draft":
            self.fin_titulo.setText("Borrador revisado")
        else:
            self.fin_titulo.setText("¡Has revisado todas!")
        sub = "Si te has equivocado en alguna, pulsa «Volver atrás» las veces que necesites."
        if self.saltadas:
            donde = "Borrador" if self.modo == "draft" else "Por revisar"
            sub = f"Has saltado {N.num(self.saltadas)}: siguen en «{donde}».\n" + sub
        self.fin_sub.setText(sub)
        while self.fin_botones.count() > 2:
            it = self.fin_botones.takeAt(1)
            if it.widget():
                it.widget().deleteLater()
        botones = [boton("Inicio", "secundario", self.v.ir_inicio)]
        if self.saltadas:
            botones.append(boton("Revisar las saltadas", "primario", lambda: self.v.ir_revision(self.modo)))
        elif self.modo == "pend" and self.v.bib.contar("draft"):
            botones.append(boton("Confirmar borradores", "primario", lambda: self.v.ir_revision("draft"), G["borrar"]))
        for i, b in enumerate(botones):
            self.fin_botones.insertWidget(1 + i, b)

    def _pintar_minis(self):
        falta = False
        for i, lab in enumerate(self.minis):
            idx = self.pos + i
            if idx >= len(self.lista):
                lab.clear()
                lab.setStyleSheet("background: transparent; border: none;")
                continue
            borde = f"2px solid {NAR_B}" if i == 0 else f"1px solid {BORDE}"
            lab.setStyleSheet(f"background: #202327; border: {borde}; border-radius: 10px; color: {TEXTO3};")
            ruta = self.lista[idx]
            if N.es_video(ruta):
                lab.setPixmap(QPixmap())
                lab.setFont(fuente_iconos(26))
                lab.setText(G["video"])
            elif ruta in self.cargador.minis:
                im = self.cargador.minis[ruta]
                if im is None:
                    lab.setText("?")
                else:
                    pm = QPixmap.fromImage(pil_a_qimage(im))
                    pm = pm.scaled(QSize(208, 136), Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                   Qt.TransformationMode.SmoothTransformation)
                    x = (pm.width() - 208) // 2
                    y = (pm.height() - 136) // 2
                    pm = pm.copy(max(0, x), max(0, y), 208, 136)
                    pm.setDevicePixelRatio(2.0)
                    lab.setPixmap(pm)
            else:
                lab.setPixmap(QPixmap())
                lab.setText("")
                self.cargador.pedir_mini(ruta)
                falta = True
        if falta:
            self.t_minis.start(200)

    # --- acciones ------------------------------------------------------
    def accion(self, tipo):
        ruta = self._actual()
        if ruta is None:
            return
        if N.es_video(ruta):
            self._soltar_video()   # Windows bloquea el archivo mientras se reproduce
        boton_ = {"eliminar": self.b_elim, "favorito": self.b_fav, "mantener": self.b_mant,
                  "borrar": self.b_borrar, "restaurar": self.b_rest, "saltar": self.b_saltar}[tipo]
        try:
            bib = self.v.bib
            reg = {"eliminar": bib.eliminar, "favorito": bib.favorito, "mantener": bib.mantener,
                   "restaurar": bib.restaurar, "borrar": bib.eliminar_definitivo,
                   "saltar": bib.saltar}[tipo](ruta)
        except Exception as e:
            QMessageBox.warning(self, "Foto Suprema", f"No se ha podido mover el archivo:\n{e}")
            return
        if tipo == "saltar":
            self.saltadas += 1
        boton_.circulo.destello()
        textos = {"eliminar": ("🗑  Enviada al borrador", "#ff8a8e"), "favorito": ("⭐  Favorita", NAR_A),
                  "mantener": ("✔  Mantenida", VERDE), "borrar": ("🗑  Borrada para siempre", "#ff8a8e"),
                  "restaurar": ("↩  Restaurada en Mantener", VERDE), "saltar": ("⏭  Saltada", TEXTO2)}
        self.toast.mostrar(*textos[tipo])
        self.historial.append(reg)
        self.pos += 1
        self.mostrar()

    def volver_atras(self):
        if not self.historial:
            return
        self._soltar_video()
        reg = self.historial.pop()
        try:
            ruta = self.v.bib.deshacer(reg)
        except Exception as e:
            QMessageBox.warning(self, "Foto Suprema", f"No se ha podido deshacer:\n{e}")
            return
        if reg["tipo"] == "saltar":
            self.saltadas = max(0, self.saltadas - 1)
        self.pos = max(0, self.pos - 1)
        if ruta:
            self.lista[self.pos] = ruta
        self.toast.mostrar("↶  Deshecho", TEXTO)
        self.b_atras.circulo.destello()
        self._ruta_mostrada = None
        self.mostrar()

    def borrar_todo(self):
        n = self.v.bib.contar("draft")
        if not n:
            return
        r = QMessageBox.warning(self, "Borrar todo el borrador",
                                f"Se van a borrar PARA SIEMPRE {N.num(n)} archivos del borrador.\n\nEsto no se puede deshacer. ¿Seguro?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                QMessageBox.StandardButton.No)
        if r != QMessageBox.StandardButton.Yes:
            return
        self._soltar_video()
        self.v.bib.purgar()
        borradas, liberado = self.v.bib.borrar_todo_borrador()
        QMessageBox.information(self, "Foto Suprema", f"Borradas {N.num(borradas)} · liberados {N.tamano_legible(liberado)}")
        self.v.ir_inicio()

    def abrir_visor(self):
        r = self._actual()
        if r:
            if N.es_video(r):
                self.player.pause()
            abrir_en_sistema(r)

    def _cargar_full(self):
        r = self._actual()
        if r is None or N.es_video(r):
            return None
        try:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            return QPixmap.fromImage(pil_a_qimage(abrir_preparada(r)))
        except Exception:
            return None
        finally:
            QApplication.restoreOverrideCursor()

    def _zoom_cambiado(self, txt):
        self.c_zoom.setVisible(bool(txt))
        self.c_zoom.setText(f"🔎  {txt}   ·   doble clic para ajustar")

    # --- vídeo ---------------------------------------------------------
    def _soltar_video(self):
        try:
            self.player.stop()
            self.player.setSource(QUrl())
        except Exception:
            pass
        QApplication.processEvents()

    def play_pausa(self):
        if self.pila.currentIndex() != 1:
            return
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def silenciar(self):
        m = not self.audio.isMuted()
        self.audio.setMuted(m)
        self.b_mute.glifo = G["mute"] if m else G["volumen"]
        self.b_mute.update()

    def _volumen(self, v):
        self.audio.setVolume(v / 100)
        self.v.cfg["volumen"] = v

    def _pos_video(self, ms):
        if not self.s_pos.isSliderDown():
            self.s_pos.setValue(int(ms))
        self.l_t.setText(fmt_ms(ms))

    def _dur_video(self, ms):
        self.s_pos.setRange(0, int(ms))
        self.l_dur.setText(fmt_ms(ms))

    def _estado_video(self, estado):
        jugando = estado == QMediaPlayer.PlaybackState.PlayingState
        self.b_play.glifo = G["pausa"] if jugando else G["play"]
        self.b_play.update()

    def _error_video(self, *_):
        if self.pila.currentIndex() == 1 and self._actual():
            self.toast.mostrar("No se puede reproducir aquí · pulsa V para abrirlo en tu reproductor", "#ff8a8e")

    # --- teclado -------------------------------------------------------
    def tecla(self, e):
        """Devuelve True si la tecla se ha usado."""
        k = _v(e.key())
        flechas = (K_IZQ, K_DER, K_ARR, K_ABA)
        if k in flechas:
            if e.isAutoRepeat():
                return True
            ahora = time.time()
            if ahora - self._ultima_tecla < 0.08:
                return True
            self._ultima_tecla = ahora
        ctrl = bool(e.modifiers() & Qt.KeyboardModifier.ControlModifier)
        if k == K_RET or (ctrl and k == K_Z):
            self.volver_atras()
        elif k == K_ESC:
            if self.visor.zoom > 1.0 and self.pila.currentIndex() == 0:
                self.visor.reset_zoom()
            else:
                self.v.ir_inicio()
        elif k == K_V:
            self.abrir_visor()
        elif k == K_ESP:
            self.play_pausa()
        elif k == K_ABA:
            self.accion("saltar")
        elif self.modo == "pend" and k in (K_IZQ, K_SUP):
            self.accion("eliminar")
        elif self.modo == "pend" and k == K_ARR:
            self.accion("favorito")
        elif self.modo == "pend" and k == K_DER:
            self.accion("mantener")
        elif self.modo == "draft" and k in (K_IZQ, K_SUP):
            self.accion("borrar")
        elif self.modo == "draft" and k == K_DER:
            self.accion("restaurar")
        else:
            return False
        return True


# ======================================================================
# VENTANA
# ======================================================================
class FiltroTeclas(QObject):
    def __init__(self, ventana):
        super().__init__()
        self.v = ventana

    def eventFilter(self, obj, e):
        if e.type() == QEvent.Type.KeyPress \
                and (obj is self.v or QApplication.activeWindow() is self.v) \
                and self.v.pila.currentWidget() is self.v.p_rev and self.v.p_rev.modo:
            return bool(self.v.p_rev.tecla(e))
        return False


class Ventana(QMainWindow):
    def __init__(self, raiz_biblioteca=None):
        super().__init__()
        self.setWindowTitle("Foto Suprema")
        try:
            self.setWindowIcon(QIcon(recurso("icono.ico")))
        except Exception:
            pass
        self.resize(1400, 900)
        self.setMinimumSize(1050, 700)
        self.cfg = N.cargar_config()
        self.cargador = Cargador()
        self.abrir_biblioteca(raiz_biblioteca or self.cfg.get("biblioteca") or N.biblioteca_por_defecto())

        raiz = QWidget()
        raiz.setObjectName("raiz")
        self.setCentralWidget(raiz)
        lay = QVBoxLayout(raiz)
        lay.setContentsMargins(0, 0, 0, 0)
        self.pila = QStackedWidget()
        lay.addWidget(self.pila)
        self.p_inicio = PaginaInicio(self)
        self.p_prog = PaginaProgreso(self)
        self.p_rev = PaginaRevision(self)
        for p in (self.p_inicio, self.p_prog, self.p_rev):
            self.pila.addWidget(p)
        self.filtro = FiltroTeclas(self)
        QApplication.instance().installEventFilter(self.filtro)
        self.ir_inicio()

    # ------------------------------------------------------------------
    def abrir_biblioteca(self, raiz):
        try:
            self.bib = N.Biblioteca(raiz)
        except Exception as e:
            QMessageBox.warning(None, "Foto Suprema", f"No se puede usar esa carpeta:\n{e}")
            raiz = N.biblioteca_por_defecto()
            self.bib = N.Biblioteca(raiz)
        self.bib.purgar()
        self.cfg["biblioteca"] = raiz
        N.guardar_config(self.cfg)

    def _ocupado(self):
        t = self.p_prog.tarea
        return t is not None and t.fase != "fin"

    def ir_inicio(self):
        if self.pila.currentWidget() is self.p_rev:
            self.p_rev.salir()
        self.p_inicio.refrescar()
        self.pila.setCurrentWidget(self.p_inicio)

    def ir_revision(self, modo):
        if self.pila.currentWidget() is self.p_rev:
            self.p_rev.salir()
        self.pila.setCurrentWidget(self.p_rev)
        self.p_rev.empezar(modo)

    def _tarea(self, tarea, titulo, origen, glifo):
        if self.pila.currentWidget() is self.p_rev:
            self.p_rev.salir()
        self.pila.setCurrentWidget(self.p_prog)
        self.p_prog.empezar(tarea, titulo, origen, glifo)

    def cambiar_biblioteca(self):
        r = QFileDialog.getExistingDirectory(self, "Elige dónde guardar la biblioteca", self.bib.raiz)
        if r:
            self.abrir_biblioteca(os.path.normpath(r))
            self.ir_inicio()

    def subir_carpeta(self):
        r = QFileDialog.getExistingDirectory(self, "Elige la carpeta con las fotos (se incluyen todas las subcarpetas)",
                                             self.cfg.get("ultima_subida", ""))
        if not r:
            return
        r = os.path.normpath(r)
        self.cfg["ultima_subida"] = r
        N.guardar_config(self.cfg)
        self._tarea(N.Importador(self.bib, [r]), "Subiendo fotos", r, G["subir"])

    def subir_sueltas(self):
        filtro = "Fotos y vídeos (" + " ".join("*" + e for e in sorted(N.EXTENSIONES)) + ");;Todos (*.*)"
        archivos, _ = QFileDialog.getOpenFileNames(self, "Elige fotos o vídeos", self.cfg.get("ultima_subida", ""), filtro)
        if archivos:
            self._tarea(N.Importador(self.bib, archivos), "Subiendo fotos", f"{len(archivos)} archivos elegidos", G["subir"])

    def organizar(self, por_meses):
        r = QFileDialog.getExistingDirectory(self, "¿Dónde quieres crear las carpetas organizadas?",
                                             self.cfg.get("ultimo_destino") or self.bib.raiz)
        if not r:
            return
        r = os.path.normpath(r)
        if os.path.normcase(r).startswith(os.path.normcase(self.bib.ruta("keep"))):
            QMessageBox.warning(self, "Foto Suprema", "Elige una carpeta que no esté dentro de «Mantener».")
            return
        self.cfg["ultimo_destino"] = r
        N.guardar_config(self.cfg)
        t = N.Organizador(self.bib, r, por_meses)
        self._tarea(t, "Organizando por años y meses" if por_meses else "Organizando por años", t.destino, G["calendario"])

    def closeEvent(self, e):
        if self._ocupado():
            if QMessageBox.question(self, "Foto Suprema", "Hay una tarea en marcha. ¿Seguro que quieres salir?") \
                    != QMessageBox.StandardButton.Yes:
                e.ignore()
                return
            self.p_prog.tarea.cancelar()
        try:
            self.p_rev.salir()
            self.bib.purgar()
        except Exception:
            pass
        N.guardar_config(self.cfg)
        e.accept()


# ======================================================================
# arranque
# ======================================================================
def preparar_app(app):
    app.setStyle("Fusion")
    app.setStyleSheet(QSS)
    f = QFont("Segoe UI")
    f.setPixelSize(14)
    app.setFont(f)


def iniciar(app=None):
    """Lo llama el lanzador (FotoSuprema.exe). Devuelve la ventana ya visible."""
    app = app or QApplication.instance() or QApplication(sys.argv)
    preparar_app(app)
    v = Ventana()
    v.showMaximized()
    return v


# ----------------------------------------------------------------------
# autoprueba (la ejecuta GitHub antes de crear el .exe)
# ----------------------------------------------------------------------
def autoprueba(carpeta_capturas):
    import tempfile
    os.makedirs(carpeta_capturas, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="fotosuprema_test_")
    N.RUTA_CONFIG = os.path.join(tmp, "config.json")
    origen = os.path.join(tmp, "pendrive")
    os.makedirs(os.path.join(origen, "Viaje", "Dia 2"), exist_ok=True)
    colores = [(230, 120, 40), (40, 120, 230), (60, 180, 110), (200, 60, 90), (240, 200, 60), (120, 80, 200)]
    for i in range(14):
        im = Image.new("RGB", (2400, 1600) if i % 3 else (1200, 1800), colores[i % len(colores)])
        ex = Image.Exif()
        ex.get_ifd(0x8769)[36867] = f"{2007 + i % 4}:{1 + i % 12:02d}:15 12:00:00"
        ex[271], ex[272] = "Apple", "iPhone 12"
        sub = ["", "Viaje", os.path.join("Viaje", "Dia 2")][i % 3]
        im.save(os.path.join(origen, sub, f"IMG_{i:04d}.jpg"), exif=ex, quality=85)
    with open(os.path.join(origen, "VID_20190101_120000.mp4"), "wb") as f:
        f.write(b"\x00" * 2048)  # vídeo falso: debe mostrar aviso sin romper nada

    app = QApplication.instance() or QApplication(sys.argv)
    preparar_app(app)
    v = Ventana(os.path.join(tmp, "Biblioteca"))
    v.resize(1500, 950)
    v.show()

    def esperar(seg=0.3):
        fin = time.time() + seg
        while time.time() < fin:
            app.processEvents()
            time.sleep(0.01)

    def captura(nombre):
        esperar(0.4)
        v.grab().save(os.path.join(carpeta_capturas, nombre))

    def tecla(k):
        ev = QKeyEvent(QEvent.Type.KeyPress, k, Qt.KeyboardModifier.NoModifier)
        v.p_rev._ultima_tecla = 0
        app.sendEvent(v, ev)
        esperar(0.15)

    captura("01_inicio_vacio.png")
    v._tarea(N.Importador(v.bib, [origen]), "Subiendo fotos", origen, G["subir"])
    limite = time.time() + 60
    while v.p_prog.tarea is not None and time.time() < limite:
        esperar(0.1)
    captura("02_subida_terminada.png")
    assert v.bib.contar("pend") == 15, v.bib.contar("pend")

    v.ir_revision("pend")
    esperar(0.8)
    captura("03_revision.png")
    tecla(Qt.Key.Key_Left)
    tecla(Qt.Key.Key_Up)
    tecla(Qt.Key.Key_Right)
    tecla(Qt.Key.Key_Down)
    assert v.p_rev.pos == 4, v.p_rev.pos
    v.p_rev.visor.aplicar_zoom(2.0)
    v.p_rev.visor.aplicar_zoom(1.5)
    captura("04_zoom.png")
    for _ in range(3):
        tecla(Qt.Key.Key_Backspace)
    assert v.p_rev.pos == 1 and v.bib.contar("fav") == 0, (v.p_rev.pos, v.bib.contar("fav"))
    tecla(Qt.Key.Key_Up)
    while v.p_rev._actual() is not None and not N.es_video(v.p_rev._actual()):
        tecla(Qt.Key.Key_Right)
    esperar(1.0)
    captura("05_video.png")
    tecla(Qt.Key.Key_Left)  # el vídeo al borrador (comprueba que se suelta el archivo)
    while v.p_rev._actual() is not None:
        tecla(Qt.Key.Key_Right)
    captura("06_final.png")
    assert v.bib.contar("pend") == 1, v.bib.contar("pend")  # la que se saltó

    v.ir_revision("draft")
    esperar(0.5)
    captura("07_borrador.png")
    tecla(Qt.Key.Key_Right)
    tecla(Qt.Key.Key_Left)
    tecla(Qt.Key.Key_Backspace)
    tecla(Qt.Key.Key_Left)
    v.ir_inicio()
    captura("08_inicio_con_datos.png")

    destino = os.path.join(tmp, "Organizadas")
    os.makedirs(destino)
    t = N.Organizador(v.bib, destino, True)
    v._tarea(t, "Organizando por años y meses", t.destino, G["calendario"])
    limite = time.time() + 60
    while v.p_prog.tarea is not None and time.time() < limite:
        esperar(0.1)
    captura("09_organizado.png")
    assert t.copiadas == v.bib.contar("keep") and t.errores == 0, (t.copiadas, t.errores)
    años = {k.split("/")[0] for k in t.carpetas_creadas}
    assert años <= {"2007", "2008", "2009", "2010", "2019"}, años
    v.close()
    print("AUTOPRUEBA OK:", v.bib.stats)
    return 0


def main():
    if "--autoprueba" in sys.argv:
        i = sys.argv.index("--autoprueba")
        destino = sys.argv[i + 1] if len(sys.argv) > i + 1 else "capturas"
        sys.exit(autoprueba(destino))
    app = QApplication(sys.argv)
    ventana = iniciar(app)  # noqa: F841
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
