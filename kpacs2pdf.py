from datetime import datetime
from configparser import ConfigParser
import img2pdf
import logging.config
import matplotlib.pyplot as plt
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from pydicom import dcmread
import sqlite3
import sys
from tqdm.auto import tqdm


def consultar_base(DB):
    '''Devolver set de UID's de placas DICOM ya procesadas a pdf'''
    connection = sqlite3.connect(DB)
    cursor = connection.cursor()
    lista = cursor.execute('''SELECT UID from Placas''').fetchall()
    lista = {item[0] for item in lista}
    cursor.close()
    connection.close()
    return lista


def crear_db(DB):
    '''Generar base de datos con placas convertidas a pdf, si no existe'''
    connection = sqlite3.connect(DB)
    cursor = connection.cursor()
    sql_crear_tabla_placas = """CREATE TABLE IF NOT EXISTS Placas(
                        UID TEXT PRIMARY KEY,
                        NombrePaciente TEXT,
                        IdPaciente TEXT,
                        Fecha TEXT,
                        Hora TEXT
                        );"""
    cursor.execute(sql_crear_tabla_placas)
    connection.commit()
    connection.close()


def generar_archivo_pdf(im, TEMP_FILE, nombre_paciente, fecha_placa, CARPETAS_PDF):
    '''Generar archivo pdf con  mismo nombre que bullzip: "Apellido- Nombre- - CR from dia-mes-año S{num} I0" '''
    num = 0
    nombre_carpeta = f"{im.PatientID} {nombre_paciente}"  # ! TODO
    nombre_upper = f"{nombre_paciente.upper().replace(' ', '- ').replace(',', '- ')}"
    while os.path.exists(f"{CARPETAS_PDF}/{nombre_carpeta}/{nombre_upper}- - CR from {fecha_placa} S{num} I0.pdf"):
        num += 1
        if num > 100:  # !Maxima cantidad (arbitraria) de pdfs por paciente, por seguridad (condicion infinite loop?)
            break
    nombre_pdf = f"{nombre_upper}- - CR from {fecha_placa} S{num} I0"
    if not os.path.exists(f"{CARPETAS_PDF}/{nombre_carpeta}"):
        os.makedirs(f"{CARPETAS_PDF}/{nombre_carpeta}")
    setup_A4 = (img2pdf.mm_to_pt(210), img2pdf.mm_to_pt(297))
    layout_fun = img2pdf.get_layout_fun(setup_A4)
    archivo_pdf = f"{nombre_carpeta}/{nombre_pdf}.pdf"
    with open(f"{CARPETAS_PDF}/{archivo_pdf}", "wb") as file:
        file.write(img2pdf.convert(TEMP_FILE.as_posix(), layout_fun=layout_fun))  # type: ignore


def generar_imagen_temp(im_numpy_array, TEMP_FILE):
    '''Generar imagen temporal para imagen del archivo DICOM'''
    plt.figure(figsize=(8.27, 11.69), dpi=150)  # para generar en tamaño de A4, con resolucion aceptable
    plt.imshow(im_numpy_array, cmap="gray_r", interpolation="nearest")
    plt.axis(False)
    # guardar imagen a png (para buscar tamaño correcto en pdf)
    plt.savefig(TEMP_FILE, format="png", orientation="portrait", bbox_inches="tight")
    # RuntimeWarning: Figures created through the pyplot interface are retained until explicitly closed and may consume too much memory.
    plt.close()


def insertar_placa_en_db(DB, im, nombre_paciente, fecha_placa, hora_placa):
    '''Insertar información de la placa procesada a pdf dentro de la base de datos'''
    fecha_db = f"{fecha_placa[6:]}-{fecha_placa[3:5]}-{fecha_placa[0:2]}"
    valores = (im.SOPInstanceUID, nombre_paciente, im.PatientID, fecha_db, hora_placa)
    connection = sqlite3.connect(DB)
    cursor = connection.cursor()
    cursor.execute("""INSERT INTO Placas VALUES(?, ?, ?, ?, ?)""", valores)
    connection.commit()
    connection.close()


def placa_ya_procesada(im, DB):
    '''Verificar contra la bade de datos si esta placa ya fue procesada'''
    connection = sqlite3.connect(DB)
    cursor = connection.cursor()
    if cursor.execute("""SELECT UID FROM Placas WHERE UID=?""", [im.SOPInstanceUID]).fetchone():
        cursor.close()
        connection.close()
        return True
    else:
        cursor.close()
        connection.close()
        return False


