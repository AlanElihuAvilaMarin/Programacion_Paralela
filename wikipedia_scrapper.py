import requests
from bs4 import BeautifulSoup
import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "contraseña",
    "database": "stocks_db"
}

URL = "https://es.wikipedia.org/wiki/Anexo:Compa%C3%B1%C3%ADas_del_S%26P_500"
HEADERS = {
    "User-Agent": "MiProyectoSP500/1.0"
}

def crear_tabla_si_no_existe():
    conexion = mysql.connector.connect(**DB_CONFIG)
    cursor = conexion.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS simbolos_sp500 (
            id INT AUTO_INCREMENT PRIMARY KEY,
            simbolo VARCHAR(10) NOT NULL UNIQUE
        )
    """)
    conexion.commit()
    cursor.close()
    conexion.close()

def obtener_simbolos():
    response = requests.get(URL, headers=HEADERS, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find(id="constituents")

    if table is None:
        raise ValueError("No se encontró la tabla de constituyentes en Wikipedia.")

    simbolos = []
    for row in table.find_all("tr")[1:]:
        cols = row.find_all("td")
        if cols:
            simbolo = cols[0].text.strip()
            simbolos.append(simbolo)

    return simbolos

def guardar_simbolos_en_mysql(simbolos):
    conexion = mysql.connector.connect(**DB_CONFIG)
    cursor = conexion.cursor()

    query = "INSERT IGNORE INTO simbolos_sp500 (simbolo) VALUES (%s)"
    for simbolo in simbolos:
        cursor.execute(query, (simbolo,))

    conexion.commit()
    print(f"Se guardaron {cursor.rowcount} símbolos nuevos en MySQL.")

    cursor.close()
    conexion.close()

if __name__ == "__main__":
    try:
        crear_tabla_si_no_existe()
        simbolos = obtener_simbolos()
        guardar_simbolos_en_mysql(simbolos)
        print("Proceso terminado correctamente.")
    except Exception as e:
        print(f"Error: {e}")