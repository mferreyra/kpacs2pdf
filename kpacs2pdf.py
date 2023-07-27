from datetime import datetime
import img2pdf
import logging.config
import matplotlib.pyplot as plt
import os
from pathlib import Path
import pickle
from PIL import Image, ImageDraw, ImageFont
import pydicom
from tqdm.auto import tqdm


def generar_imagen_temp(im_numpy_array, temp_file):
    plt.figure(figsize=(8.27, 11.69), dpi=150)  # para generar en tamaño de A4, con resolucion aceptable
    plt.imshow(im_numpy_array, cmap="gray_r", interpolation="nearest")
    plt.axis(False)
    # guardar imagen a png (para buscar tamaño correcto en pdf)
    plt.savefig(temp_file, format="png", orientation="portrait", bbox_inches="tight")
    # RuntimeWarning: Figures created through the pyplot interface are retained until explicitly closed and may consume too much memory.
    plt.close()
    return temp_file


def sobrescribir_imagen_temp(im, temp_file, nombre_paciente, fecha, hora):
    imagen = Image.open(temp_file)
    draw = ImageDraw.Draw(imagen)
    font = ImageFont.truetype("arial.ttf", 11)
    width, height = imagen.size
    # coordenadas para escribir en cada esquina
    sup_izq = (20, 20)
    sup_der_1 = (width - 220, 20)
    sup_der_2 = (width - 85, 20)
    sup_der_3 = (width - 140, 20)
    inf_izq = (20, height - 65)
    inf_der = (width - 115, height - 85)
    # texto a escribir en cada una
    text_sup_izq = f"{nombre_paciente}\n{im.PatientSex}\nID: {im.PatientID}"
    text_sup_der_1 = f"{im.InstitutionName}\n"
    text_sup_der_2 = f"\n Ref: {im.ReferringPhysicianName} / Perf:"  # ? Si im.ReferringPhysicianName no esta vacio, se puede ir de la image?
    text_sup_der_3 = f"\n\nStudy date: {fecha}\nStudy time: {hora}"
    text_inf_izq = (f"W{im.WindowWidth}  /  C{im.WindowCenter}\n \n S-Value: {im.Sensitivity}")
    text_inf_der = f"{im.BodyPartExamined }\nPosition: {im.ViewPosition}\n{im.InstanceNumber} IMA {im.SeriesNumber}\nZoom factor: x0.99"  # Zoom harcoded!
    draw.text(sup_izq, text_sup_izq, font=font, fill="white", stroke_width=1, stroke_fill="black")
    draw.text(sup_der_1, text_sup_der_1, font=font, fill="white", stroke_width=1, stroke_fill="black")
    draw.text(sup_der_2, text_sup_der_2, font=font, fill="white", stroke_width=1, stroke_fill="black")
    draw.text(sup_der_3, text_sup_der_3, font=font, fill="white", stroke_width=1, stroke_fill="black")
    draw.text(inf_izq, text_inf_izq, font=font, fill="white", stroke_width=1, stroke_fill="black")
    draw.text(inf_der, text_inf_der, font=font, fill="white", stroke_width=1, stroke_fill="black")
    # imagen.save(fp=f"./pdf/{im.PatientName}.pdf", format="pdf")
    imagen.save(fp=temp_file, format="png")


def generar_archivo_pdf(im, temp_file, nombre_paciente, fecha):
    # generar archivo pdf igual a formato nombre con bullzip: "Apellido- Nombre- - CR from dia-mes-año S{num} I0"
    num = 0
    nombre_carpeta = f"{im.PatientID} {nombre_paciente}"
    nombre_upper = f"{nombre_paciente.upper().replace(' ', '- ').replace(',', '- ')}"
    while os.path.exists(f"./pdf/{nombre_carpeta}/{nombre_upper} - - CR from {fecha} S{num} I0.pdf"):
        num += 1  # ! Puede ocurrir que duplique imágenes si vuelvo a procesar la misma, ya que le asignará un num diferente (Si borro lista procesados)
        if num > 20:
            break
    nombre_pdf = f"{nombre_upper}- - CR from {fecha} S{num} I0"
    if not os.path.exists(f"./pdf/{nombre_carpeta}"):
        os.makedirs(f"./pdf/{nombre_carpeta}")
    setup_A4 = (img2pdf.mm_to_pt(210), img2pdf.mm_to_pt(297))
    layout_fun = img2pdf.get_layout_fun(setup_A4)
    archivo_pdf = f"{nombre_carpeta}/{nombre_pdf}.pdf"
    with open(f"./pdf/{archivo_pdf}", "wb") as file:
        file.write(img2pdf.convert(temp_file, layout_fun=layout_fun))  # type: ignore


