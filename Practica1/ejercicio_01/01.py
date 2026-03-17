import time
import requests
import threading

ciudades = [
    {"lat": 19.43 , "lon": -99.13} , # CDMX
    {"lat": 40.71 , "lon": -74.00} , # NY
    {"lat": 51.50 , "lon": -0.12} , # Londres
    {"lat": 35.68 , "lon": 139.69} # Tokio
]

def obtener_clima ( lat , lon ) :
    base_url = "https://api.open-meteo.com/v1/forecast"
    params = f"?latitude={lat}&longitude={lon}&current_weather=true"
    url = base_url + params
    respuesta = requests.get(url)
    if respuesta.status_code == 200:
        return respuesta.json()['current_weather']
    return None

if __name__ == "__main__" :
    inicio = time.time ()
    for ciudad in ciudades :
        obtener_clima(ciudad ['lat'] , ciudad ['lon'])
    print ( f"Tiempo secuencial : { time.time () - inicio } segundos ")

    inicio2 = time.time ()
    threads =[]
    for ciudad in ciudades:
        threads.append(
			threading.Thread(target=obtener_clima, args=(ciudad ['lat'] , ciudad ['lon']))
		)

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    print(f"Tiempo total threading: {time.time() - inicio2}")

#Conclusión: Vale la pena hacer threading para reducir los tiempos de consulta.
