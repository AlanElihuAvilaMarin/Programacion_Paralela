from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import freeze_support
import os
import time

import rasterio
import numpy as np
from numba import njit, prange, set_num_threads


BASE_DIR = Path(__file__).resolve().parent

# Si tus carpetas Forest, Highway, Industrial, etc. están directamente en "Clase final"
CARPETA_ENTRADA = BASE_DIR

# Si después las metes dentro de input, usa:
# CARPETA_ENTRADA = BASE_DIR / "input"

CARPETA_SALIDA = BASE_DIR / "resultados_indices"

# Computadora: 4 núcleos físicos.
# Usamos 2 procesos y 2 hilos por proceso para no saturar.
MAX_WORKERS = 3
NUMBA_THREADS = 3


@njit(parallel=True)
def calcular_indices_pixel_por_pixel(blue, green, red, nir, swir1, swir2):
    alto, ancho = red.shape

    ndvi = np.empty((alto, ancho), dtype=np.float32)
    ndwi = np.empty((alto, ancho), dtype=np.float32)
    ndbi = np.empty((alto, ancho), dtype=np.float32)
    nbr = np.empty((alto, ancho), dtype=np.float32)

    for i in prange(alto):
        for j in range(ancho):
            # Convertimos de reflectancia escalada a reflectancia real
            b = blue[i, j] / 10000.0
            g = green[i, j] / 10000.0
            r = red[i, j] / 10000.0
            n = nir[i, j] / 10000.0
            s1 = swir1[i, j] / 10000.0
            s2 = swir2[i, j] / 10000.0

            # Clipping: recortar valores anómalos
            if b < 0.0:
                b = 0.0
            elif b > 1.0:
                b = 1.0

            if g < 0.0:
                g = 0.0
            elif g > 1.0:
                g = 1.0

            if r < 0.0:
                r = 0.0
            elif r > 1.0:
                r = 1.0

            if n < 0.0:
                n = 0.0
            elif n > 1.0:
                n = 1.0

            if s1 < 0.0:
                s1 = 0.0
            elif s1 > 1.0:
                s1 = 1.0

            if s2 < 0.0:
                s2 = 0.0
            elif s2 > 1.0:
                s2 = 1.0

            # NDVI = (NIR - Red) / (NIR + Red)
            denominador = n + r
            if denominador == 0.0:
                ndvi[i, j] = 0.0
            else:
                ndvi[i, j] = (n - r) / denominador

            # NDWI = (Green - NIR) / (Green + NIR)
            denominador = g + n
            if denominador == 0.0:
                ndwi[i, j] = 0.0
            else:
                ndwi[i, j] = (g - n) / denominador

            # NDBI = (SWIR1 - NIR) / (SWIR1 + NIR)
            denominador = s1 + n
            if denominador == 0.0:
                ndbi[i, j] = 0.0
            else:
                ndbi[i, j] = (s1 - n) / denominador

            # NBR = (NIR - SWIR2) / (NIR + SWIR2)
            denominador = n + s2
            if denominador == 0.0:
                nbr[i, j] = 0.0
            else:
                nbr[i, j] = (n - s2) / denominador

    return ndvi, ndwi, ndbi, nbr


def procesar_imagen(ruta_imagen):
    set_num_threads(NUMBA_THREADS)

    ruta_imagen = Path(ruta_imagen)

    with rasterio.open(ruta_imagen) as dataset:
        if dataset.count < 12:
            raise ValueError(
                f"{ruta_imagen.name} tiene {dataset.count} bandas. "
                "Se necesitan al menos 12 bandas."
            )

        # Bandas Sentinel-2:
        # Banda 2  = Azul
        # Banda 3  = Verde
        # Banda 4  = Rojo
        # Banda 8  = NIR
        # Banda 11 = SWIR 1
        # Banda 12 = SWIR 2

        blue = dataset.read(2).astype(np.float32)
        green = dataset.read(3).astype(np.float32)
        red = dataset.read(4).astype(np.float32)
        nir = dataset.read(8).astype(np.float32)
        swir1 = dataset.read(11).astype(np.float32)
        swir2 = dataset.read(12).astype(np.float32)

        perfil = dataset.profile.copy()

    ndvi, ndwi, ndbi, nbr = calcular_indices_pixel_por_pixel(
        blue, green, red, nir, swir1, swir2
    )

    ruta_relativa = ruta_imagen.relative_to(CARPETA_ENTRADA)
    ruta_salida = CARPETA_SALIDA / ruta_relativa.parent / f"{ruta_imagen.stem}_indices.tif"

    ruta_salida.parent.mkdir(parents=True, exist_ok=True)

    perfil.update(
        driver="GTiff",
        dtype="float32",
        count=4,
        compress="deflate",
        nodata=0.0
    )

    with rasterio.open(ruta_salida, "w", **perfil) as salida:
        salida.write(ndvi, 1)
        salida.write(ndwi, 2)
        salida.write(ndbi, 3)
        salida.write(nbr, 4)

        salida.set_band_description(1, "NDVI")
        salida.set_band_description(2, "NDWI")
        salida.set_band_description(3, "NDBI")
        salida.set_band_description(4, "NBR")

    return ruta_imagen.name, ruta_salida


def obtener_imagenes_tif():
    imagenes = []

    for extension in ("*.tif", "*.tiff"):
        for ruta in CARPETA_ENTRADA.rglob(extension):
            if CARPETA_SALIDA not in ruta.parents:
                imagenes.append(ruta)

    return imagenes


def main():
    inicio = time.perf_counter()

    imagenes = obtener_imagenes_tif()

    print("=" * 60)
    print("PROCESAMIENTO DE ÍNDICES ESPECTRALES")
    print("=" * 60)
    print(f"Carpeta de entrada: {CARPETA_ENTRADA}")
    print(f"Carpeta de salida:  {CARPETA_SALIDA}")
    print(f"Imágenes encontradas: {len(imagenes)}")
    print(f"Procesos usados: {MAX_WORKERS}")
    print(f"Hilos JIT por proceso: {NUMBA_THREADS}")
    print("=" * 60)

    if len(imagenes) == 0:
        print("No se encontraron imágenes .tif o .tiff.")
        return

    errores = 0

    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        tareas = [executor.submit(procesar_imagen, imagen) for imagen in imagenes]

        for i, tarea in enumerate(as_completed(tareas), start=1):
            try:
                nombre, salida = tarea.result()
                print(f"[{i}/{len(imagenes)}] OK: {nombre}")
            except Exception as error:
                errores += 1
                print(f"[{i}/{len(imagenes)}] ERROR: {error}")

    fin = time.perf_counter()

    print("=" * 60)
    print("PROCESAMIENTO TERMINADO")
    print(f"Tiempo total: {fin - inicio:.2f} segundos")
    print(f"Errores: {errores}")
    print(f"Resultados guardados en: {CARPETA_SALIDA}")
    print("=" * 60)


if __name__ == "__main__":
    freeze_support()
    main()