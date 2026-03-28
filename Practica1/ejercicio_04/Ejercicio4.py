import urllib.request
from collections import Counter
import re
import threading

libros = [
    ("https://www.gutenberg.org/cache/epub/1342/pg1342.txt", "Orgullo y Prejuicio"),
    ("https://www.gutenberg.org/cache/epub/84/pg84.txt", "Frankenstein"),
    ("https://www.gutenberg.org/cache/epub/11/pg11.txt", "Alicia en el pais de las maravillas")
]

def contar_palabras(url):
    respuesta = urllib.request.urlopen(url)
    texto = respuesta.read().decode('utf-8').lower()
    lista_palabras = re.findall(r'\b\w+\b', texto)
    return Counter(lista_palabras)

# Lista compartida para almacenar los Counters parciales
counters = []
lock = threading.Lock()

def worker(url):
    counter = contar_palabras(url)
    with lock:
        counters.append(counter)

# Crear y lanzar hilos
threads = []
for url, title in libros:
    t = threading.Thread(target=worker, args=(url,))
    threads.append(t)
    t.start()

# Esperar a que todos los hilos terminen
for t in threads:
    t.join()

# Fase de reducción: fusionar todos los Counters
final_counter = Counter()
for c in counters:
    final_counter.update(c)

# Mostrar el top 20 de palabras más frecuentes
print("Top 20 palabras más frecuentes:")
for palabra, frecuencia in final_counter.most_common(20):
    print(f"{palabra}: {frecuencia}")