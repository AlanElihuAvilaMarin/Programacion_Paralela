import threading
import requests
import queue
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, text

cola_precios = queue.Queue()

# --- FASE 1: SOLO SCRAPING ---
def solo_scraping(cola_symbols):
    headers = {"User-Agent": "Mozilla/5.0"}
    while not cola_symbols.empty():
        try:
            symbol = cola_symbols.get_nowait()
            url = f"https://finance.yahoo.com/quote/{symbol}"
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                valor = soup.find("span", {"data-testid": "qsp-price"})
                if valor:
                    precio = float(valor.text.replace(",", ""))
                    cola_precios.put((symbol, precio)) # Guardamos en memoria
                    print(f"[Scraped] {symbol} listo")
            cola_symbols.task_done()
        except: break

# --- FASE 2: SOLO INSERCIÓN ---
def solo_insercion():
    engine = create_engine("postgresql+psycopg2://postgres:supersecret@localhost:5432/postgres")
    while True:
        try:
            # Timeout para que el hilo muera si no hay más datos
            symbol, precio = cola_precios.get(timeout=5)
            with engine.begin() as conn:
                conn.execute(
                    text("INSERT INTO inversiones (symbol, price) VALUES (:s, :p)"),
                    {"s": symbol, "p": precio}
                )
            print(f"[DB] {symbol} guardado")
            cola_precios.task_done()
        except queue.Empty:
            break