import pydicom as dicom
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont

im = dicom.dcmread("mama.dcm")
im_np_array = im.pixel_array

plt.figure(figsize=(8.27, 11.69), dpi=100)
plt.imshow(im_np_array, cmap='gray_r', interpolation='nearest')
plt.axis(False)
plt.savefig("dcm2pdf_temp.png", format='png', orientation='portrait', bbox_inches='tight')
plt.close()

imagen = Image.open("dcm2pdf_temp.png")
width, height = imagen.size
draw = ImageDraw.Draw(imagen)
font = ImageFont.truetype(r'C:\Users\System-Pc\Desktop\arial.ttf', 8)

arriba_izq = (15, 15)
arriba_der = (width-150, 15)
abajo_izq = (15, height-60)
abajo_der = (width-80, height-60)

text_arriba_izq = f"{im.PatientName}\n{im.PatientSex}\n{im.PatientID}"
text_arriba_der = f"{im.InstitutionName}\n Ref: {im.ReferringPhysicianName} / Perf: ''\nStudy date: {im.StudyDate}\nStudy time: {im.StudyTime}"
text_abajo_izq = f"W{im.WindowWidth} / C {im.WindowCenter}\n' '\nS-Value: {im.Sensitivity}"
text_abajo_der = f"{im.BodyPartExamined }\n'Position: {im.ViewPosition}'\n{im.InstanceNumber} IMA {im.SeriesNumber}\nZoom factor: x''"

draw.text(arriba_izq, text_arriba_izq, font=font)    
draw.text(arriba_der, text_arriba_der, font=font) 
draw.text(abajo_izq, text_abajo_izq, font=font) 
draw.text(abajo_der, text_abajo_der, font=font) 

imagen.save(fp="fin2.pdf", format="pdf")

""" 
#arriba_izq = (15, 15)
text_arriba_izq = f"{im.PatientName}\n{im.PatientSex}\n{im.PatientID}"

#arriba_der = (width-15, 15)
text_arriba_der = f"{im.InstitutionName}\n Ref: {im.ReferringPhysicianName} / Perf: ''\nStudy date: {im.StudyDate}\nStudy time: {im.StudyTime}"
#/ Perf: im.PerformedProtocolCodeSequence? im.StudyID?

#abajo_izq = (15, height-15)
text_abajo_izq = f"W{im.WindowWidth} / C {im.WindowCenter}\n' '\nS-Value: {im.Sensitivity}"

#abajo_der = (width-15, height-15)
text_abajo_der = f"{im.BodyPartExamined }\n'Position: {im.ViewPosition}'\n{im.InstanceNumber} IMA {im.SeriesNumber}\nZoom factor: x''"
#im.AcquisitionDeviceProcessingDescription
#im.InstanceNumber? "IMA"  im.SeriesNumber?
#"Zoom factor: " im.[Mag./Reduc. Ratio? im.RescaleSlope?
 """