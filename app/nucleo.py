"""
Foto Suprema - núcleo: biblioteca, acciones con "volver atrás", subida,
organizador por años/meses, lectura de fecha/cámara y estadísticas.
HECHO POR @BYALVARO__
"""
import os
import re
import sys
import json
import time
import shutil
import threading
from datetime import datetime

try:
    from PIL import Image
    try:
        from pillow_heif import register_heif_opener  # fotos .HEIC de iPhone
        register_heif_opener()
    except Exception:
        pass
except Exception:  # pragma: no cover
    Image = None

EXT_FOTO = {
    ".jpg", ".jpeg", ".jpe", ".jfif", ".png", ".gif", ".bmp", ".webp",
    ".tif", ".tiff", ".heic", ".heif",
}
EXT_VIDEO = {".mp4", ".mov", ".avi", ".mkv", ".m4v", ".3gp", ".wmv", ".mts", ".m2ts", ".webm", ".mpg", ".mpeg"}
EXTENSIONES = EXT_FOTO | EXT_VIDEO

CARPETAS = {
    "pend": "Por revisar",
    "keep": "Mantener",
    "fav": "Favoritos",
    "draft": "Borrador",
}
CARPETA_POR_BORRAR = ".por_borrar"  # borrados definitivos que aún se pueden deshacer

MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio",
         "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

IGNORAR_CARPETAS = {"system volume information", "$recycle.bin", "recycler",
                    ".trashes", ".spotlight-v100", ".fseventsd", CARPETA_POR_BORRAR}


# ----------------------------------------------------------------------
# utilidades
# ----------------------------------------------------------------------
def carpeta_app():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def carpeta_datos():
    """Carpeta de datos del usuario (%LOCALAPPDATA%\\FotoSuprema en Windows)."""
    base = os.environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), ".local", "share")
    r = os.path.join(base, "FotoSuprema")
    os.makedirs(r, exist_ok=True)
    return r


def biblioteca_por_defecto():
    """Imágenes\\Foto Suprema"""
    return os.path.join(os.path.expanduser("~"), "Pictures", "Foto Suprema")


RUTA_CONFIG = os.path.join(carpeta_datos(), "config.json")


def cargar_json(ruta):
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def guardar_json(ruta, datos):
    try:
        tmp = ruta + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
        os.replace(tmp, ruta)
    except Exception:
        pass


def cargar_config():
    return cargar_json(RUTA_CONFIG)


def guardar_config(cfg):
    guardar_json(RUTA_CONFIG, cfg)


def extension(nombre):
    return os.path.splitext(nombre)[1].lower()


def es_valido(nombre):
    return extension(nombre) in EXTENSIONES


def es_video(nombre):
    return extension(nombre) in EXT_VIDEO


def num(n):
    return f"{n:,}".replace(",", ".")


def tamano_legible(b):
    b = float(b)
    for unidad in ("B", "KB", "MB", "GB", "TB"):
        if b < 1024 or unidad == "TB":
            return (f"{b:.0f} {unidad}" if unidad == "B" else f"{b:.1f} {unidad}").replace(".", ",")
        b /= 1024


def tiempo_legible(seg):
    if seg is None:
        return "calculando…"
    seg = int(round(seg))
    if seg < 60:
        return f"{seg} s"
    m, s = divmod(seg, 60)
    if m < 60:
        return f"{m} min {s:02d} s"
    h, m = divmod(m, 60)
    return f"{h} h {m:02d} min"


def ruta_libre(carpeta, nombre):
    destino = os.path.join(carpeta, nombre)
    if not os.path.exists(destino):
        return destino
    base, ext = os.path.splitext(nombre)
    i = 1
    while True:
        destino = os.path.join(carpeta, f"{base}_{i}{ext}")
        if not os.path.exists(destino):
            return destino
        i += 1


def ocultar_en_windows(ruta):
    if os.name == "nt":
        try:
            import ctypes
            ctypes.windll.kernel32.SetFileAttributesW(ruta, 0x02)
        except Exception:
            pass