def main():
    logging.config.dictConfig({"disable_existing_loggers": True, "version": 1})  # * Para apagar warning de img2pdf
    LISTA_PROCESADOS = "kpacs2pdf_lista_procesados"
    TEMP_FILE_NAME = "kpacs2pdf_temp.temp"  # TODO cambiar a PATH
    ARCHIVO_ERRORES = "kpacs2pdf_errores.txt"

    # listar archivos en directorio
    # carpeta = Path(r"C:\Users\mferreyra\Desktop\Kpacks Quilmes")
    carpeta = Path(r"C:\Users\usuario\Documents\Trabajo\kpacs 28.06-30.06")  # TODO cambiar a leer de config file
    # carpeta = Path(r"C:\Users\usuario\source\kpacs2pdf\DICOM test")
    listado_nuevo = set(carpeta.rglob("*.dcm"))
    # cargar archivos ya procesados y hacer diff
    if os.path.exists(LISTA_PROCESADOS):  # TODO cambiar a base SQLite
        with open(LISTA_PROCESADOS, "rb") as file:
            listado_procesados = pickle.load(file)
    else:
        listado_procesados = set()
    listado = listado_nuevo - listado_procesados
    # crear carpeta para guardar pdf si no existe (evit error en img2pdf with open())
    if not os.path.exists("./pdf/"):  # TODO leer de config file
        os.makedirs("./pdf/")

    # leer archivos dicom
    for item in tqdm(listado, desc="Procesando imagenes", colour="green", leave=True, position=0):
        try:
            im = pydicom.dcmread(str(item))
            im_np_array = im.pixel_array
        except Exception as error:
            with open(ARCHIVO_ERRORES, "a+") as log:
                log.write(f"*|{datetime.now().strftime('%D %H:%M:%S')}| Archivo: {str(item)}\n    Error -> {repr(error)}\n")
            continue
        if (im.PatientID).startswith("1-"):  # * Saltear imagenes de MEVA para no procesarlas
            continue

        nombre_paciente = f"{im.PatientName}".replace("^", " ")
        fecha = f"{im.StudyDate[6:]}/{im.StudyDate[4:6]}/{im.StudyDate[0:4]}"
        hora = f"{im.AcquisitionTime[0:2]}:{im.AcquisitionTime[2:4]}:{im.AcquisitionTime[4:6]}"
        temp_file = generar_imagen_temp(im_np_array, TEMP_FILE_NAME)  # TODO cambiar a Path
        sobrescribir_imagen_temp(im, temp_file, nombre_paciente, fecha, hora)
        generar_archivo_pdf(im, temp_file, nombre_paciente, fecha)

    # borrar archivo png temporal
    if os.path.exists(TEMP_FILE_NAME):
        os.remove(TEMP_FILE_NAME)
    # guardar listado de archivos procesados, agregando a previos
    with open(LISTA_PROCESADOS, "wb") as archivo:
        pickle.dump(listado_nuevo, archivo, protocol=pickle.HIGHEST_PROTOCOL)


if __name__ == "__main__":
    main()

# * Para compilar archivo con pyinstaller sin errores
# * pyinstaller --onefile -F --hiddenimport=pydicom.encoders.gdcm --hiddenimport=pydicom.encoders.pylibjpeg
# * --upx-dir=C:\Users\usuario\source\kpacs2pdf\upx-4.0.2-win64 --icon=C:\Users\usuario\source\kpacs2pdf\splash.ico --clean kpacs2pdf.py
# * agregar --upx-dir "CARPETA" para reducir tamaño de .exe generado en carpeta dist

# TODO
# Agregar directorio a procesar y guardar por consola? preguntando? argpars? os['ENV'] config.ini?
# * carpeta = Path(r"C:\KPacs\Imagebox")
# ? import tempfile para generar carpeta .tmp para archivo png?
# ? Guardar uid de cada dicom dentro de meta de pdf? dentro de base de procesados?
# CSV para presentar archivos procesados? probar reemplazar Pickle por SQLite?
# Modificar posicion texto segun DPI imagen y segun longitud string? #im.size / get textbox size / etc.
# Usar Mypy
# Generar tests
