import pydicom as dycom
import matplotlib.pyplot as plt
from PIL import Image
import os
#import subprocess
#import time

#start = time.time()

#print(im_np_array.shape)
#im = Image.fromarray(im_np_array)
#im.show()
#im.save("guardado.png")
#print(type(im))

im = dycom.dcmread("./prueba2.dcm")
#print(dir(im))
#print(im.WindowCenter)
#print(im.WindowWidth)
im_np_array = im.pixel_array

#rc('figure', figsize=(8.27,11.69))
#plt.rcParams['figure.figsize'] = (8.27, 11.026)
fig = plt.figure(figsize=(8.27, 11.69), dpi=100)
#fig.subplots_adjust(left=0, right=0, top=0, bottom=0)
ax = fig.add_subplot()
ax.imshow(im_np_array, cmap='gray_r', interpolation='nearest')
#plt.imshow(im_np_array, cmap='gray_r', interpolation='nearest')
#print(im_np_array.shape)
#plt.axis(False)
ax.axis(False)

#ax=plt.subplots_adjust

#ax.text(1,1,"texto ArribaIzq", horizontalalignment='right', verticalalignment="top")
#plt.legend("pasd")
#plt.text(0,2048,"texto AbajoIzq")
#plt.annotate(text="texto ArribaIzq", xy=[0,1], xycoords='figure fraction')
#plt.text(1,1,"texto ArribaDer", horizontalalignment='right', verticalalignment="top")
#plt.text(0,0,"texto AbajoDer", horizontalalignment='right', verticalalignment="bottom")
plt.savefig("temp.png", format='png', orientation='portrait', bbox_inches='tight')
#subprocess.check_call(["attrib","+H","temp.png"])
imagen = Image.open("temp.png")
imagen.save("fin.pdf", format="pdf")

os.remove("temp.png")

#end = time.time()
#print(str(end-start))


#plt.show()
#plt.savefig("fname", dpi=None, facecolor='w', edgecolor='w', orientation='portrait', format=None, transparent=False, bbox_inches=None, pad_inches=0.1, metadata=None)

#plt.imsave("guardadoIM.pdf", im_np_array, cmap='gray')
