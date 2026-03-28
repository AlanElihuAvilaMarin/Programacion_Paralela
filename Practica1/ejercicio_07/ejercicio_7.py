import requests
import threading
import os
import time

URL_ARCHIVO = "https://www.python.org/ftp/python/3.11.5/python-3.11.5.exe"
NUM_HILOS = 4
NOMBRE_SALIDA = "python_descargado.exe"

def obtener_tamano(url):
        respuesta = requests.head(url)
        return int(respuesta.headers.get('content-length', 0))

def descargar_fragmento(url, inicio, fin, id_fragmento):
    headers = {'Range': f'bytes={inicio}-{fin}'}
    
    try:
        respuesta = requests.get(url, headers=headers, stream=True)
        
        nombre_parte = f"parte_{id_fragmento}.tmp"
        
        with open(nombre_parte, 'wb') as f:
            for chunk in respuesta.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        
        print(f"Fragmento {id_fragmento} descargado ({inicio}-{fin})")
    
    except Exception as e:
        print(f"Error en fragmento {id_fragmento}:", e)

def unir_fragmentos(num_hilos, nombre_salida):
    with open(nombre_salida, 'wb') as salida:
        for i in range(num_hilos):
            nombre_parte = f"parte_{i}.tmp"
            with open(nombre_parte, 'rb') as f:
                salida.write(f.read())
    
    print(f"\nArchivo final ensamblado: {nombre_salida}")

def limpiar_temporales(num_hilos):
    for i in range(num_hilos):
        try:
            os.remove(f"parte_{i}.tmp")
        except:
            pass
    print("Archivos temporales eliminados")


if __name__ == "__main__":
    tiempo_inicial = time.time()
    
    tamano_total = obtener_tamano(URL_ARCHIVO)

    print(f"Tamaño total: {tamano_total} bytes")
    
    tamano_bloque = tamano_total // NUM_HILOS
    
    hilos = []
    
    for i in range(NUM_HILOS):
        inicio = i * tamano_bloque
        fin = (inicio + tamano_bloque - 1) if i < NUM_HILOS - 1 else tamano_total - 1
        
        hilo = threading.Thread(
            target=descargar_fragmento,
            args=(URL_ARCHIVO, inicio, fin, i)
        )
        
        hilos.append(hilo)
        hilo.start()
    
    for hilo in hilos:
        hilo.join()
    
    print("\nTodos los fragmentos descargados")
    
    unir_fragmentos(NUM_HILOS, NOMBRE_SALIDA)
    
    limpiar_temporales(NUM_HILOS)
    
    tiempo_final = time.time()
    
    print(f"\nTiempo total: {tiempo_final - tiempo_inicial} segundos")