# ----------------------------------------------------------------------
# fecha y cámara
# ----------------------------------------------------------------------
_RE_FECHA_NOMBRE = re.compile(r"(?<!\d)((?:19|20)\d{2})[-_.]?(0[1-9]|1[0-2])[-_.]?(0[1-9]|[12]\d|3[01])(?!\d)")
ANIO_MIN = 1980


def _fecha_valida(d):
    return d is not None and ANIO_MIN <= d.year <= datetime.now().year + 1


def _parsear_exif_fecha(valor):
    if not valor:
        return None
    if isinstance(valor, bytes):
        valor = valor.decode("ascii", "ignore")
    valor = str(valor).strip().replace("\x00", "")
    for fmt in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y:%m:%d", "%Y-%m-%d"):
        try:
            d = datetime.strptime(valor[:len(datetime.now().strftime(fmt))], fmt)
            return d if _fecha_valida(d) else None
        except Exception:
            continue
    return None


def leer_exif(ruta):
    """Devuelve (fecha_exif o None, cámara o '') leyendo las propiedades de la foto."""
    if Image is None or es_video(ruta):
        return None, ""
    try:
        with Image.open(ruta) as im:
            exif = im.getexif()
            if not exif:
                return None, ""
            sub = {}
            try:
                sub = exif.get_ifd(0x8769)  # Exif IFD
            except Exception:
                pass
            fecha = (_parsear_exif_fecha(sub.get(36867))      # DateTimeOriginal
                     or _parsear_exif_fecha(sub.get(36868))   # DateTimeDigitized
                     or _parsear_exif_fecha(exif.get(306)))   # DateTime
            marca = str(exif.get(271, "") or "").strip().strip("\x00")
            modelo = str(exif.get(272, "") or "").strip().strip("\x00")
            if marca and modelo.lower().startswith(marca.lower().split()[0]):
                camara = modelo
            else:
                camara = f"{marca} {modelo}".strip()
            return fecha, camara
    except Exception:
        return None, ""


def fecha_por_nombre(ruta):
    m = _RE_FECHA_NOMBRE.search(os.path.basename(ruta))
    if not m:
        return None
    try:
        d = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        return d if _fecha_valida(d) else None
    except ValueError:
        return None


def fecha_de(ruta):
    """
    Fecha de la foto/vídeo y de dónde sale:
      1) propiedades (EXIF) de la foto
      2) fecha escrita en el nombre (IMG_20190812, IMG-20190812-WA0001, Screenshot_2019-08-12…)
      3) fecha de modificación del archivo
    Devuelve (datetime o None, 'exif'|'nombre'|'archivo'|None)
    """
    f, _ = leer_exif(ruta)
    if f:
        return f, "exif"
    f = fecha_por_nombre(ruta)
    if f:
        return f, "nombre"
    try:
        f = datetime.fromtimestamp(os.path.getmtime(ruta))
        if _fecha_valida(f):
            return f, "archivo"
    except Exception:
        pass
    return None, None


def info_archivo(ruta):
    """Datos para mostrar debajo de la foto."""
    info = {"ruta": ruta, "nombre": os.path.basename(ruta), "video": es_video(ruta),
            "ancho": None, "alto": None, "bytes": 0, "fecha": None, "origen_fecha": None, "camara": ""}
    try:
        info["bytes"] = os.path.getsize(ruta)
    except OSError:
        pass
    if not info["video"] and Image is not None:
        try:
            with Image.open(ruta) as im:
                w, h = im.size
                try:
                    orient = im.getexif().get(274, 1)
                except Exception:
                    orient = 1
                if orient in (5, 6, 7, 8):
                    w, h = h, w
                info["ancho"], info["alto"] = w, h
        except Exception:
            pass
    fecha_exif, camara = leer_exif(ruta)
    info["camara"] = camara
    if fecha_exif:
        info["fecha"], info["origen_fecha"] = fecha_exif, "exif"
    else:
        info["fecha"], info["origen_fecha"] = fecha_de(ruta)
    return info


