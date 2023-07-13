import pydicom as dicom
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
import os
import pathlib
import pickle
from tqdm.auto import tqdm
from datetime import datetime
#import img2pdf
import time

start = time.time()

#listar archivos en directorio
carpeta = pathlib.Path(r"C:\Users\mferreyra\Desktop\Kpacks Quilmes")
#carpeta = pathlib.Path(r"C:\Users\usuario\Documents\kpacks 28.06-30.06")
listado_nuevo = set(carpeta.rglob("*.dcm"))

#cargar archivos ya procesados y hacer diff
if os.path.exists("dcm2pdf_lista_procesados"):
    with open ("dcm2pdf_lista_procesados", 'rb') as leer:
        listado_procesados = pickle.load(leer)
else:
    listado_procesados = set()
listado = listado_nuevo - listado_procesados

#leer archivos dicom
for item in tqdm(listado, desc="Procesando imagenes", colour="green"):
    try:
        im = dicom.dcmread(str(item))
        im_np_array = im.pixel_array
    except Exception as e:
        with open("dcm2pdf_errores.txt", "a+") as log:
            log.write(f"*|{datetime.now().strftime('%D %H:%M:%S')}| Archivo: {str(item)}\n    Error -> {repr(e)}\n")
        continue

    #generar imagen
    plt.figure(figsize=(8.27, 11.69), dpi=100) #para generar en tamaño de A4, con resolucion aceptable
    plt.imshow(im_np_array, cmap='gray_r', interpolation='nearest')
    plt.axis(False)
    #guardar imagen a png (para buscar tamaño correcto en pdf)
    plt.savefig("dcm2pdf_temp.png", format='png', orientation='portrait', bbox_inches='tight')
    plt.close() #RuntimeWarning: Figures created through the pyplot interface are retained until explicitly closed and may consume too much memory.
    #abrir para sobreescribir texto y guardar en pdf en tamaño correcto para A4 con PIL
    imagen = Image.open("dcm2pdf_temp.png")
    draw = ImageDraw.Draw(imagen)
    try:
        font = ImageFont.truetype(r'C:\Users\System-Pc\Desktop\arial.ttf', 8) #Fuente? TODO
    except:
        font=None
    
    width, height = imagen.size
    
    sup_izq = (15, 15)
    sup_der = (width-200, 15)
    inf_izq = (15, height-75)
    inf_der = (width-150, height-75)
    
    text_sup_izq = f"{im.PatientName}\n{im.PatientSex}\n{im.PatientID}"
    text_sup_der = f"{im.InstitutionName}\n Ref: {im.ReferringPhysicianName} / Perf: ''\nStudy date: {im.StudyDate}\nStudy time: {im.StudyTime}"
    text_inf_izq = f"W{im.WindowWidth} / C {im.WindowCenter}\n' '\nS-Value: {im.Sensitivity}"
    text_inf_der = f"{im.BodyPartExamined }\n'Position: {im.ViewPosition}'\n{im.InstanceNumber} IMA {im.SeriesNumber}\nZoom factor: x''"
    
    draw.text(sup_izq, text_sup_izq, font=font)    
    draw.text(sup_der, text_sup_der, font=font) 
    draw.text(inf_izq, text_inf_izq, font=font) 
    draw.text(inf_der, text_inf_der, font=font) 

    #imagen.show()
    imagen.save(fp="fin2.pdf", format="pdf")

    #nueva img2pdf
    # a4inpt = (img2pdf.mm_to_pt(210), img2pdf.mm_to_pt(297))
    # layout_fun = img2pdf.get_layout_fun(a4inpt)
    # with open("name.pdf", "wb") as f:
    #     f.write(img2pdf.convert("dcm2pdf_temp.png", layout_fun=layout_fun))

    #borrar archivo png temporal
    if os.path.exists("dcm2pdf_temp.png"):
        os.remove("dcm2pdf_temp.png")

#guardar listado de archivos procesados, agregando a previos
with open("dcm2pdf_lista_procesados", 'wb') as archivo:
    pickle.dump(listado_nuevo, archivo, protocol=pickle.HIGHEST_PROTOCOL)

end = time.time()
print(str(end-start))

#TODO
#Agregar directorio a procesar y guardar por consola? preguntando? argpars?
#leer propiedades a guardar sobre imagen y escribir en cada esquina
#CSV para presentar archivos procesados? probar reemplazar Pickle por SQLite?
#generar archivo ejecutable