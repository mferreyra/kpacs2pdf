import pathlib
import pickle

carpeta = pathlib.Path(r"C:\Users\mferreyra\Desktop\Kpacks Quilmes")
listado = set(carpeta.rglob("[0-9].*.dcm"))

with open("lista", 'wb') as archivo:
    pickle.dump(listado, archivo, protocol=pickle.HIGHEST_PROTOCOL)

with open ("lista", 'rb') as leer:
    lista2 = pickle.load(leer)
