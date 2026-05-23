from pathlib import Path
import rasterio
import matplotlib.pyplot as plt
from matplotlib.widgets import Button


BASE_DIR = Path(__file__).resolve().parent
CARPETA_RESULTADOS = BASE_DIR / "resultados_indices"


archivos = sorted(CARPETA_RESULTADOS.rglob("*_indices.tif"))

if len(archivos) == 0:
    print("No se encontraron archivos *_indices.tif")
    exit()


indice_actual = 0


def cargar_indices(ruta):
    with rasterio.open(ruta) as dataset:
        ndvi = dataset.read(1)
        ndwi = dataset.read(2)
        ndbi = dataset.read(3)
        nbr = dataset.read(4)

    return ndvi, ndwi, ndbi, nbr


def actualizar_figura():
    global indice_actual

    ruta = archivos[indice_actual]
    ndvi, ndwi, ndbi, nbr = cargar_indices(ruta)

    imagen_ndvi.set_data(ndvi)
    imagen_ndwi.set_data(ndwi)
    imagen_ndbi.set_data(ndbi)
    imagen_nbr.set_data(nbr)

    titulo = f"{indice_actual + 1}/{len(archivos)} - {ruta.relative_to(CARPETA_RESULTADOS)}"
    fig.suptitle(titulo, fontsize=14)

    fig.canvas.draw_idle()


def siguiente(event):
    global indice_actual

    if indice_actual < len(archivos) - 1:
        indice_actual += 1
    else:
        indice_actual = 0

    actualizar_figura()


def anterior(event):
    global indice_actual

    if indice_actual > 0:
        indice_actual -= 1
    else:
        indice_actual = len(archivos) - 1

    actualizar_figura()


def tecla_presionada(event):
    if event.key == "right":
        siguiente(event)
    elif event.key == "left":
        anterior(event)


ndvi, ndwi, ndbi, nbr = cargar_indices(archivos[indice_actual])

fig, axes = plt.subplots(2, 2, figsize=(12, 8))

plt.subplots_adjust(bottom=0.18)

imagen_ndvi = axes[0, 0].imshow(ndvi, cmap="RdYlGn", vmin=-1, vmax=1)
axes[0, 0].set_title("NDVI - Vegetación")
axes[0, 0].axis("off")
plt.colorbar(imagen_ndvi, ax=axes[0, 0])

imagen_ndwi = axes[0, 1].imshow(ndwi, cmap="Blues", vmin=-1, vmax=1)
axes[0, 1].set_title("NDWI - Humedad")
axes[0, 1].axis("off")
plt.colorbar(imagen_ndwi, ax=axes[0, 1])

imagen_ndbi = axes[1, 0].imshow(ndbi, cmap="gray", vmin=-1, vmax=1)
axes[1, 0].set_title("NDBI - Construcciones")
axes[1, 0].axis("off")
plt.colorbar(imagen_ndbi, ax=axes[1, 0])

imagen_nbr = axes[1, 1].imshow(nbr, cmap="hot", vmin=-1, vmax=1)
axes[1, 1].set_title("NBR - Riesgo de incendio")
axes[1, 1].axis("off")
plt.colorbar(imagen_nbr, ax=axes[1, 1])


ax_anterior = plt.axes([0.30, 0.05, 0.15, 0.06])
ax_siguiente = plt.axes([0.55, 0.05, 0.15, 0.06])

boton_anterior = Button(ax_anterior, "Anterior")
boton_siguiente = Button(ax_siguiente, "Siguiente")

boton_anterior.on_clicked(anterior)
boton_siguiente.on_clicked(siguiente)

fig.canvas.mpl_connect("key_press_event", tecla_presionada)

actualizar_figura()

plt.show()

