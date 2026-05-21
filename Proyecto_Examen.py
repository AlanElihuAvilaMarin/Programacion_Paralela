import threading
import queue
import time
import numpy as np

cola_telemetria = queue.Queue()            
lock_estadisticas = threading.Lock()       
semaforo_io = threading.Semaphore(1)       

estadisticas_globales = {"renders_totales": 0}


def consumidor_telemetria():
    while True:
        mensaje = cola_telemetria.get()
        if mensaje == "SALIR":
            break
        
        with semaforo_io:
            with lock_estadisticas:
                estadisticas_globales["renders_totales"] += 1
                total = estadisticas_globales["renders_totales"]
            print(f"[Log Hilo] Render #{total} -> {mensaje}")
        
        cola_telemetria.task_done()


def medir_rendimiento(func):
    def wrapper(*args, **kwargs):
        inicio = time.time()
        resultado = func(*args, **kwargs)
        tiempo_total = time.time() - inicio
        cola_telemetria.put(f"Tiempo de cómputo: {tiempo_total:.4f} segundos")
        return resultado, tiempo_total
    return wrapper



def calcular_bloque_mandelbrot_vectorizado(args):
    y_start, y_end, ancho, alto, x_min, x_max, y_min, y_max, max_iter = args
    
    x_coords = np.linspace(x_min, x_max, ancho)
    y_coords = np.linspace(y_min + (y_start / alto) * (y_max - y_min), 
                           y_min + (y_end / alto) * (y_max - y_min), 
                           y_end - y_start, endpoint=False)
    
    c = x_coords + 1j * y_coords[:, np.newaxis]
    
    z = np.zeros_like(c, dtype=complex)
    iteraciones = np.zeros(c.shape, dtype=int)
    vivos = np.ones(c.shape, dtype=bool)  
    
    for i in range(max_iter):
        if not vivos.any():
            break
        z[vivos] = z[vivos] ** 2 + c[vivos]
        
        escapados = (z.real * 2 + z.imag * 2 > 4.0) & vivos
        iteraciones[escapados] = i
        vivos[escapados] = False
    
    bloque_color = (iteraciones * 255 / max_iter).astype(np.uint8)
    return y_start, y_end, bloque_color





