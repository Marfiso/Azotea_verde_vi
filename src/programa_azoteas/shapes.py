# Librería para cosas relacionadas a shps
import geopandas as gpd


# Función para obtener archivo shape con crs correcto
def get_shape(shp_loc):
    shape = gpd.read_file(shp_loc)
    shape = shape.to_crs("EPSG:32614")
    shape = shape["geometry"].item()
    return shape


# Función para obtener valor de área del polígono que se pase
def get_shape_area(scenes, shape):
    dummy = scenes[0, 0].copy() # Creando un arreglo con las dimensiones de x, y
    dummy[:, :] = 1 # Convirtiendo todos los valores de pix a 1
    dummy = dummy.rio.clip([shape]) # Clipping a la shape que se pasa, entonces los que estan fuera de la shape son 0
    shape_area = dummy.sum().item() # Haciendo suma de cuántos 1's hay = Área (en pixeles)
    return shape_area