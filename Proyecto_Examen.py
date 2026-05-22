import threading
import queue
import time
import multiprocessing
import numpy as np
import threading
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

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

class FractalApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Proyecto Paralela: Mandelbrot Vectorizado")
        self.ancho = 800
        self.alto = 600
        self.x_min, self.x_max = -2.0, 0.5
        self.y_min, self.y_max = -1.25, 1.25
        self.max_iter = 150  
        self.num_cores = multiprocessing.cpu_count()
        
        self.canvas = tk.Canvas(root, width=self.ancho, height=self.alto, bg="black")
        self.canvas.pack(side=tk.TOP, expand=True, fill=tk.BOTH)
        self.status = ttk.Label(root, text="Iniciando motores optimizados...", font=("Arial", 11))
        self.status.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        
        self.canvas.bind("<Button-1>", self.hacer_zoom_in)   
        self.canvas.bind("<Button-3>", self.hacer_zoom_out)  
        
        self.hilo_logs = threading.Thread(target=consumidor_telemetria, daemon=True)
        self.hilo_logs.start()
        
        self.renderizar_fractal()

    def renderizar_fractal(self):
        self.status.config(text=f"Calculando matricialmente con {self.num_cores} núcleos...")
        self.root.update()
        
        clave_estado = (self.x_min, self.x_max, self.y_min, self.y_max, self.max_iter)
        
        if clave_estado in cache_fractales:
            print("[Memoización] Vista recuperada instantáneamente.")
            matriz_imagen = cache_fractales[clave_estado]
            tiempo_total = 0.0
        else:
            matriz_imagen, tiempo_total = self.despachar_calculo_paralelo(clave_estado)
            cache_fractales[clave_estado] = matriz_imagen

        img_pil = Image.fromarray(matriz_imagen, mode='L')
        self.img_tk = ImageTk.PhotoImage(img_pil.convert("RGB"))
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.img_tk)
        
        if tiempo_total > 0:
            self.status.config(text=f"Renderizado en {tiempo_total:.4f}s usando Vectorización NumPy + Pool ({self.num_cores} cores).")
        else:
            self.status.config(text="Cargado instantáneamente desde la Caché (Memoización).")
    @medir_rendimiento
    def despachar_calculo_paralelo(self, clave_estado):
        num_fragmentos = self.num_cores * 4  
        filas_por_fragmento = self.alto // num_fragmentos
        
        tareas = list(map(
            lambda i: (
                i * filas_por_fragmento, 
                (i + 1) * filas_por_fragmento if i != num_fragmentos - 1 else self.alto, 
                self.ancho, self.alto, self.x_min, self.x_max, self.y_min, self.y_max, self.max_iter
            ), 
            range(num_fragmentos)
        ))
        
        with multiprocessing.Pool(processes=self.num_cores) as pool:
            resultados = pool.map(calcular_bloque_mandelbrot_vectorizado, tareas)
            
        matriz_imagen = np.zeros((self.alto, self.ancho), dtype=np.uint8)
        for y_start, y_end, bloque in resultados:
            matriz_imagen[y_start:y_end, :] = bloque
            
        return matriz_imagen
    def aplicar_zoom(self, mouse_x, mouse_y, factor):
        click_real = self.x_min + (mouse_x / self.ancho) * (self.x_max - self.x_min)
        click_imag = self.y_min + (mouse_y / self.alto) * (self.y_max - self.y_min)
        
        nuevo_ancho_complejo = (self.x_max - self.x_min) * factor
        nuevo_alto_complejo = (self.y_max - self.y_min) * factor
        
        self.x_min = click_real - nuevo_ancho_complejo / 2
        self.x_max = click_real + nuevo_ancho_complejo / 2
        self.y_min = click_imag - nuevo_alto_complejo / 2
        self.y_max = click_imag + nuevo_alto_complejo / 2
        
        if factor < 1.0:
            self.max_iter = int(self.max_iter * 1.15) 
        else:
            self.max_iter = max(150, int(self.max_iter / 1.15))
            
        self.renderizar_fractal()

    def hacer_zoom_in(self, event):
        self.aplicar_zoom(event.x, event.y, 0.5)

    def hacer_zoom_out(self, event):
        self.aplicar_zoom(event.x, event.y, 2.0)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    root = tk.Tk()
    app = FractalApp(root)
    root.mainloop()