def procesar_config_file(path_ini, path_dicom_dir, path_pdf_dir, db_path, error_path):
    '''Procesar archivo .ini vs generarlo si no existe y salir del programa'''
    config_file = ConfigParser()
    if not path_ini.exists():
        with open(path_ini, 'x', encoding='UTF-8') as config_f:
            config_f.write(
                f'[Ruta carpeta archivos DICOM (Kpacks/Imagebox)]\n'
                f'DICOM_dir = {path_dicom_dir}\n\n'
                f'[Ruta carpeta archivos pdf generados]\n'
                f'PDF_dir = {path_pdf_dir}\n\n'
                f'[Ruta carpeta base de datos]\n'
                f'DB_dir = {db_path}\n\n'
                f'[Ruta carpeta archivo errores al procesar DICOM]\n'
                f'ERROR_dir = {error_path}\n\n')
            print("Generado archivo config.ini con directorios a procesar")
            sys.exit()
    config_file.read(path_ini, encoding='UTF-8')
    return config_file


def sobrescribir_imagen_temp(im, TEMP_FILE, nombre_paciente, fecha_placa, hora_placa):
    '''Colocar por sobre la imagen anotaciones de la placa adquirida'''
    imagen = Image.open(TEMP_FILE)
    draw = ImageDraw.Draw(imagen)
    font = ImageFont.truetype("arial.ttf", 11)
    width, height = imagen.size
    # coordenadas para escribir en cada esquina de la imagen
    sup_izq = (20, 20)  # utilizar font.getlength(text) o font.getbbox(text) para estimar posicion?
    sup_der_1 = (width - 220, 20)
    sup_der_2 = (width - 85, 20)
    sup_der_3 = (width - 140, 20)
    inf_izq = (20, height - 65)
    inf_der = (width - 115, height - 85)
    # texto a escribir en cada esquina de la imagen
    text_sup_izq = f"{nombre_paciente}\n{im.PatientSex}\nID: {im.PatientID}"
    text_sup_der_1 = f"{im.InstitutionName}\n"
    text_sup_der_2 = f"\n Ref: {im.ReferringPhysicianName} / Perf:"  # ?Si tengo im.ReferringPhysicianName se sale de la imagen?
    text_sup_der_3 = f"\n\nStudy date: {fecha_placa}\nStudy time: {hora_placa}"
    text_inf_izq = (f"W{im.WindowWidth}  /  C{im.WindowCenter}\n \n S-Value: {im.Sensitivity}")
    text_inf_der = f"{im.BodyPartExamined}\nPosition: {im.ViewPosition}\n{im.InstanceNumber} IMA {im.SeriesNumber}\nZoom factor: x0.99"  # *Zoom harcoded!
    draw.text(sup_izq, text_sup_izq, font=font, fill="white", stroke_width=1, stroke_fill="black")
    draw.text(sup_der_1, text_sup_der_1, font=font, fill="white", stroke_width=1, stroke_fill="black")
    draw.text(sup_der_2, text_sup_der_2, font=font, fill="white", stroke_width=1, stroke_fill="black")
    draw.text(sup_der_3, text_sup_der_3, font=font, fill="white", stroke_width=1, stroke_fill="black")
    draw.text(inf_izq, text_inf_izq, font=font, fill="white", stroke_width=1, stroke_fill="black")
    draw.text(inf_der, text_inf_der, font=font, fill="white", stroke_width=1, stroke_fill="black")
    # guardar cambios
    imagen.save(fp=TEMP_FILE, format="png")


