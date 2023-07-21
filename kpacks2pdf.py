import pydicom as dicom
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path
import pickle
from tqdm.auto import tqdm
from datetime import datetime
import img2pdf
import logging.config
#import time

def main():

    logging.config.dictConfig({'disable_existing_loggers': True, "version": 1}) #Apagar warning de img2pdf

    #start = time.time()

    #listar archivos en directorio
    #carpeta = Path(r"C:\Users\mferreyra\Desktop\Kpacks Quilmes")
    carpeta = Path(r"C:\Users\usuario\Documents\Trabajo\kpacks 28.06-30.06")
    #carpeta = Path(r"C:\Users\usuario\source\kpacks2pdf\DICOM test")
    listado_nuevo = set(carpeta.rglob("*.dcm"))

    #cargar archivos ya procesados y hacer diff
    if os.path.exists("dcm2pdf_lista_procesados"):
        with open ("dcm2pdf_lista_procesados", 'rb') as leer:
            listado_procesados = pickle.load(leer)
    else:
        listado_procesados = set()
    listado = listado_nuevo - listado_procesados

    #crear carpeta para guardar pdf si no existe (evit error en img2pdf with open())
    if not os.path.exists("./pdf/"):
        os.makedirs("./pdf/")

    #leer archivos dicom
    for item in tqdm(listado, desc="Procesando imagenes", colour="green", leave=True, position=0):
        try:
            im = dicom.dcmread(str(item))
            im_np_array = im.pixel_array
        except Exception as e:
            with open("dcm2pdf_errores.txt", "a+") as log:
                log.write(f"*|{datetime.now().strftime('%D %H:%M:%S')}| Archivo: {str(item)}\n    Error -> {repr(e)}\n")
            continue

        if (im.PatientID).startswith('1-'): #Saltear imagenes de MEVA para no procesarlas
            continue

        #generar imagen
        plt.figure(figsize=(8.27, 11.69), dpi=150) #para generar en tamaño de A4, con resolucion aceptable
        plt.imshow(im_np_array, cmap='gray_r', interpolation='nearest')
        plt.axis(False)
        #guardar imagen a png (para buscar tamaño correcto en pdf)
        plt.savefig("dcm2pdf_temp.temp", format='png', orientation='portrait', bbox_inches='tight')
        plt.close() #RuntimeWarning: Figures created through the pyplot interface are retained until explicitly closed and may consume too much memory.
        #abrir para sobreescribir texto y guardar en pdf en tamaño correcto para A4 con PIL
        imagen = Image.open("dcm2pdf_temp.temp")
        draw = ImageDraw.Draw(imagen)
        try:
            font = ImageFont.truetype('arial.ttf', 11) #Fuente? TODO
        except:
            font=None
        
        width, height = imagen.size
        
        sup_izq = (20, 20)
        sup_der_1 = (width-220, 20)
        sup_der_2 = (width-85, 20)
        sup_der_3 = (width-140, 20)
        inf_izq = (20, height-65)
        inf_der = (width-115, height-85)
        
        nombre = f'{im.PatientName}'.replace('^', ' ')
        fecha = f"{im.StudyDate[6:]}/{im.StudyDate[4:6]}/{im.StudyDate[0:4]}"
        try:
            hora = f"{im.AcquisitionTime[0:2]}:{im.AcquisitionTime[2:4]}:{im.AcquisitionTime[4:6]}"
        except:
            hora = f"{im.StudyTime[0:2]}:{im.StudyTime[2:4]}:{im.StudyTime[4:6]}"

        text_sup_izq = f"{nombre}\n{im.PatientSex}\nID: {im.PatientID}"
        text_sup_der_1 = f"{im.InstitutionName}\n"
        text_sup_der_2 = f"\n Ref: {im.ReferringPhysicianName} / Perf:" #Si trae im.ReferringPhysicianName se puede ir de la image?
        text_sup_der_3 = f"\n\nStudy date: {fecha}\nStudy time: {hora}"
        text_inf_izq = f"W{im.WindowWidth}  /  C{im.WindowCenter}\n \n S-Value: {im.Sensitivity}"
        text_inf_der = f"{im.BodyPartExamined }\nPosition: {im.ViewPosition}\n{im.InstanceNumber} IMA {im.SeriesNumber}\nZoom factor: x0.99" #Queda fijo 0.99 porque no lo tiene guardado
        
        draw.text(sup_izq, text_sup_izq, font=font, fill='white', stroke_width=1, stroke_fill='black')    
        draw.text(sup_der_1, text_sup_der_1, font=font, fill='white', stroke_width=1, stroke_fill='black')
        draw.text(sup_der_2, text_sup_der_2, font=font, fill='white', stroke_width=1, stroke_fill='black')
        draw.text(sup_der_3, text_sup_der_3, font=font, fill='white', stroke_width=1, stroke_fill='black')
        draw.text(inf_izq, text_inf_izq, font=font, fill='white', stroke_width=1, stroke_fill='black') 
        draw.text(inf_der, text_inf_der, font=font, fill='white', stroke_width=1, stroke_fill='black') 

        #imagen.show()
        #imagen.save(fp=f"./pdf/{im.PatientName}.pdf", format="pdf")
        imagen.save(fp="dcm2pdf_temp.temp", format="png")    

        #if os.path.exists("dcm2pdf_temp.temp"):
        #    os.system('attrib +h dcm2pdf_temp.temp') #Puede generar error de permiso de acceso

        #nueva img2pdf
        a4inpt = (img2pdf.mm_to_pt(210), img2pdf.mm_to_pt(297))
        layout_fun = img2pdf.get_layout_fun(a4inpt)
        
        #generar nombre archivo pdf segun formato actual Apellido- Nombre- - CR- form dia-mes-año S{num} I0
        #archivo_nombre = f"{im.PatientID} {nombre} ({im.StudyDate[6:]}.{im.StudyDate[4:6]}.{im.StudyDate[0:4]} - {im.StudyTime[0:2]}h{im.StudyTime[2:4]}'{im.StudyTime[4:6]}'')"
        num = 0
        while os.path.exists(f"./pdf/{im.PatientID} {nombre}/{nombre.upper().replace(' ', '- ').replace(',', '- ')}- - CR- from {im.StudyDate[6:]}-{im.StudyDate[4:6]}-{im.StudyDate[0:4]} S{num} I0.pdf"):
            num+=1
            if num > 20:
                break

        archivo_nombre = f"{nombre.upper().replace(' ', '- ').replace(',', '- ')}- - CR- from {im.StudyDate[6:]}-{im.StudyDate[4:6]}-{im.StudyDate[0:4]} S{num} I0"

        if not os.path.exists(f"./pdf/{im.PatientID} {nombre}"):
            os.makedirs(f"./pdf/{im.PatientID} {nombre}")

        with open(f"./pdf/{im.PatientID} {nombre}/{archivo_nombre}.pdf", "wb") as f:
            f.write(img2pdf.convert("dcm2pdf_temp.temp", layout_fun=layout_fun)) # type: ignore

    #borrar archivo png temporal
    if os.path.exists("dcm2pdf_temp.temp"):
        os.remove("dcm2pdf_temp.temp")

    #guardar listado de archivos procesados, agregando a previos
    with open("dcm2pdf_lista_procesados", 'wb') as archivo:
        pickle.dump(listado_nuevo, archivo, protocol=pickle.HIGHEST_PROTOCOL)

    #end = time.time()
    #print(str(end-start))

#Para generar punto de acceso del programa
if __name__ == '__main__':
    main()

#Para compilar archivo con pyinstaller sin errores
#pyinstaller --onefile -F --hiddenimport=pydicom.encoders.gdcm --hiddenimport=pydicom.encoders.pylibjpeg --upx-dir=C:\Users\usuario\source\kpacks2pdf\upx-4.0.2-win64 --icon=C:\Users\usuario\source\kpacks2pdf\splash.ico --clean kpacks2pdf.py
#agregar --upx-dir "CARPETA" para reducir tamaño de .exe

#TODO
#Agregar directorio a procesar y guardar por consola? preguntando? argpars? os['ENV'] config.ini? sacar pathlib
#import tempfile para generar carpeta .tmp para archivo png?
#Guardar uid dentro de meta de pdf?
#CSV para presentar archivos procesados? probar reemplazar Pickle por SQLite?
#Modificar posicion texto segun DPI imagen y segun longitud string? #im.size / get taxtbox size / etc.
#Usar Mypy
#Refactorizar