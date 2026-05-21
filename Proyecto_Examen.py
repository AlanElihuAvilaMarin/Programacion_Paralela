import threading
import queue

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






