from datetime import datetime
from configparser import ConfigParser
import img2pdf
import logging.config
import matplotlib.pyplot as plt
import os
from pathlib import Path
import pickle
from PIL import Image, ImageDraw, ImageFont
from pydicom import dcmread
import sqlite3
from tqdm.auto import tqdm


def procesar_config_file(path_ini, path_dicom_dir, path_pdf_dir):
    '''procesar o generar .ini file'''
    config_file = ConfigParser()
    if not path_ini.exists():
        with open(path_ini, 'x', encoding='UTF-8') as config_f:
            config_f.write(
            f'[dicom (Kpacks/Imagebox)]\n'
            f'DICOM_dir = {path_dicom_dir}\n\n'
            f'[pdf (Pacientes)]\n'
            f'PDF_dir = {path_pdf_dir}\n')
    config_file.read(path_ini, encoding='UTF-8')
    return config_file


def generar_imagen_temp(im_numpy_array, TEMP_FILE):
    plt.figure(figsize=(8.27, 11.69), dpi=150)  # para generar en tamaño de A4, con resolucion aceptable
    plt.imshow(im_numpy_array, cmap="gray_r", interpolation="nearest")
    plt.axis(False)
    # guardar imagen a png (para buscar tamaño correcto en pdf)
    plt.savefig(TEMP_FILE, format="png", orientation="portrait", bbox_inches="tight")
    # RuntimeWarning: Figures created through the pyplot interface are retained until explicitly closed and may consume too much memory.
    plt.close()


def sobrescribir_imagen_temp(im, TEMP_FILE, nombre_paciente, fecha_placa, hora_placa):
    imagen = Image.open(TEMP_FILE)
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
    text_sup_der_2 = f"\n Ref: {im.ReferringPhysicianName} / Perf:"  # *Si im.ReferringPhysicianName no vacio,sale de la imagen?
    text_sup_der_3 = f"\n\nStudy date: {fecha_placa}\nStudy time: {hora_placa}"
    text_inf_izq = (f"W{im.WindowWidth}  /  C{im.WindowCenter}\n \n S-Value: {im.Sensitivity}")
    text_inf_der = f"{im.BodyPartExamined }\nPosition: {im.ViewPosition}\n{im.InstanceNumber} IMA {im.SeriesNumber}\nZoom factor: x0.99"  # *Zoom harcoded!
    draw.text(sup_izq, text_sup_izq, font=font, fill="white", stroke_width=1, stroke_fill="black")
    draw.text(sup_der_1, text_sup_der_1, font=font, fill="white", stroke_width=1, stroke_fill="black")
    draw.text(sup_der_2, text_sup_der_2, font=font, fill="white", stroke_width=1, stroke_fill="black")
    draw.text(sup_der_3, text_sup_der_3, font=font, fill="white", stroke_width=1, stroke_fill="black")
    draw.text(inf_izq, text_inf_izq, font=font, fill="white", stroke_width=1, stroke_fill="black")
    draw.text(inf_der, text_inf_der, font=font, fill="white", stroke_width=1, stroke_fill="black")
    # guardar cambios
    imagen.save(fp=TEMP_FILE, format="png")


def generar_archivo_pdf(im, TEMP_FILE, nombre_paciente, fecha_placa, CARPETAS_PDF):
    # generar pdf con  mismo nombre que bullzip: "Apellido- Nombre- - CR from dia-mes-año S{num} I0"
    num = 0
    nombre_carpeta = f"{im.PatientID} {nombre_paciente}"
    nombre_upper = f"{nombre_paciente.upper().replace(' ', '- ').replace(',', '- ')}"
    while os.path.exists(f"{CARPETAS_PDF}/{nombre_carpeta}/{nombre_upper}- - CR from {fecha_placa} S{num} I0.pdf"):
        num += 1  # ! Puede que duplique imágenes si vuelvo a procesar la misma (Si borro lista procesados)
        if num > 50:  # numero arbitrario de máxima cantidad de imagenes por paciente?
            break
    nombre_pdf = f"{nombre_upper}- - CR from {fecha_placa} S{num} I0"
    if not os.path.exists(f"{CARPETAS_PDF}/{nombre_carpeta}"):
        os.makedirs(f"{CARPETAS_PDF}/{nombre_carpeta}")
    setup_A4 = (img2pdf.mm_to_pt(210), img2pdf.mm_to_pt(297))
    layout_fun = img2pdf.get_layout_fun(setup_A4)
    archivo_pdf = f"{nombre_carpeta}/{nombre_pdf}.pdf"
    with open(f"{CARPETAS_PDF}/{archivo_pdf}", "wb") as file:
        file.write(img2pdf.convert(TEMP_FILE.as_posix(), layout_fun=layout_fun))  # type: ignore


def crear_db(DB_PATH):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    sql_crear_tabla_placas = """CREATE TABLE IF NOT EXISTS Placas(
                        UID REAL PRIMARY KEY, 
                        NombrePaciente TEXT,
                        IdPaciente INT NOT NULL,
                        Fecha TEXT,
                        Hora TEXT
                        );"""
    cursor.execute(sql_crear_tabla_placas)
    connection.commit()
    connection.close()


