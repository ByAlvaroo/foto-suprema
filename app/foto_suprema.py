"""
FOTO SUPREMA - organizador de fotos
HECHO POR @BYALVARO__
"""
import os
import sys
import time
import queue
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from PIL import Image, ImageOps, ImageTk

import nucleo as N

# nitidez en pantallas con escalado (125 %, 150 %…)
if os.name == "nt":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

# ----------------------------------------------------------------------
# estilo
# ----------------------------------------------------------------------
BG = "#121419"
PANEL = "#1c2029"
PANEL2 = "#252a35"
BORDE = "#2f3542"
TEXTO = "#eceff4"
TEXTO2 = "#9aa3b2"
ACENTO = "#7c5cff"
ROJO = "#e5484d"
AMARILLO = "#f5b301"
VERDE = "#30a46c"
AZUL = "#3e8ed0"
GRIS = "#5b6474"
F = "Segoe UI"

FIRMA = "HECHO POR @BYALVARO__"


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
        messagebox.showerror("Foto Suprema", f"No se ha podido abrir:\n{e}")


def aclarar(color, f=0.15):
    color = color.lstrip("#")
    r, g, b = (int(color[i:i + 2], 16) for i in (0, 2, 4))
    r, g, b = (min(255, int(c + (255 - c) * f)) for c in (r, g, b))
    return f"#{r:02x}{g:02x}{b:02x}"


class Boton(tk.Label):
    """Botón plano con efecto al pasar el ratón (funciona igual en todos los Windows)."""

    def __init__(self, padre, texto, color, comando, tam=12, pad=(18, 10), negrita=True, fg="white", ancho=None):
        super().__init__(padre, text=texto, bg=color, fg=fg, cursor="hand2",
                         font=(F, tam, "bold" if negrita else "normal"),
                         padx=pad[0], pady=pad[1])
        if ancho:
            self.configure(width=ancho)
        self.color = color
        self.comando = comando
        self.activo = True
        self.bind("<Enter>", lambda e: self.activo and self.configure(bg=aclarar(self.color)))
        self.bind("<Leave>", lambda e: self.configure(bg=self.color if self.activo else PANEL2))
        self.bind("<Button-1>", self._click)

    def _click(self, _e):
        if self.activo and self.comando:
            self.comando()

    def set_activo(self, activo):
        self.activo = activo
        self.configure(bg=self.color if activo else PANEL2,
                       fg="white" if activo else GRIS,
                       cursor="hand2" if activo else "arrow")

    def set_texto(self, t):
        self.configure(text=t)


# ----------------------------------------------------------------------
# carga de imágenes en segundo plano
# ----------------------------------------------------------------------
def abrir_preparada(ruta, max_w=None, max_h=None):
    """Abre una foto girada según su EXIF y, si se pide, reducida para pantalla.
    La foto original NUNCA se modifica (solo se lee)."""
    im = Image.open(ruta)
    if max_w and max_h and im.format == "JPEG":
        try:
            lado = max(max_w, max_h)
            im.draft("RGB", (lado, lado))  # lectura rápida a menor tamaño
        except Exception:
            pass
    im = ImageOps.exif_transpose(im)
    if im.mode not in ("RGB", "RGBA"):
        im = im.convert("RGBA" if "A" in im.getbands() or im.mode == "P" else "RGB")
    if max_w and max_h:
        im.thumbnail((max_w, max_h), Image.LANCZOS)
    else:
        im.load()
    return im


