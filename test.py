import pydicom as dycom
import matplotlib.pyplot as plt
from PIL import Image
import os
#import time

#start = time.time()
#leer dicom
im = dycom.dcmread("./prueba2.dcm")
im_np_array = im.pixel_array
#generar imagen
plt.figure(figsize=(8.27, 11.69), dpi=100)
plt.imshow(im_np_array, cmap='gray_r', interpolation='nearest')
plt.axis(False)
#guardar imagen a png (para buscar tamaño correcto en pdf)
plt.savefig("temp.png", format='png', orientation='portrait', bbox_inches='tight')
#abrir y guardar en pdf en tamaño correcto con PIL
imagen = Image.open("temp.png")
imagen.save(fp="fin.pdf", format="pdf")
#borrar archivo png temporal
if os.path.exists("temp.png"):
    os.remove("temp.png")

#end = time.time()
#print(str(end-start))

#TODO
#listar archivos dentro de carpetas/pacientes
#leer propiedades a guardar sobre imagen
#sobreescribir texto con datos en imagen png