import requests
import queue 
import threading
import time
#Secuencial
def productor_secuencial():
    cola_chistes = []
    #Simulación: descarga secuancial de chistes
    endpoint = "https://api.chucknorris.io/jokes/random"
    for _ in range(5):
        r = requests.get(endpoint)
        cola_chistes.append(r.json()['value'])
    return cola_chistes

#print(productor_secuencial())

#Threads
MAX_ITEMS = 50
TIEMPO_LIMITE = 5

cola = queue.Queue(maxsize=20)
contador = 0

lock = threading.Lock()
stop_event = threading.Event()

#Productores
def productor(nproductor):
    global contador
    endpoint = "https://api.chucknorris.io/jokes/random"

    while not stop_event.is_set():
        try:
            r = requests.get(endpoint, timeout=3)
            chiste = r.json()['value']

            cola.put(chiste) 

            with lock:
                contador += 1
                if contador >= MAX_ITEMS:
                    stop_event.set()

            print(f"Productor {nproductor} produjo chiste")
        except Exception as e:
            print("Error: ",e)
        
#Consumidores
def consumidor(nconsumidor):
    with open(f"chistes_{nconsumidor}.txt", "w", encoding="utf-8") as f:
        while True:
            chiste = cola.get()
            
            if chiste is None:  # centinela
                break
            
            f.write(chiste + "\n\n")
            print(f"Consumidor {nconsumidor} guardó chiste")
            
            cola.task_done()

if __name__ == "__main__":
    hilos_productores = []
    hilos_consumidores = []

    inicio = time.time()

    # Crear consumidores
    for i in range(3):
        t = threading.Thread(target=consumidor, args=(i,))
        hilos_consumidores.append(t)
        t.start()

    # Crear productores
    for i in range(2):
        t = threading.Thread(target=productor, args=(i,))
        hilos_productores.append(t)
        t.start()

    # Control de tiempo
    while time.time() - inicio < TIEMPO_LIMITE:
        if stop_event.is_set():
            break
        time.sleep(0.1)    
    # Forzar parada si se cumplió tiempo
    stop_event.set()

    # Esperar productores
    for t in hilos_productores:
        t.join()

    # Enviar centinelas para cerrar consumidores
    for _ in hilos_consumidores:
        cola.put(None)

    # Esperar consumidores
    for t in hilos_consumidores:
        t.join()

    print("\nProceso terminado correctamente.")
    print(f"Total de chistes procesados: {contador}")