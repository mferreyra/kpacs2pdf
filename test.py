import pydicom as dycom
import matplotlib.pyplot as plt
#from PIL import Image


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
plt.figure(figsize=(8.27, 11.69), dpi=150)
plt.imshow(im_np_array, cmap='gray_r', interpolation='nearest')
plt.axis('off')
plt.savefig("guardadoPrueba150.pdf", format='pdf', bbox_inches='tight', pad_inches=0)

#plt.show()
#plt.savefig("fname", dpi=None, facecolor='w', edgecolor='w', orientation='portrait', format=None, transparent=False, bbox_inches=None, pad_inches=0.1, metadata=None)

#plt.imsave("guardadoIM.pdf", im_np_array, cmap='gray')
