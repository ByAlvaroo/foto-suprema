# 📸 Foto Suprema

Organizador de fotos para limpiar miles de fotos en minutos.

**HECHO POR @BYALVARO__**

## Qué hace

- **Subir una carpeta** (por ejemplo, la del pendrive): copia todas las fotos y vídeos de la carpeta **y de todas sus subcarpetas**. Ves una barra de progreso con «Subidas 3 de 5.000», el porcentaje, la velocidad y el tiempo que falta. Los originales no se tocan, y si vuelves a subir el mismo pendrive, las fotos que ya están se saltan.
- **Revisar fotos**, una a una y a pantalla completa:
  - `←` **Eliminar**: la foto va a la carpeta *Borrador*, todavía sin borrarse.
  - `↑` **Favorito**: la foto va a *Mantener* y además se copia a *Favoritos*.
  - `→` **Mantener**: la foto va a *Mantener*.
  - `↓` **Saltar**: la dejas para más tarde.
  - **↶ Volver atrás** (o `Retroceso`): deshace la última acción. Puedes pulsarlo todas las veces que quieras.
  - **Los vídeos se reproducen dentro de la app**, con sonido, barra para avanzar, pausa (`Espacio`) y volumen.
  - Zoom con la rueda del ratón (arrastra para moverte y haz doble clic para ajustar), tira de miniaturas con las siguientes fotos, fecha y cámara de cada foto, y `V` para abrir la foto o el vídeo en el visor de Windows.
- **Confirmar borradores**: repasas las fotos del *Borrador*. `←` las **borra para siempre** y `→` las **restaura** a *Mantener*. También hay un botón para borrar todo el borrador de una vez.
- **Organizar por años** o **por años y meses**: copia lo que hay en *Mantener* a carpetas `2007`, `2008`… (o `2009/03 - Marzo`). Solo se crean las carpetas de años y meses en los que hay al menos una foto. La fecha se toma de las propiedades de la foto (EXIF); si no la tiene, se usa la fecha que aparece en el nombre (`IMG_20190812`, fotos de WhatsApp…) y, si tampoco, la fecha del archivo. Las fotos se copian tal cual, con la misma resolución y calidad.
- **Estadísticas**: cuántas fotos has subido, mantenido, marcado como favoritas y borrado, y cuánto espacio has liberado.

Por defecto, la biblioteca se crea en `Imágenes\Foto Suprema`, con las carpetas *Por revisar*, *Mantener*, *Favoritos* y *Borrador*. Puedes cambiar la ubicación desde la pantalla de inicio.

Admite JPG, PNG, HEIC (iPhone), WEBP, GIF, BMP, TIFF y vídeos (MP4, MOV, AVI, MKV…).

## Instalación (solo la primera vez)

1. Ve a **Releases**, en la columna de la derecha del repositorio, y descarga `FotoSuprema.exe`.
2. Ábrelo. No hace falta instalar Python ni nada más, porque todo va dentro del .exe.
   - Si Windows muestra «Windows protegió su PC», pulsa **Más información → Ejecutar de todas formas**. Sale porque el .exe no está firmado.

## Actualizaciones automáticas

Cada vez que abres el .exe, comprueba `version.json` en este repositorio:

- Si la versión de GitHub es más nueva, descarga los archivos de `app/` y abre la app ya actualizada.
- Si no hay internet, abre la última versión que tenga.
- Si el código nuevo tiene un error de sintaxis, no lo instala y sigue usando el anterior.

**Para publicar una actualización:**
1. Cambia los archivos de `app/`.
2. Sube el número de versión en `version.json` (por ejemplo, `1.0.0` → `1.0.1`).
3. Haz commit y push. Al abrir el .exe en cualquier PC, se actualizará solo.

Solo hay que volver a compilar el .exe si cambias `lanzador/lanzador.py` o necesitas una librería nueva. En ese caso, sube `VERSION_LANZADOR` en `lanzador.py` y `lanzador_minimo` en `version.json`: GitHub compila el .exe nuevo y el .exe viejo se reemplaza solo.

La interfaz está hecha con Qt (PySide6), que trae el reproductor de vídeo integrado.

## Estructura

```
app/foto_suprema.py     interfaz (Qt) + autoprueba
app/nucleo.py           lógica (subir, mover, volver atrás, organizar, fechas)
version.json            versión actual (lo que mira el .exe para actualizarse)
lanzador/lanzador.py    el .exe: busca actualizaciones y abre la app
lanzador/icono.ico
.github/workflows/      compila el .exe automáticamente en GitHub
```

Para probar sin .exe (con Python instalado): `pip install pyside6 pillow pillow-heif` y después `python app/foto_suprema.py`.

Cada vez que haces push, GitHub prueba la app en Windows (`--autoprueba`) y guarda capturas de todas las pantallas en la pestaña **Actions → capturas-de-pantalla**. Solo se crea un .exe nuevo si cambias el lanzador o el mensaje del commit lleva `[exe]`.