def insertar_placa_en_db(DB_PATH, im, nombre_paciente, fecha_placa, hora_placa):
    fecha_db = f"{fecha_placa[6:]}-{fecha_placa[3:5]}-{fecha_placa[0:2]}"
    valores = (im.SOPInstanceUID, nombre_paciente, im.PatientID, fecha_db, hora_placa) 
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute("""INSERT INTO Placas VALUES(?, ?, ?, ?, ?)""", valores)
    connection.commit()
    connection.close()


def placa_ya_procesada(im, DB_PATH):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    if cursor.execute("""SELECT UID FROM Placas WHERE UID=?""", [im.SOPInstanceUID] ).fetchone():
        cursor.close()
        connection.close()
        return True
    else:
        cursor.close()
        connection.close()
        return False


def main():
    logging.config.dictConfig({"disable_existing_loggers": True, "version": 1})  # *Para apagar warning de img2pdf
    # archivo config
    DEFAULT_INI_PATH = Path.cwd()/"kpacs2pdf.ini"
    DEFAULT_DICOM_DIR = "C:/KPacs/Imagebox"
    DEFAULT_PDF_DIR = Path.cwd()/"pdf"
    config_file = procesar_config_file(DEFAULT_INI_PATH, DEFAULT_DICOM_DIR, DEFAULT_PDF_DIR)
    # rutas  # agregar a config_file?
    LISTA_PROCESADOS = Path.cwd()/"kpacs2pdf_lista_procesados"
    ARCHIVO_ERRORES = Path.cwd()/"kpacs2pdf_errores.txt"
    TEMP_FILE = Path.cwd()/"kpacs2pdf_temp.temp"
    CARPETAS_PDF = Path(config_file.get('pdf (Pacientes)', 'PDF_dir').strip('\"'))
    CARPETA_IMAGEBOX = Path(config_file.get('dicom (Kpacks/Imagebox)', 'DICOM_dir').strip('\"'))
    DB_PATH = Path.cwd()/"kpacs2pf_procesados.db"

    # !----------------------
    # listar archivos en directorio
    listado_dcm_nuevo = set(CARPETA_IMAGEBOX.rglob("*.dcm"))
    # cargar archivos ya procesados y hacer diff
    if os.path.exists(LISTA_PROCESADOS):  # TODO cambiar a base SQLite
        with open(LISTA_PROCESADOS, "rb") as file:
            listado_dcm_procesados = pickle.load(file)
    else:
        listado_dcm_procesados = set() # *Rutas sin duplicados
    listado_dcm = listado_dcm_nuevo - listado_dcm_procesados
    crear_db(DB_PATH)
    #----------------------

    # crear carpeta para guardar pdf si no existe (evit error en img2pdf with open())
    if not os.path.exists(CARPETAS_PDF):
        os.mkdir(CARPETAS_PDF)
    # leer archivos dicom
    for item in tqdm(listado_dcm, desc="Procesando imagenes", colour="green", leave=True, position=0):
        try:
            im = dcmread(str(item))
            im_np_array = im.pixel_array
        except Exception as error:
            with open(ARCHIVO_ERRORES, "a+") as log:
                log.write(f"*|{datetime.now().strftime('%D %H:%M:%S')}| Archivo: {str(item)}\n    Error -> {repr(error)}\n")
            continue
        if (im.PatientID).startswith("1-"):  # * Saltear imagenes de MEVA para no procesarlas
            continue
        if placa_ya_procesada(im, DB_PATH):  # !
            continue
        # procesados
        nombre_paciente = f"{im.PatientName}".replace("^", " ")
        fecha_placa = f"{im.StudyDate[6:]}-{im.StudyDate[4:6]}-{im.StudyDate[0:4]}"
        hora_placa = f"{im.AcquisitionTime[0:2]}:{im.AcquisitionTime[2:4]}:{im.AcquisitionTime[4:6]}"
        generar_imagen_temp(im_np_array, TEMP_FILE)
        sobrescribir_imagen_temp(im, TEMP_FILE, nombre_paciente, fecha_placa, hora_placa)
        generar_archivo_pdf(im, TEMP_FILE, nombre_paciente, fecha_placa, CARPETAS_PDF)
        # !
        insertar_placa_en_db(DB_PATH, im, nombre_paciente, fecha_placa, hora_placa)

    # borrar archivo png temporal
    if os.path.exists(TEMP_FILE):
        os.remove(TEMP_FILE)
    # guardar listado de archivos procesados, agregando a previos
    with open(LISTA_PROCESADOS, "wb") as archivo:
        pickle.dump(listado_dcm_nuevo, archivo, protocol=pickle.HIGHEST_PROTOCOL)  # TODO ver SQLite


if __name__ == "__main__":
    main()


# TODO
# SQLite
# ! agregar todas las rutas a config
# ? Modificar posicion texto segun DPI imagen y segun longitud string? #im.size, get textbox size, etc.
# ? Usar Mypy
# ? Generar tests