# ----------------------------------------------------------------------
# biblioteca
# ----------------------------------------------------------------------
STATS_VACIAS = {"subidas": 0, "eliminadas": 0, "favoritas": 0, "mantenidas": 0,
                "restauradas": 0, "borradas_def": 0, "bytes_liberados": 0, "organizadas": 0}


class Biblioteca:
    def __init__(self, raiz):
        self.raiz = raiz
        for k in CARPETAS:
            os.makedirs(self.ruta(k), exist_ok=True)
        self.ruta_stats = os.path.join(raiz, "foto_suprema_estadisticas.json")
        self.stats = dict(STATS_VACIAS)
        self.stats.update({k: v for k, v in cargar_json(self.ruta_stats).items() if k in STATS_VACIAS})
        self._lock = threading.Lock()

    def ruta(self, clave):
        return os.path.join(self.raiz, CARPETAS[clave])

    def ruta_por_borrar(self):
        r = os.path.join(self.raiz, CARPETA_POR_BORRAR)
        if not os.path.isdir(r):
            os.makedirs(r, exist_ok=True)
            ocultar_en_windows(r)
        return r

    def listar(self, clave):
        carpeta = self.ruta(clave)
        try:
            with os.scandir(carpeta) as it:
                nombres = [e.name for e in it if e.is_file() and es_valido(e.name)]
        except FileNotFoundError:
            return []
        nombres.sort(key=lambda n: n.lower())
        return [os.path.join(carpeta, n) for n in nombres]

    def contar(self, clave):
        return len(self.listar(clave))

    def tamano_carpeta(self, clave):
        total = 0
        for r in self.listar(clave):
            try:
                total += os.path.getsize(r)
            except OSError:
                pass
        return total

    # --- estadísticas ---------------------------------------------------
    def sumar(self, deltas, signo=1):
        with self._lock:
            for k, v in deltas.items():
                self.stats[k] = max(0, self.stats.get(k, 0) + signo * v)
            guardar_json(self.ruta_stats, self.stats)

    # --- operaciones básicas -------------------------------------------
    def _mover_a(self, src, carpeta):
        dst = ruta_libre(carpeta, os.path.basename(src))
        shutil.move(src, dst)
        return dst

    def _mover(self, src, clave):
        return self._mover_a(src, self.ruta(clave))

    def _copiar(self, src, clave):
        dst = ruta_libre(self.ruta(clave), os.path.basename(src))
        shutil.copy2(src, dst)
        return dst

    def _registro(self, tipo, ops, stats):
        self.sumar(stats)
        return {"tipo": tipo, "ops": ops, "stats": stats}

    # --- acciones (todas devuelven un registro para "volver atrás") -----
    def eliminar(self, src):
        dst = self._mover(src, "draft")
        return self._registro("eliminar", [("mover", dst, src)], {"eliminadas": 1})

    def mantener(self, src):
        dst = self._mover(src, "keep")
        return self._registro("mantener", [("mover", dst, src)], {"mantenidas": 1})

    def favorito(self, src):
        dst = self._mover(src, "keep")
        copia = self._copiar(dst, "fav")
        return self._registro("favorito", [("borrar", copia, None), ("mover", dst, src)], {"favoritas": 1})

    def restaurar(self, src):
        dst = self._mover(src, "keep")
        return self._registro("restaurar", [("mover", dst, src)], {"restauradas": 1, "eliminadas": -1})

    def eliminar_definitivo(self, src):
        """Se aparta a una carpeta oculta y se borra de verdad al salir de la pantalla,
        así 'Volver atrás' también funciona aquí."""
        tam = os.path.getsize(src) if os.path.exists(src) else 0
        dst = self._mover_a(src, self.ruta_por_borrar())
        return self._registro("borrar", [("mover", dst, src)], {"borradas_def": 1, "bytes_liberados": tam})

    def saltar(self, src):
        return {"tipo": "saltar", "ops": [], "stats": {}, "ruta": src}

    def deshacer(self, registro):
        """Revierte una acción. Devuelve la ruta donde vuelve a estar la foto."""
        restaurada = registro.get("ruta")
        for op, a, b in registro["ops"]:
            if op == "borrar":
                if os.path.exists(a):
                    os.remove(a)
            elif op == "mover":
                destino = b if not os.path.exists(b) else ruta_libre(os.path.dirname(b), os.path.basename(b))
                shutil.move(a, destino)
                restaurada = destino
        if registro.get("stats"):
            self.sumar(registro["stats"], signo=-1)
        return restaurada

    def purgar(self):
        """Borra de verdad lo apartado con 'Borrar para siempre'."""
        r = os.path.join(self.raiz, CARPETA_POR_BORRAR)
        if not os.path.isdir(r):
            return 0
        n = 0
        for nombre in os.listdir(r):
            p = os.path.join(r, nombre)
            try:
                if os.path.isfile(p):
                    os.remove(p)
                    n += 1
            except OSError:
                pass
        return n

    def borrar_todo_borrador(self):
        n, liberado = 0, 0
        for p in self.listar("draft"):
            try:
                t = os.path.getsize(p)
                os.remove(p)
                n += 1
                liberado += t
            except OSError:
                pass
        self.sumar({"borradas_def": n, "bytes_liberados": liberado})
        return n, liberado

    def indice_existentes(self):
        vistos = set()
        for k in CARPETAS:
            try:
                with os.scandir(self.ruta(k)) as it:
                    for e in it:
                        if e.is_file():
                            try:
                                vistos.add((e.name.lower(), e.stat().st_size))
                            except OSError:
                                pass
            except FileNotFoundError:
                pass
        return vistos


