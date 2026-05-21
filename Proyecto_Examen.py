import threading
import queue
import time
import multiprocessing
import numpy as np

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



