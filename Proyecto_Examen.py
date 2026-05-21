import threading
import queue

cola_telemetria = queue.Queue()            
lock_estadisticas = threading.Lock()       
semaforo_io = threading.Semaphore(1)       

estadisticas_globales = {"renders_totales": 0}