class Cargador:
    """Hilo que prepara la vista previa de las siguientes fotos y las miniaturas."""

    def __init__(self):
        self.cola = queue.Queue()
        self.previas = {}      # (ruta, w, h) -> PIL
        self.minis = {}        # ruta -> PIL
        self.infos = {}        # ruta -> dict
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
            self._limpiar_resto(mantener)

    def _limpiar_resto(self, mantener):
        if True:
            if len(self.minis) > 400:
                for k in list(self.minis)[:200]:
                    if k not in mantener:
                        del self.minis[k]
            if len(self.infos) > 400:
                for k in list(self.infos)[:200]:
                    if k not in mantener:
                        del self.infos[k]

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
                    im = None if N.es_video(ruta) else abrir_preparada(ruta, 150, 100)
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
# aplicación
# ----------------------------------------------------------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Foto Suprema")
        self.configure(bg=BG)
        self.geometry("1280x820")
        self.minsize(1000, 680)
        try:
            self.state("zoomed")
        except Exception:
            pass
        try:
            self.iconbitmap(recurso("icono.ico"))
        except Exception:
            pass

        estilo = ttk.Style(self)
        try:
            estilo.theme_use("clam")
        except Exception:
            pass
        estilo.configure("S.Horizontal.TProgressbar", troughcolor=PANEL2, background=ACENTO,
                         bordercolor=PANEL2, lightcolor=ACENTO, darkcolor=ACENTO, thickness=28)
        estilo.configure("Fina.Horizontal.TProgressbar", troughcolor=PANEL2, background=ACENTO,
                         bordercolor=PANEL2, lightcolor=ACENTO, darkcolor=ACENTO, thickness=6)

        self.cfg = N.cargar_config()
        raiz = self.cfg.get("biblioteca") or N.biblioteca_por_defecto()
        self.abrir_biblioteca(raiz)

        self.cargador = Cargador()
        self.modo = None           # None | "pend" | "draft"
        self.tarea = None
        self._ultimo_tecla = 0

        self.cuerpo = tk.Frame(self, bg=BG)
        self.cuerpo.pack(fill="both", expand=True)

        self.bind_all("<Key>", self.on_tecla)
        self.protocol("WM_DELETE_WINDOW", self.cerrar)
        self.pantalla_inicio()

    # ------------------------------------------------------------------
    def abrir_biblioteca(self, raiz):
        try:
            self.bib = N.Biblioteca(raiz)
        except Exception as e:
            messagebox.showerror("Foto Suprema", f"No se puede usar esa carpeta:\n{e}")
            raiz = N.biblioteca_por_defecto()
            self.bib = N.Biblioteca(raiz)
        self.bib.purgar()
        self.cfg["biblioteca"] = raiz
        N.guardar_config(self.cfg)

    def limpiar(self):
        if self.modo == "draft":
            self.bib.purgar()
        self.modo = None
        for w in self.cuerpo.winfo_children():
            w.destroy()

    def cerrar(self):
        if self.tarea and self.tarea.fase != "fin":
            if not messagebox.askyesno("Foto Suprema", "Hay una tarea en marcha. ¿Seguro que quieres salir?"):
                return
            self.tarea.cancelar()
        try:
            self.bib.purgar()
        except Exception:
            pass
        self.destroy()

    def pie(self, padre):
        tk.Label(padre, text=FIRMA, bg=BG, fg=GRIS, font=(F, 9, "bold")).pack(side="bottom", pady=8)

    # ==================================================================
    # INICIO
    # ==================================================================
    def pantalla_inicio(self):
        self.limpiar()
        c = self.cuerpo
        self.pie(c)

        cont = tk.Frame(c, bg=BG)
        cont.pack(fill="both", expand=True, padx=40, pady=(24, 0))

        cab = tk.Frame(cont, bg=BG)
        cab.pack(fill="x")
        tk.Label(cab, text="📸 Foto Suprema", bg=BG, fg=TEXTO, font=(F, 30, "bold")).pack(side="left")
        tk.Label(cab, text="   Organiza miles de fotos en minutos", bg=BG, fg=TEXTO2,
                 font=(F, 13)).pack(side="left", pady=(14, 0))

        # biblioteca
        fila = tk.Frame(cont, bg=PANEL, highlightbackground=BORDE, highlightthickness=1)
        fila.pack(fill="x", pady=(18, 14))
        tk.Label(fila, text="📁 Biblioteca:", bg=PANEL, fg=TEXTO2, font=(F, 11)).pack(side="left", padx=(14, 6), pady=10)
        tk.Label(fila, text=self.bib.raiz, bg=PANEL, fg=TEXTO, font=(F, 11, "bold"),
                 anchor="w").pack(side="left", fill="x", expand=True)
        Boton(fila, "Abrir carpeta", PANEL2, lambda: abrir_en_sistema(self.bib.raiz), 10, (12, 6)).pack(side="right", padx=(4, 10), pady=8)
        Boton(fila, "Cambiar", PANEL2, self.cambiar_biblioteca, 10, (12, 6)).pack(side="right", padx=4, pady=8)

        # tarjetas con contadores
        n_pend, n_keep = self.bib.contar("pend"), self.bib.contar("keep")
        n_fav, n_draft = self.bib.contar("fav"), self.bib.contar("draft")
        tarjetas = tk.Frame(cont, bg=BG)
        tarjetas.pack(fill="x")
        for i, (titulo, n, color, clave) in enumerate([
                ("Por revisar", n_pend, ACENTO, "pend"),
                ("Mantener", n_keep, VERDE, "keep"),
                ("Favoritos", n_fav, AMARILLO, "fav"),
                ("Borrador", n_draft, ROJO, "draft")]):
            t = tk.Frame(tarjetas, bg=PANEL, highlightbackground=BORDE, highlightthickness=1, cursor="hand2")
            t.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 7, 0 if i == 3 else 7))
            tarjetas.columnconfigure(i, weight=1, uniform="t")
            tk.Frame(t, bg=color, height=4).pack(fill="x")
            l1 = tk.Label(t, text=N.num(n), bg=PANEL, fg=TEXTO, font=(F, 24, "bold"))
            l1.pack(anchor="w", padx=16, pady=(10, 0))
            l2 = tk.Label(t, text=titulo, bg=PANEL, fg=TEXTO2, font=(F, 11))
            l2.pack(anchor="w", padx=16, pady=(0, 12))
            ruta = self.bib.ruta(clave)
            for w in (t, l1, l2):
                w.bind("<Button-1>", lambda e, r=ruta: abrir_en_sistema(r))

        # acciones
        acc = tk.Frame(cont, bg=BG)
        acc.pack(fill="x", pady=18)
        for i in range(3):
            acc.columnconfigure(i, weight=1, uniform="a")

        def gran(fila_, col, emoji, titulo, sub, color, cmd, activo=True):
            f = tk.Frame(acc, bg=PANEL, highlightbackground=BORDE, highlightthickness=1)
            f.grid(row=fila_, column=col, sticky="nsew", padx=7, pady=7)
            fila_t = tk.Frame(f, bg=PANEL)
            fila_t.pack(anchor="w", padx=16, pady=(12, 0))
            tk.Label(fila_t, text=emoji, bg=PANEL, fg=color, font=(F, 18)).pack(side="left")
            tk.Label(fila_t, text="  " + titulo, bg=PANEL, fg=TEXTO, font=(F, 14, "bold")).pack(side="left")
            tk.Label(f, text=sub, bg=PANEL, fg=TEXTO2, font=(F, 10), justify="left",
                     wraplength=330).pack(anchor="w", padx=16, pady=(2, 10))
            b = Boton(f, "Empezar  →", color, cmd, 11, (14, 7))
            b.pack(anchor="w", padx=16, pady=(0, 14))
            b.set_activo(activo)
            return b

        gran(0, 0, "⬆", "Subir una carpeta", "Copia todas las fotos y vídeos de la carpeta y de todas sus subcarpetas. Los originales no se tocan.",
             ACENTO, self.subir_carpeta)
        gran(0, 1, "🖼", "Revisar fotos", f"{N.num(n_pend)} por revisar.  ← eliminar · ↑ favorito · → mantener",
             VERDE, lambda: self.pantalla_revision("pend"), n_pend > 0)
        gran(0, 2, "🗑", "Confirmar borradores", f"{N.num(n_draft)} en el borrador. Bórralas para siempre o restáuralas.",
             ROJO, lambda: self.pantalla_revision("draft"), n_draft > 0)
        gran(1, 0, "➕", "Subir fotos sueltas", "Elige una o varias fotos o vídeos concretos.",
             ACENTO, self.subir_sueltas)
        gran(1, 1, "📅", "Organizar por años", "Copia lo de «Mantener» en carpetas 2007, 2008… (solo las que tengan fotos).",
             AZUL, lambda: self.organizar(False), n_keep > 0)
        gran(1, 2, "🗓", "Organizar por años y meses", "Igual, pero dentro de cada año: 01 - Enero, 02 - Febrero…",
             AZUL, lambda: self.organizar(True), n_keep > 0)

        # estadísticas
        s = self.bib.stats
        est = tk.Frame(cont, bg=PANEL, highlightbackground=BORDE, highlightthickness=1)
        est.pack(fill="x", padx=7)
        tk.Label(est, text="📊 Tus estadísticas", bg=PANEL, fg=TEXTO, font=(F, 12, "bold")).grid(
            row=0, column=0, columnspan=7, sticky="w", padx=16, pady=(10, 4))
        datos = [
            ("Subidas", N.num(s["subidas"]), ACENTO),
            ("Mantenidas", N.num(s["mantenidas"] + s["favoritas"]), VERDE),
            ("Favoritas", N.num(s["favoritas"]), AMARILLO),
            ("Al borrador", N.num(s["eliminadas"]), ROJO),
            ("Borradas del todo", N.num(s["borradas_def"]), ROJO),
            ("Espacio liberado", N.tamano_legible(s["bytes_liberados"]), VERDE),
            ("Organizadas", N.num(s["organizadas"]), AZUL),
        ]
        for i, (t, v, col) in enumerate(datos):
            est.columnconfigure(i, weight=1, uniform="e")
            tk.Label(est, text=v, bg=PANEL, fg=col, font=(F, 16, "bold")).grid(row=1, column=i, sticky="w", padx=16)
            tk.Label(est, text=t, bg=PANEL, fg=TEXTO2, font=(F, 9)).grid(row=2, column=i, sticky="w", padx=16, pady=(0, 12))

    def cambiar_biblioteca(self):
        r = filedialog.askdirectory(title="Elige dónde guardar la biblioteca (se crearán las carpetas dentro)",
                                    initialdir=self.bib.raiz)
        if r:
            self.abrir_biblioteca(os.path.normpath(r))
            self.pantalla_inicio()

    # ==================================================================
    # SUBIR / ORGANIZAR (barra de progreso)
    # ==================================================================
    def subir_carpeta(self):
        r = filedialog.askdirectory(title="Elige la carpeta con las fotos (se incluyen todas las subcarpetas)",
                                    initialdir=self.cfg.get("ultima_subida") or "/")
        if not r:
            return
        self.cfg["ultima_subida"] = r
        N.guardar_config(self.cfg)
        self.lanzar(N.Importador(self.bib, [os.path.normpath(r)]), "Subiendo fotos", r)

    def subir_sueltas(self):
        tipos = " ".join("*" + e for e in sorted(N.EXTENSIONES))
        archivos = filedialog.askopenfilenames(title="Elige fotos o vídeos",
                                               filetypes=[("Fotos y vídeos", tipos), ("Todos", "*.*")],
                                               initialdir=self.cfg.get("ultima_subida") or "/")
        if archivos:
            self.lanzar(N.Importador(self.bib, list(archivos)), "Subiendo fotos", f"{len(archivos)} archivos elegidos")

    def organizar(self, por_meses):
        r = filedialog.askdirectory(title="¿Dónde quieres crear las carpetas organizadas?",
                                    initialdir=self.cfg.get("ultimo_destino") or self.bib.raiz)
        if not r:
            return
        r = os.path.normpath(r)
        if os.path.normcase(r).startswith(os.path.normcase(self.bib.ruta("keep"))):
            messagebox.showwarning("Foto Suprema", "Elige una carpeta que no esté dentro de «Mantener».")
            return
        self.cfg["ultimo_destino"] = r
        N.guardar_config(self.cfg)
        t = N.Organizador(self.bib, r, por_meses)
        self.lanzar(t, "Organizando por años y meses" if por_meses else "Organizando por años", t.destino)

    def lanzar(self, tarea, titulo, origen):
        self.limpiar()
        self.tarea = tarea
        c = self.cuerpo
        self.pie(c)
        caja = tk.Frame(c, bg=PANEL, highlightbackground=BORDE, highlightthickness=1)
        caja.place(relx=0.5, rely=0.45, anchor="center")

        tk.Label(caja, text=titulo, bg=PANEL, fg=TEXTO, font=(F, 22, "bold")).pack(pady=(28, 2), padx=50)
        tk.Label(caja, text=origen, bg=PANEL, fg=TEXTO2, font=(F, 10), wraplength=740).pack()

        self.p_grande = tk.Label(caja, text="Buscando fotos…", bg=PANEL, fg=TEXTO, font=(F, 26, "bold"))
        self.p_grande.pack(pady=(30, 4))
        self.p_pct = tk.Label(caja, text="", bg=PANEL, fg=ACENTO, font=(F, 18, "bold"))
        self.p_pct.pack()
        self.p_barra = ttk.Progressbar(caja, style="S.Horizontal.TProgressbar", maximum=100, length=700)
        self.p_barra.pack(pady=16)
        self.p_eta = tk.Label(caja, text="", bg=PANEL, fg=TEXTO, font=(F, 14))
        self.p_eta.pack()
        self.p_det = tk.Label(caja, text="", bg=PANEL, fg=TEXTO2, font=(F, 11), justify="center")
        self.p_det.pack(pady=(8, 0))

        self.p_botones = tk.Frame(caja, bg=PANEL)
        self.p_botones.pack(side="bottom", pady=24)
        self.p_cancelar = Boton(self.p_botones, "Cancelar", PANEL2, self._cancelar_tarea, 11)
        self.p_cancelar.pack()

        tarea.iniciar()
        self.after(120, self._refrescar_tarea)

    def _cancelar_tarea(self):
        if self.tarea and messagebox.askyesno("Foto Suprema", "¿Cancelar? Lo que ya se ha copiado se queda."):
            self.tarea.cancelar()

    def _refrescar_tarea(self):
        t = self.tarea
        if t is None or not self.p_grande.winfo_exists():
            return
        if t.fase == "escaneando":
            self.p_grande.configure(text=f"Buscando fotos…  {N.num(t.encontradas_escaneo)} encontradas")
            self.p_barra.configure(mode="indeterminate")
            self.p_barra.step(3)
        else:
            self.p_barra.configure(mode="determinate")
            self.p_barra["value"] = t.porcentaje()
            self.p_grande.configure(text=f"{t.verbo} {N.num(t.hechos)} de {N.num(t.total)}")
            self.p_pct.configure(text=f"{t.porcentaje():.1f} %".replace(".", ","))
            if t.fase != "fin":
                self.p_eta.configure(text=f"⏱ Tiempo estimado restante: {N.tiempo_legible(t.eta())}")
            det = (f"Velocidad: {t.por_segundo():.0f} archivos/s · {t.mb_por_segundo():.1f} MB/s   ·   "
                   f"Transcurrido: {N.tiempo_legible(t.transcurrido())}\n"
                   f"{N.tamano_legible(t.bytes_hechos)} de {N.tamano_legible(t.bytes_total)}")
            if t.repetidas:
                det += f"   ·   Ya existían (saltadas): {N.num(t.repetidas)}"
            if t.errores:
                det += f"   ·   Errores: {N.num(t.errores)}"
            self.p_det.configure(text=det)
        if t.fase == "fin":
            self._fin_tarea()
            return
        self.after(150, self._refrescar_tarea)

    def _fin_tarea(self):
        t = self.tarea
        self.p_barra["value"] = 100 if not t.cancelado else t.porcentaje()
        for w in self.p_botones.winfo_children():
            w.destroy()
        if t.error_fatal:
            self.p_grande.configure(text="❌ Ha habido un problema")
            self.p_eta.configure(text=t.error_fatal)
        elif t.cancelado:
            self.p_grande.configure(text=f"Cancelado · {t.verbo.lower()} {N.num(t.copiadas)}")
            self.p_eta.configure(text="")
        else:
            self.p_grande.configure(text="✅ ¡Listo!")
            if isinstance(t, N.Organizador):
                años = sorted({k.split("/")[0] for k in t.carpetas_creadas})
                txt = f"{N.num(t.copiadas)} copiadas en {len(t.carpetas_creadas)} carpetas"
                self.p_eta.configure(text=txt)
                extra = "Años: " + ", ".join(años) if años else ""
                if t.origenes.get("archivo"):
                    extra += f"\n{N.num(t.origenes['archivo'])} sin fecha en sus propiedades: se ha usado la fecha del archivo"
                self.p_det.configure(text=extra)
            else:
                self.p_eta.configure(text=f"Se han subido {N.num(t.copiadas)} archivos en {N.tiempo_legible(t.transcurrido())}")
        self.tarea = None
        Boton(self.p_botones, "Inicio", PANEL2, self.pantalla_inicio, 12).pack(side="left", padx=6)
        if isinstance(t, N.Organizador):
            Boton(self.p_botones, "📂 Abrir carpeta", AZUL, lambda: abrir_en_sistema(t.destino), 12).pack(side="left", padx=6)
        elif self.bib.contar("pend"):
            Boton(self.p_botones, "Empezar a revisar  →", VERDE, lambda: self.pantalla_revision("pend"), 12).pack(side="left", padx=6)

    # ==================================================================
    # REVISIÓN (por revisar  /  borrador)
    # ==================================================================
    def pantalla_revision(self, modo):
        self.limpiar()
        self.modo = modo
        self.lista = self.bib.listar(modo)
        self.pos = 0
        self.historial = []
        self.saltadas = 0
        self.zoom = 1.0
        self.full = None
        self.centro = None
        self._foto_tk = None
        self._minis_tk = []
        self._render_id = None
        self._ultimo_tam = (0, 0)
        es_borr = modo == "draft"
        c = self.cuerpo

        # barra superior
        top = tk.Frame(c, bg=BG)
        top.pack(fill="x", padx=18, pady=(12, 4))
        Boton(top, "←  Inicio", PANEL2, self.pantalla_inicio, 11, (14, 7)).pack(side="left")
        tk.Label(top, text="🗑 Confirmar borradores" if es_borr else "🖼 Revisar fotos", bg=BG, fg=TEXTO,
                 font=(F, 17, "bold")).pack(side="left", padx=16)
        if es_borr:
            self.b_todo = Boton(top, "Borrar TODO el borrador", ROJO, self.borrar_todo, 10, (12, 7))
            self.b_todo.pack(side="right")
        self.l_contador = tk.Label(top, text="", bg=BG, fg=TEXTO2, font=(F, 12))
        self.l_contador.pack(side="right", padx=14)
        self.barra_rev = ttk.Progressbar(c, style="Fina.Horizontal.TProgressbar", maximum=100)
        self.barra_rev.pack(fill="x", padx=18)

        # pie con firma y ayuda de teclas
        self.pie(c)
        if es_borr:
            ayuda = "←  Borrar para siempre      →  Restaurar (a Mantener)      ↓  Saltar      Retroceso  Volver atrás      Rueda  Zoom      V  Abrir en visor"
        else:
            ayuda = "←  Eliminar (al borrador)      ↑  Favorito      →  Mantener      ↓  Saltar      Retroceso  Volver atrás      Rueda  Zoom      V  Abrir en visor"
        tk.Label(c, text=ayuda, bg=BG, fg=TEXTO2, font=(F, 10)).pack(side="bottom")

        # botones de acción
        bots = tk.Frame(c, bg=BG)
        bots.pack(side="bottom", pady=(6, 4))
        self.b_atras = Boton(bots, "↶  Volver atrás", PANEL2, self.volver_atras, 13, (18, 12))
        self.b_atras.pack(side="left", padx=(0, 26))
        if es_borr:
            self.b_acc = [
                Boton(bots, "←  Borrar para siempre", ROJO, lambda: self.accion("borrar"), 14, (24, 12)),
                Boton(bots, "→  Restaurar", VERDE, lambda: self.accion("restaurar"), 14, (24, 12)),
            ]
        else:
            self.b_acc = [
                Boton(bots, "←  🗑 Eliminar", ROJO, lambda: self.accion("eliminar"), 14, (24, 12)),
                Boton(bots, "↑  ⭐ Favorito", AMARILLO, lambda: self.accion("favorito"), 14, (24, 12), fg="#1a1a1a"),
                Boton(bots, "→  ✔ Mantener", VERDE, lambda: self.accion("mantener"), 14, (24, 12)),
            ]
        for b in self.b_acc:
            b.pack(side="left", padx=6)
        self.b_saltar = Boton(bots, "↓  Saltar", PANEL2, lambda: self.accion("saltar"), 13, (18, 12))
        self.b_saltar.pack(side="left", padx=(26, 0))

        # tira de miniaturas
        self.tira = tk.Canvas(c, bg=BG, height=104, highlightthickness=0)
        self.tira.pack(side="bottom", fill="x", padx=18, pady=(4, 2))

        # info
        info = tk.Frame(c, bg=BG)
        info.pack(side="bottom", fill="x", padx=18, pady=(4, 0))
        self.l_info = tk.Label(info, text="", bg=BG, fg=TEXTO, font=(F, 11), anchor="w")
        self.l_info.pack(side="left", fill="x", expand=True)
        Boton(info, "🔍 Abrir en visor", PANEL2, self.abrir_visor, 10, (12, 5), negrita=False).pack(side="right")
        self.l_zoom = tk.Label(info, text="", bg=BG, fg=ACENTO, font=(F, 10, "bold"))
        self.l_zoom.pack(side="right", padx=10)

        # lienzo de la foto
        self.lienzo = tk.Canvas(c, bg="#0b0c0f", highlightthickness=0)
        self.lienzo.pack(fill="both", expand=True, padx=18, pady=(8, 0))
        self.lienzo.bind("<Configure>", self._al_redimensionar)
        self.lienzo.bind("<MouseWheel>", self._rueda)
        self.lienzo.bind("<Button-4>", lambda e: self._rueda(e, 120))
        self.lienzo.bind("<Button-5>", lambda e: self._rueda(e, -120))
        self.lienzo.bind("<ButtonPress-1>", self._arrastre_ini)
        self.lienzo.bind("<B1-Motion>", self._arrastre)
        self.lienzo.bind("<Double-Button-1>", lambda e: self._reset_zoom(True))

        self.after(60, self.mostrar)

    # --- utilidades de revisión ---------------------------------------
    def _tam_lienzo(self):
        w = max(200, self.lienzo.winfo_width())
        h = max(200, self.lienzo.winfo_height())
        return w, h

    def _actual(self):
        if 0 <= self.pos < len(self.lista):
            return self.lista[self.pos]
        return None

    def _al_redimensionar(self, e):
        if (e.width, e.height) == self._ultimo_tam:
            return
        self._ultimo_tam = (e.width, e.height)
        if self._render_id:
            self.after_cancel(self._render_id)
        self._render_id = self.after(120, self.mostrar)

    def mostrar(self):
        if self.modo is None or not self.lienzo.winfo_exists():
            return
        self._render_id = None
        total = len(self.lista)
        hechas = min(self.pos, total)
        self.l_contador.configure(
            text=f"Foto {N.num(min(self.pos + 1, total))} de {N.num(total)}   ·   quedan {N.num(total - hechas)}")
        self.barra_rev["value"] = (hechas * 100 / total) if total else 100
        self.b_atras.set_activo(bool(self.historial))
        self.b_atras.set_texto(f"↶  Volver atrás ({len(self.historial)})" if self.historial else "↶  Volver atrás")
        if self.modo == "draft":
            restantes = total - hechas
            self.b_todo.set_activo(restantes > 0)

        ruta = self._actual()
        for b in self.b_acc + [self.b_saltar]:
            b.set_activo(ruta is not None)
        self.lienzo.delete("all")
        self.full = None
        self.zoom = 1.0
        self.centro = None
        self.l_zoom.configure(text="")
        if ruta is None:
            self._pantalla_final()
            self._dibujar_tira()
            return

        w, h = self._tam_lienzo()
        if N.es_video(ruta):
            self._foto_tk = None
            self.lienzo.create_text(w // 2, h // 2 - 30, text="🎬", fill=TEXTO2, font=(F, 70))
            self.lienzo.create_text(w // 2, h // 2 + 50, text="Vídeo  ·  pulsa V o «Abrir en visor» para verlo",
                                    fill=TEXTO2, font=(F, 14))
        else:
            im = self.cargador.previas.get((ruta, w, h))
            if im is None and (ruta, w, h) not in self.cargador.previas:
                try:
                    im = abrir_preparada(ruta, w, h)
                    with self.cargador.lock:
                        self.cargador.previas[(ruta, w, h)] = im
                except Exception:
                    im = None
            if im is None:
                self._foto_tk = None
                self.lienzo.create_text(w // 2, h // 2, text="No se puede mostrar esta imagen\n(igualmente puedes clasificarla)",
                                        fill=TEXTO2, font=(F, 14), justify="center")
            else:
                self._foto_tk = ImageTk.PhotoImage(im)
                self.lienzo.create_image(w // 2, h // 2, image=self._foto_tk, anchor="center")

        self._mostrar_info(ruta)
        # precargar las siguientes
        siguientes = self.lista[self.pos + 1:self.pos + 4]
        for r in siguientes:
            self.cargador.pedir_previa(r, w, h)
            self.cargador.pedir_info(r)
        self.cargador.limpiar(set(self.lista[max(0, self.pos - 2):self.pos + 12]))
        self._dibujar_tira()

    def _mostrar_info(self, ruta):
        inf = self.cargador.infos.get(ruta)
        if inf is None:
            inf = N.info_archivo(ruta)
            with self.cargador.lock:
                self.cargador.infos[ruta] = inf
        partes = [f"📄 {inf['nombre']}"]
        if inf["ancho"]:
            partes.append(f"{inf['ancho']} × {inf['alto']} px")
        partes.append(N.tamano_legible(inf["bytes"]))
        if inf["fecha"]:
            f = inf["fecha"]
            txt = f"📅 {f.day} de {N.MESES[f.month - 1].lower()} de {f.year}"
            if inf["origen_fecha"] == "exif":
                txt += f", {f:%H:%M}"
            elif inf["origen_fecha"] == "archivo":
                txt += " (fecha del archivo)"
            partes.append(txt)
        if inf["camara"]:
            partes.append(f"📷 {inf['camara']}")
        self.l_info.configure(text="     ·     ".join(partes))

    def _pantalla_final(self):
        w, h = self._tam_lienzo()
        self._foto_tk = None
        self.l_info.configure(text="")
        if self.modo == "draft":
            titulo = "✅ Borrador revisado"
        else:
            titulo = "🎉 ¡Has revisado todas!"
        self.lienzo.create_text(w // 2, h // 2 - 50, text=titulo, fill=TEXTO, font=(F, 30, "bold"))
        sub = "Si te has equivocado en alguna, pulsa «Volver atrás» las veces que necesites."
        if self.saltadas:
            sub = f"Has saltado {N.num(self.saltadas)}. Siguen en «{'Borrador' if self.modo == 'draft' else 'Por revisar'}».\n" + sub
        self.lienzo.create_text(w // 2, h // 2 + 10, text=sub, fill=TEXTO2, font=(F, 13), justify="center")
        y = h // 2 + 80
        fr = tk.Frame(self.lienzo, bg="#0b0c0f")
        Boton(fr, "Inicio", PANEL2, self.pantalla_inicio, 12).pack(side="left", padx=6)
        if self.saltadas:
            Boton(fr, "Revisar las saltadas  →", ACENTO, lambda: self.pantalla_revision(self.modo), 12).pack(side="left", padx=6)
        elif self.modo == "pend" and self.bib.contar("draft"):
            Boton(fr, "Confirmar borradores  →", ROJO, lambda: self.pantalla_revision("draft"), 12).pack(side="left", padx=6)
        self.lienzo.create_window(w // 2, y, window=fr)

    def _dibujar_tira(self):
        t = self.tira
        if not t.winfo_exists():
            return
        t.delete("all")
        self._minis_tk = []
        tw = max(300, t.winfo_width())
        celda_w, celda_h = 150, 100
        n = max(1, (tw + 8) // (celda_w + 8))
        inicio = self.pos
        faltan = False
        tk_label = "Siguientes:" if self.pos < len(self.lista) else ""
        x = 0
        for i in range(n):
            idx = inicio + i
            if idx >= len(self.lista):
                break
            ruta = self.lista[idx]
            color_borde = ACENTO if i == 0 else BORDE
            t.create_rectangle(x, 2, x + celda_w, 2 + celda_h, outline=color_borde, width=3 if i == 0 else 1, fill=PANEL)
            if N.es_video(ruta):
                t.create_text(x + celda_w // 2, 2 + celda_h // 2, text="🎬", fill=TEXTO2, font=(F, 22))
            elif ruta in self.cargador.minis:
                im = self.cargador.minis[ruta]
                if im is not None:
                    ph = ImageTk.PhotoImage(im)
                    self._minis_tk.append(ph)
                    t.create_image(x + celda_w // 2, 2 + celda_h // 2, image=ph)
                else:
                    t.create_text(x + celda_w // 2, 2 + celda_h // 2, text="?", fill=GRIS, font=(F, 18))
            else:
                self.cargador.pedir_mini(ruta)
                faltan = True
            x += celda_w + 8
        del tk_label
        if faltan:
            self.after(250, self._dibujar_tira_si_sigue)

    def _dibujar_tira_si_sigue(self):
        if self.modo is not None:
            self._dibujar_tira()

    # --- acciones ------------------------------------------------------
    def accion(self, tipo):
        ruta = self._actual()
        if ruta is None:
            return
        try:
            if tipo == "eliminar":
                reg = self.bib.eliminar(ruta)
            elif tipo == "favorito":
                reg = self.bib.favorito(ruta)
            elif tipo == "mantener":
                reg = self.bib.mantener(ruta)
            elif tipo == "restaurar":
                reg = self.bib.restaurar(ruta)
            elif tipo == "borrar":
                reg = self.bib.eliminar_definitivo(ruta)
            elif tipo == "saltar":
                reg = self.bib.saltar(ruta)
                self.saltadas += 1
            else:
                return
        except Exception as e:
            messagebox.showerror("Foto Suprema", f"No se ha podido mover el archivo:\n{e}")
            return
        self.historial.append(reg)
        self.pos += 1
        self._destello(tipo)
        self.mostrar()

    def volver_atras(self):
        if not self.historial:
            return
        reg = self.historial.pop()
        try:
            ruta = self.bib.deshacer(reg)
        except Exception as e:
            messagebox.showerror("Foto Suprema", f"No se ha podido deshacer:\n{e}")
            return
        if reg["tipo"] == "saltar":
            self.saltadas = max(0, self.saltadas - 1)
        self.pos = max(0, self.pos - 1)
        if ruta:
            self.lista[self.pos] = ruta
        self.mostrar()

    def _destello(self, tipo):
        colores = {"eliminar": ROJO, "borrar": ROJO, "favorito": AMARILLO, "mantener": VERDE,
                   "restaurar": VERDE, "saltar": GRIS}
        self.lienzo.configure(bg=colores.get(tipo, "#0b0c0f"))
        self.after(90, lambda: self.lienzo.winfo_exists() and self.lienzo.configure(bg="#0b0c0f"))

    def borrar_todo(self):
        n = len(self.lista) - self.pos
        restantes = self.bib.contar("draft")
        if not restantes:
            return
        if not messagebox.askyesno("Borrar todo el borrador",
                                   f"Se van a borrar PARA SIEMPRE {N.num(restantes)} archivos del borrador.\n\n"
                                   "Esto no se puede deshacer. ¿Seguro?", icon="warning"):
            return
        del n
        self.bib.purgar()
        borradas, liberado = self.bib.borrar_todo_borrador()
        messagebox.showinfo("Foto Suprema", f"Borradas {N.num(borradas)} · liberados {N.tamano_legible(liberado)}")
        self.pantalla_inicio()

    def abrir_visor(self):
        r = self._actual()
        if r:
            abrir_en_sistema(r)

    # --- zoom ----------------------------------------------------------
    def _cargar_full(self):
        r = self._actual()
        if r is None or N.es_video(r):
            return False
        if self.full is None:
            try:
                self.config(cursor="watch")
                self.update_idletasks()
                self.full = abrir_preparada(r)
            except Exception:
                return False
            finally:
                self.config(cursor="")
            W, H = self.full.size
            self.centro = [W / 2, H / 2]
        return True

    def _escala(self):
        w, h = self._tam_lienzo()
        W, H = self.full.size
        ajuste = min(w / W, h / H, 1.0)
        return ajuste * self.zoom, ajuste

    def _limitar_centro(self, s):
        w, h = self._tam_lienzo()
        W, H = self.full.size
        vw, vh = w / s, h / s
        cx, cy = self.centro
        cx = W / 2 if vw >= W else min(max(cx, vw / 2), W - vw / 2)
        cy = H / 2 if vh >= H else min(max(cy, vh / 2), H - vh / 2)
        self.centro = [cx, cy]

    def _rueda(self, e, delta=None):
        if self._actual() is None:
            return
        d = delta if delta is not None else e.delta
        if not self._cargar_full():
            return
        s_old, ajuste = self._escala()
        factor = 1.25 if d > 0 else 1 / 1.25
        max_zoom = max(1.0, 4.0 / ajuste)  # hasta 400 % del tamaño real
        nuevo = min(max(self.zoom * factor, 1.0), max_zoom)
        if nuevo == self.zoom:
            return
        w, h = self._tam_lienzo()
        mx, my = e.x - w / 2, e.y - h / 2
        px, py = self.centro[0] + mx / s_old, self.centro[1] + my / s_old
        self.zoom = nuevo
        s_new, _ = self._escala()
        self.centro = [px - mx / s_new, py - my / s_new]
        if self.zoom <= 1.0001:
            self._reset_zoom(False)
            return
        self._render_zoom()

    def _arrastre_ini(self, e):
        self._arr = (e.x, e.y)

    def _arrastre(self, e):
        if self.zoom <= 1.0 or self.full is None:
            return
        s, _ = self._escala()
        dx, dy = e.x - self._arr[0], e.y - self._arr[1]
        self._arr = (e.x, e.y)
        self.centro[0] -= dx / s
        self.centro[1] -= dy / s
        self._render_zoom()

    def _render_zoom(self):
        s, ajuste = self._escala()
        self._limitar_centro(s)
        w, h = self._tam_lienzo()
        W, H = self.full.size
        vw, vh = min(W, w / s), min(H, h / s)
        cx, cy = self.centro
        caja = (int(max(0, cx - vw / 2)), int(max(0, cy - vh / 2)),
                int(min(W, cx + vw / 2)), int(min(H, cy + vh / 2)))
        trozo = self.full.crop(caja)
        tam = (max(1, int((caja[2] - caja[0]) * s)), max(1, int((caja[3] - caja[1]) * s)))
        trozo = trozo.resize(tam, Image.BILINEAR if s < 1 else Image.NEAREST if s >= 3 else Image.BICUBIC)
        self._foto_tk = ImageTk.PhotoImage(trozo)
        self.lienzo.delete("all")
        self.lienzo.create_image(w // 2, h // 2, image=self._foto_tk, anchor="center")
        self.l_zoom.configure(text=f"🔎 {s * 100:.0f} %  ·  arrastra para moverte · doble clic para ajustar")

    def _reset_zoom(self, redibujar=True):
        if self.zoom == 1.0 and not redibujar:
            return
        self.zoom = 1.0
        self.l_zoom.configure(text="")
        r = self._actual()
        if r is None:
            return
        w, h = self._tam_lienzo()
        im = self.cargador.previas.get((r, w, h))
        if im is not None:
            self._foto_tk = ImageTk.PhotoImage(im)
            self.lienzo.delete("all")
            self.lienzo.create_image(w // 2, h // 2, image=self._foto_tk, anchor="center")

    # ==================================================================
    # teclado
    # ==================================================================
    def on_tecla(self, e):
        if self.modo is None:
            return
        # evitar que mantener pulsada una flecha dispare 30 fotos seguidas
        ahora = time.time()
        k = e.keysym
        if k in ("Left", "Right", "Up", "Down") and ahora - self._ultimo_tecla < 0.12:
            return
        self._ultimo_tecla = ahora
        ctrl = bool(e.state & 0x4)
        if k == "BackSpace" or (ctrl and k.lower() == "z"):
            self.volver_atras()
        elif k == "Escape":
            if self.zoom > 1.0:
                self._reset_zoom(True)
            else:
                self.pantalla_inicio()
        elif k.lower() == "v":
            self.abrir_visor()
        elif k == "Down":
            self.accion("saltar")
        elif self.modo == "pend":
            if k in ("Left", "Delete"):
                self.accion("eliminar")
            elif k == "Up":
                self.accion("favorito")
            elif k == "Right":
                self.accion("mantener")
        elif self.modo == "draft":
            if k in ("Left", "Delete"):
                self.accion("borrar")
            elif k == "Right":
                self.accion("restaurar")


if __name__ == "__main__":
    App().mainloop()
