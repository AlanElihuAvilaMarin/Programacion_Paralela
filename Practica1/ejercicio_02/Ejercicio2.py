import threading
import time

# Ejercicio 2: Alan Elihu Avila Marin

boletos_disponibles = 1000
candado = threading.Lock()

def vender_boletos(cantidad):
    global boletos_disponibles
    with candado:
        temp = boletos_disponibles
        time.sleep(0.0001)
        boletos_disponibles = temp - cantidad

hilos = []
for i in range(100):
    t = threading.Thread(target=vender_boletos, args=(1,))
    hilos.append(t)
    t.start()

for t in hilos:
    t.join()

print(f"Total de boletos en sistema: {boletos_disponibles}")