def main():
    '''Punto de partida para la ejecución del programa'''
    logging.config.dictConfig({"disable_existing_loggers": True, "version": 1})  # *Para apagar warning de img2pdf
    # archivo config
    DEFAULT_INI_PATH = Path.cwd() / "kpacs2pdf.ini"
    DEFAULT_DICOM_DIR = Path("C:/KPacs/Imagebox")
    DEFAULT_PDF_DIR = Path.cwd() / "pdf"
    DEFAULT_DB_DIR = Path.cwd()
    DEFAULT_ERROR_DIR = Path.cwd()
    config_file = procesar_config_file(DEFAULT_INI_PATH, DEFAULT_DICOM_DIR, DEFAULT_PDF_DIR, DEFAULT_DB_DIR, DEFAULT_ERROR_DIR)
    # rutas carpetas y archivos utilizados
    CARPETA_DICOM_IMAGEBOX = Path(config_file.get('Ruta carpeta archivos DICOM (Kpacks/Imagebox)', 'DICOM_dir').strip('\"'))
    CARPETAS_PDF = Path(config_file.get('Ruta carpeta archivos pdf generados', 'PDF_dir').strip('\"'))
    CARPETA_DB = Path(config_file.get('Ruta carpeta base de datos', 'DB_dir').strip('\"'))
    CARPETA_ERRORES = Path(config_file.get('Ruta carpeta archivo errores al procesar DICOM', 'ERROR_dir').strip('\"'))
    TEMP_FILE = Path.cwd() / "kpacs2pdf_temp.temp"
    DB = CARPETA_DB / "kpacs2pf_procesados.db"
    ARCHIVO_ERRORES = CARPETA_ERRORES / "kpacs2pdf_errores.txt"
    # crear carpetas si no existen (evita error en img2pdf with open())
    for carpeta in [CARPETAS_PDF, CARPETA_DB, CARPETA_ERRORES]:
        if not os.path.exists(carpeta):
            os.mkdir(carpeta)
    # crear database si no existe una
    crear_db(DB)
    # listar archivos en directorio imagebox, cargar archivos ya procesados y hacer diff
    listado_carpeta_dcm = set(CARPETA_DICOM_IMAGEBOX.rglob("*.dcm"))
    listado_base_dcm = consultar_base(DB)  # ! TODO Procesar todos y detallar en base que proceso hice
    listado_archivos_dcm = listado_carpeta_dcm - listado_base_dcm
    # leer archivos DICOM
    for item in tqdm(listado_archivos_dcm, desc="Procesando archivos DICOM", colour="green", leave=True, position=0):
        try:
            im = dcmread(str(item))
            im_np_array = im.pixel_array
        except Exception as error:
            with open(ARCHIVO_ERRORES, "a+") as log:
                log.write(f"*|{datetime.now().strftime('%D %H:%M:%S')}| Archivo: {str(item)}\n    Error -> {repr(error)}\n")
            continue
        if (im.PatientID).strip().startswith("1-"):  # Saltear placas de Meva para no procesarlas  # ! TODO
            continue
        año = im.StudyDate[0:4]
        if int(año) < 2021:
            continue
        if placa_ya_procesada(im, DB):  # *Saltear placas en base de datos
            continue
        # procesar dcm para convertir a pdf
        nombre_paciente = f"{im.PatientName}".replace("^", " ")
        fecha_placa = f"{im.StudyDate[6:]}-{im.StudyDate[4:6]}-{im.StudyDate[0:4]}"
        hora_placa = f"{im.AcquisitionTime[0:2]}:{im.AcquisitionTime[2:4]}:{im.AcquisitionTime[4:6]}"
        generar_imagen_temp(im_np_array, TEMP_FILE)
        sobrescribir_imagen_temp(im, TEMP_FILE, nombre_paciente, fecha_placa, hora_placa)
        generar_archivo_pdf(im, TEMP_FILE, nombre_paciente, fecha_placa, CARPETAS_PDF)
        # guardar información de placa ya procesada a pdf en la base de datos
        try:
            insertar_placa_en_db(DB, im, nombre_paciente, fecha_placa, hora_placa)
        except Exception as error:
            with open(ARCHIVO_ERRORES, "a+") as log:
                log.write(f"*|{datetime.now().strftime('%D %H:%M:%S')}| Archivo: {str(item)}\n    Error -> {repr(error)}\n")
            continue

    # borrar archivo png temporal
    if os.path.exists(TEMP_FILE):
        os.remove(TEMP_FILE)


if __name__ == "__main__":
    main()


# TODO
# ! Validar datos im (im.PatientID, im.PatientName, etc)
# Procesar todas las im y detallar en db que proceso hice. Detallar ruta en db
# Validar ruta antes de os.mkdir
# opcion en config file para agregar string con ID parcial de placas para no procesar (Ej: "1-"" para saltear placas de Meva)
# opcion en config file para agregar string con fecha de placas para no procesar (Ej: <2021 para saltear placas viejas)
# archivo errores a formato CSV con plantilla utilizando --add-data? Incluir ruta (hyperlink) al archivo que fallo
# ? Usar Mypy/types hint
# ? Generar tests