# ----------------------------------------------------------------------
# tareas largas con barra de progreso (subir / organizar)
# ----------------------------------------------------------------------
class TareaCopia:
    verbo = "Copiadas"

    def __init__(self):
        self.fase = "escaneando"   # escaneando -> copiando -> fin
        self.total = 0
        self.hechos = 0
        self.copiadas = 0
        self.repetidas = 0
        self.errores = 0
        self.bytes_total = 0
        self.bytes_hechos = 0
        self.encontradas_escaneo = 0
        self.inicio_copia = None
        self.fin = None
        self.cancelado = False
        self.error_fatal = None
        self._hilo = threading.Thread(target=self._run_seguro, daemon=True)

    def iniciar(self):
        self._hilo.start()

    def cancelar(self):
        self.cancelado = True

    def _run_seguro(self):
        try:
            self._run()
        except Exception as e:
            self.error_fatal = str(e)
        finally:
            self.fin = time.time()
            self.fase = "fin"

    def _run(self):
        raise NotImplementedError

    def porcentaje(self):
        if self.total == 0:
            return 100.0 if self.fase == "fin" else 0.0
        return self.hechos * 100.0 / self.total

    def transcurrido(self):
        if not self.inicio_copia:
            return 0.0
        return (self.fin or time.time()) - self.inicio_copia

    def eta(self):
        t = self.transcurrido()
        if t < 1.0 or self.bytes_hechos == 0:
            return None
        return max(0.0, (self.bytes_total - self.bytes_hechos) / (self.bytes_hechos / t))

    def por_segundo(self):
        t = self.transcurrido()
        return self.hechos / t if t > 0 else 0.0

    def mb_por_segundo(self):
        t = self.transcurrido()
        return self.bytes_hechos / t / (1024 * 1024) if t > 0 else 0.0


