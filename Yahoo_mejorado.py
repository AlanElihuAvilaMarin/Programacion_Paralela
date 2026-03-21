import time
import random
import requests
import threading
from bs4 import BeautifulSoup
import queue
import mysql.connector

cola_procesos = queue.Queue()

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "contraseña",
    "database": "stocks_db"
}

def obtener_simbolos_desde_mysql():
    conexion = mysql.connector.connect(**DB_CONFIG)
    cursor = conexion.cursor()
    cursor.execute("SELECT simbolo FROM simbolos_sp500")
    simbolos = [fila[0] for fila in cursor.fetchall()]
    cursor.close()
    conexion.close()
    return simbolos

def consultar_precio(symbol):
    url = f"https://finance.yahoo.com/quote/{symbol}"
    headers = {
        "User-Agent": "MiProyecto/1.0"
    }

    precio = "Privado"
    intentos = 0

    while intentos < 3:
        try:
            time.sleep(2 * random.random())
            response = requests.get(url, headers=headers, timeout=20)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                valor = soup.find("span", {"data-testid": "qsp-price"})
                if valor:
                    precio = valor.text.strip()
                break
            else:
                intentos += 1
        except Exception:
            intentos += 1

    return precio

def worker():
    conexion = mysql.connector.connect(**DB_CONFIG)
    cursor = conexion.cursor()

    while True:
        try:
            symbol = cola_procesos.get_nowait()
        except queue.Empty:
            break

        try:
            precio = consultar_precio(symbol)
            print(f"La acción {symbol} cuesta: {precio}")

            query = "INSERT INTO precios (simbolo, precio) VALUES (%s, %s)"
            cursor.execute(query, (symbol, precio))
            conexion.commit()

            print(f"-> {symbol} guardado en MySQL con éxito.")
        except Exception as e:
            print(f"Error con {symbol}: {e}")
        finally:
            cola_procesos.task_done()

    cursor.close()
    conexion.close()

if __name__ == "__main__":
    lista_simbolos = obtener_simbolos_desde_mysql()

    for symbol in lista_simbolos:
        cola_procesos.put(symbol)

    threads = []
    for _ in range(8):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    print("Proceso finalizado. Revisa tu tabla 'precios' en MySQL Workbench.")