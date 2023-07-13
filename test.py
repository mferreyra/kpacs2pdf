import pydicom as dicom
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
import img2pdf

im = dicom.dcmread("mama.dcm")
im_np_array = im.pixel_array

plt.figure(figsize=(8.27, 11.69), dpi=100)
plt.imshow(im_np_array, cmap="gray_r", interpolation="nearest")
plt.axis(False)
plt.savefig(
    "dcm2pdf_temp.png", format="png", orientation="portrait", bbox_inches="tight"
)
plt.close()

# imagen = Image.open("dcm2pdf_temp.png")

a4inpt = (img2pdf.mm_to_pt(210), img2pdf.mm_to_pt(297))
layout_fun = img2pdf.get_layout_fun(a4inpt)
with open("name.pdf", "wb") as f:
    f.write(img2pdf.convert("dcm2pdf_temp.png", layout_fun=layout_fun))


# width, height = imagen.size
# draw = ImageDraw.Draw(imagen)
# font = ImageFont.truetype(r"C:\Users\System-Pc\Desktop\arial.ttf", 8)

# sup_izq = (15, 15)
# sup_der = (width - 150, 15)
# inf_izq = (15, height - 60)
# inf_der = (width - 80, height - 60)

# text_sup_izq = f"{im.PatientName}\n{im.PatientSex}\n{im.PatientID}"
# text_sup_der = f"{im.InstitutionName}\n Ref: {im.ReferringPhysicianName} / Perf: ''\nStudy date: {im.StudyDate}\nStudy time: {im.StudyTime}"
# text_inf_izq = (
#     f"W{im.WindowWidth} / C {im.WindowCenter}\n' '\nS-Value: {im.Sensitivity}"
# )
# text_inf_der = f"{im.BodyPartExamined }\n'Position: {im.ViewPosition}'\n{im.InstanceNumber} IMA {im.SeriesNumber}\nZoom factor: x''"

# draw.text(sup_izq, text_sup_izq, font=font)
# draw.text(sup_der, text_sup_der, font=font)
# draw.text(inf_izq, text_inf_izq, font=font)
# draw.text(inf_der, text_inf_der, font=font)

# imagen.save(fp="fin2.pdf", format="pdf")


# # sup_izq = (15, 15)
# text_sup_izq = f"{im.PatientName}\n{im.PatientSex}\n{im.PatientID}"

# # sup_der = (width-15, 15)
# text_sup_der = f"{im.InstitutionName}\n Ref: {im.ReferringPhysicianName} / Perf: ''\nStudy date: {im.StudyDate}\nStudy time: {im.StudyTime}"
# # / Perf: im.PerformedProtocolCodeSequence? im.StudyID?

# # inf_izq = (15, height-15)
# text_inf_izq = (
#     f"W{im.WindowWidth} / C {im.WindowCenter}\n' '\nS-Value: {im.Sensitivity}"
# )

# # inf_der = (width-15, height-15)
# text_inf_der = f"{im.BodyPartExamined }\n'Position: {im.ViewPosition}'\n{im.InstanceNumber} IMA {im.SeriesNumber}\nZoom factor: x''"
# # im.AcquisitionDeviceProcessingDescription
# # im.InstanceNumber? "IMA"  im.SeriesNumber?
# # "Zoom factor: " im.[Mag./Reduc. Ratio? im.RescaleSlope?