class Importador(TareaCopia):
    """Copia (nunca mueve) todo lo de la carpeta elegida y TODAS sus subcarpetas a 'Por revisar'."""
    verbo = "Subidas"

    def __init__(self, biblioteca, fuentes, saltar_repetidas=True):
        super().__init__()
        self.bib = biblioteca
        self.fuentes = list(fuentes)
        self.saltar_repetidas = saltar_repetidas

    def _escanear(self):
        archivos = []
        raiz_bib = os.path.normcase(os.path.abspath(self.bib.raiz))
        for f in self.fuentes:
            if self.cancelado:
                break
            if os.path.isfile(f):
                if es_valido(f):
                    archivos.append(f)
                    self.encontradas_escaneo += 1
                continue
            for carpeta, subcarpetas, nombres in os.walk(f, onerror=lambda e: None):
                if self.cancelado:
                    break
                if os.path.normcase(os.path.abspath(carpeta)).startswith(raiz_bib):
                    subcarpetas[:] = []
                    continue
                subcarpetas[:] = [s for s in subcarpetas
                                  if not s.startswith(".") and s.lower() not in IGNORAR_CARPETAS]
                for n in nombres:
                    if es_valido(n) and not n.startswith("._"):
                        archivos.append(os.path.join(carpeta, n))
                        self.encontradas_escaneo += 1
        lista = []
        for a in archivos:
            try:
                lista.append((a, os.path.getsize(a)))
            except OSError:
                pass
        return lista

    def _run(self):
        lista = self._escanear()
        self.total = len(lista)
        self.bytes_total = sum(t for _, t in lista) or 1
        vistos = self.bib.indice_existentes() if self.saltar_repetidas else set()
        destino = self.bib.ruta("pend")
        self.fase = "copiando"
        self.inicio_copia = time.time()
        for ruta, tam in lista:
            if self.cancelado:
                break
            clave = (os.path.basename(ruta).lower(), tam)
            if self.saltar_repetidas and clave in vistos:
                self.repetidas += 1
            else:
                try:
                    dst = ruta_libre(destino, os.path.basename(ruta))
                    shutil.copy2(ruta, dst)   # copia exacta: misma resolución y calidad
                    vistos.add(clave)
                    vistos.add((os.path.basename(dst).lower(), tam))
                    self.copiadas += 1
                except Exception:
                    self.errores += 1
            self.bytes_hechos += tam
            self.hechos += 1
        if self.copiadas:
            self.bib.sumar({"subidas": self.copiadas})


class Organizador(TareaCopia):
    """Copia las fotos de 'Mantener' a destino/AAAA  o  destino/AAAA/MM - Mes.
    Solo se crean las carpetas de años/meses que tengan al menos una foto."""
    verbo = "Organizadas"

    def __init__(self, biblioteca, destino, por_meses):
        super().__init__()
        self.bib = biblioteca
        self.por_meses = por_meses
        nombre = "Fotos por años y meses" if por_meses else "Fotos por años"
        self.destino = os.path.join(destino, nombre)
        self.carpetas_creadas = {}    # "2019" -> nº fotos  /  "2019/03 - Marzo" -> nº
        self.origenes = {"exif": 0, "nombre": 0, "archivo": 0, None: 0}

    def subcarpeta(self, fecha):
        if fecha is None:
            return "Sin fecha"
        if self.por_meses:
            return os.path.join(str(fecha.year), f"{fecha.month:02d} - {MESES[fecha.month - 1]}")
        return str(fecha.year)

    def _run(self):
        lista = []
        for r in self.bib.listar("keep"):
            try:
                lista.append((r, os.path.getsize(r)))
            except OSError:
                pass
            self.encontradas_escaneo += 1
        self.total = len(lista)
        self.bytes_total = sum(t for _, t in lista) or 1
        self.fase = "copiando"
        self.inicio_copia = time.time()
        for ruta, tam in lista:
            if self.cancelado:
                break
            try:
                fecha, origen = fecha_de(ruta)
                self.origenes[origen] = self.origenes.get(origen, 0) + 1
                sub = self.subcarpeta(fecha)
                carpeta = os.path.join(self.destino, sub)
                os.makedirs(carpeta, exist_ok=True)   # solo se crea si hay al menos una foto
                nombre = os.path.basename(ruta)
                existente = os.path.join(carpeta, nombre)
                if os.path.exists(existente) and os.path.getsize(existente) == tam:
                    self.repetidas += 1              # ya estaba organizada de antes
                else:
                    shutil.copy2(ruta, ruta_libre(carpeta, nombre))
                    self.copiadas += 1
                clave = sub.replace(os.sep, "/")
                self.carpetas_creadas[clave] = self.carpetas_creadas.get(clave, 0) + 1
            except Exception:
                self.errores += 1
            self.bytes_hechos += tam
            self.hechos += 1
        if self.copiadas:
            self.bib.sumar({"organizadas": self.copiadas})
