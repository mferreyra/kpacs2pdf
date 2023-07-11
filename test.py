import pydicom as dycom
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
import os
import pathlib
import pickle
from tqdm.auto import tqdm
from datetime import datetime
import time

start = time.time()

#listar archivos en directorio
#carpeta = pathlib.Path(r"C:\Users\mferreyra\Desktop\Kpacks Quilmes")
carpeta = pathlib.Path(r"C:\Users\usuario\Documents\Trabajo\kpacks 28.06-30.06")
listado_nuevo = set(carpeta.rglob("*.dcm"))

#cargar archivos ya procesados y hacer diff
if os.path.exists("lista_procesados"):
    with open ("lista_procesados", 'rb') as leer:
        listado_procesados = pickle.load(leer)
else:
    listado_procesados = set()
listado = listado_nuevo - listado_procesados

#leer archivos dicom
for item in tqdm(listado, desc="Procesando imagenes", colour="green"):
    try:
        im = dycom.dcmread(str(item))
        im_np_array = im.pixel_array
    except Exception as e:
        with open("errores.txt", "a+") as log:
            log.write(f"|{datetime.now().strftime('%D %H:%M:%S')}| Archivo: {str(item)}\n    Error -> {repr(e)}\n")
        continue
    #generar imagen
    plt.figure(figsize=(8.27, 11.69), dpi=100)
    plt.imshow(im_np_array, cmap='gray_r', interpolation='nearest')
    plt.axis(False)
    #guardar imagen a png (para buscar tamaño correcto en pdf)
    plt.savefig("temp.png", format='png', orientation='portrait', bbox_inches='tight')
    plt.close() #RuntimeWarning: Figures created through the pyplot interface are retained until explicitly closed and may consume too much memory.
    #abrir para sobreescribir texto y guardar en pdf en tamaño correcto para A4 con PIL
    imagen = Image.open("temp.png")
    draw = ImageDraw.Draw(imagen)
    try:
        font = ImageFont.truetype(r'C:\Users\System-Pc\Desktop\arial.ttf', 20) #Fuente?
    except:
        font=None
    text = "Paciente Pirulo \n Vino ayer\n Lo vio el otro medico" #ler atributos a escribir
    #Abajo izq, etc en coordenadas ralativas a imagen.size -> (w,h)
    draw.text((220, 400), text, font=font)    
    #imagen.show()
    imagen.save(fp="fin.pdf", format="pdf")

    #borrar archivo png temporal
    if os.path.exists("temp.png"):
        os.remove("temp.png")

#guardar listado de archivos procesados, agregando a previos
with open("lista_procesados", 'wb') as archivo:
    pickle.dump(listado_nuevo, archivo, protocol=pickle.HIGHEST_PROTOCOL)

end = time.time()
print(str(end-start))

#TODO
#leer propiedades a guardar sobre imagen y escribir en cada esquina
#CSV para presentar archivos procesados? probar reemplazar Pickle por SQLite?
#generar archivo ejecutable