# Librería de funciones relacionadas a tratamiento de escenas
import programa_azoteas.data as pdata
import rioxarray as rxr
import xarray as xr


# Función para crear datacube con todas las bandas (Analysis y udm2)
def load_datasets(directory):
    datasets = [] # Creando lista vacía de datasets
    data_udm = []

    for fname in directory.glob("*.tif"): # Buscando únicamente archivos .tif
        dt = pdata.get_time_from_name(fname.name) # Sacando datetime de nombre de archivo, name está como path
        ds = rxr.open_rasterio(fname) # Abriendo para crear el dataset
        ds = ds.expand_dims(time=[dt]) # Agregando dimensión de tiempo a c/dataset con datetimte

        if "udm2" in str(fname):
            data_udm.append(ds)
        elif "AnalyticMS" in str(fname): # Sólo archivos con 4 bandas (Analytic)
            datasets.append(ds / 10000) # Agregando c/dataset a lista
            #Cada banda RBGN se divide entre 10,000 porque en la imagen se multiplicó por 10,000 para que no hubiera decimales, es regresarla a la original

    data = xr.concat(datasets, dim="time") # Concatenando data through axis de tiempo => cronología
    data["band"] = ["b", "g", "r", "nir"] # Renombrando

    
    udm = xr.concat(data_udm, dim="time") # Concatenando udm through axis de tiempo => cronología
    udm["band"] = ["clear", "snow", "cloud_shadow", "light_haze", "heavy_haze", "cloud", "confidence", "unusable"] # Renombrando

    concat = xr.concat([data, udm], dim="band") # Concatenando data y udm through bands para hacer datacube con todas las bandas (12)
    return concat


# Función para quitar scenes donde no hay info (imagen)
def remove_nodata(data):
    arr_bgr = data.sel(band=["b", "g", "r"])
    arr_bool = arr_bgr == 0 # Extrayendo un booleano (True/False) de los clipped para ver en cuáles hay 0 (True)
    arr_bool = ~arr_bool.all(dim=["x", "y", "band"]) # Sacando cuáles datasets tienen 0 en todo el arreglo (aka no hay valores en la zona de estudio, e invirtiendo el True/False
    
    arr_without_zeros = data[arr_bool] # Quedándonos únicamente con las que sí tienen datos en la zona (no 0)
    return arr_without_zeros


# Función para quitar scenes donde haya mucho de un parámtero (cloud, cloud shadow, light haze y heavy haze)
def clean_scenes(data, shape_area, band_name, threshold):
    band = data.sel(band=band_name) # Sacando la banda sobre la que se va a trabajar
    
    num_ones = (band == 1).sum(dim=["x", "y"]) # Cuantificando el número de 1's que hay por cada slice de tiempo (scene)
    frac_one = num_ones / shape_area # Dividiendo entre el área del shape a la que se cortó = Fracción de lo que se busca (cloud, etc)
    mask = frac_one < threshold # Booleano donde True es aquellos que frac sea menor al threshold (True = Menos de 0.1 de cobertura, False = mayor a 0.1 de cobertura)
    return data.loc[mask] # Pasando la mask a las scenes originales, entonces se quitan las que sean False (tiempo)



# Para datos de sentinel
# Función para crear datacube 4 datacubes (1: RGBN, 2: Cloud, 3: Cloudprob, 4: Cloudscore)
# Para las nubes sólo se usa el datacube de cloudscore, porque sentinel no produjo cloud masks
# desde Feb, 2022 hasta Feb, 2024. Cloudscore es la solución de ese error
# Aún así, dejemos los datacubes de cloud y cloudprob, why not
def load_datasets_sentinel(directory):
    datasets = [] # Creando lista vacía de datasets
    data_cloud = []
    data_cloudprob = []
    data_cloudscore = []

    for fname in directory.glob("*.tif"): # Buscando únicamente archivos .tif
        # t.append(fname)
        dt = pdata.get_time_sentinel_name(fname.name) # Sacando datetime de nombre de archivo, name está como path
        ds = rxr.open_rasterio(fname) # Abriendo para crear el dataset
        ds = ds.expand_dims(time=[dt]) # Agregando dimensión de tiempo a c/dataset con datetimte

        if "cloudprob" in str(fname): # Para archivos de cloud probability
            data_cloudprob.append(ds)
        elif "cloud.tif" in str(fname): # Archivos de cloud
            data_cloud.append(ds)
        elif "cloudscore.tif" in str(fname): # Archivos de cloudscore
            data_cloudscore.append(ds)
        else: # Todos los demás (RBGNs)
            datasets.append(ds / 1000) # Agregando c/dataset a lista
            #Cada banda RBGN se divide entre 10,000 porque en la imagen se multiplicó por 10,000 para que no hubiera decimales, es regresarla a la original

    data = xr.concat(datasets, dim="time") # Concatenando data through axis de tiempo => cronología
    data["band"] = ["b", "g", "r", "nir"] # Renombrando

    cloud = xr.concat(data_cloud, dim="time").sel(band=1).drop_vars("band") # Sólo una banda, y quitando el label de band

    cloudprob = xr.concat(data_cloudprob, dim="time").sel(band=1).drop_vars("band") # Sólo una banda, y quitando el label de band
    
    cloudscore = xr.concat(data_cloudscore, dim="time")
    cloudscore["band"] = ["cs", "cs_cdf"]

    return data, cloud, cloudprob, cloudscore


# Para sacar mask de donde no hay nubosidad
def get_clean_cloudscore_mask(data, threshold: int):
    scenes = data.sel(band="cs").drop_vars("band") # Utilizando únicamente imágenes de la banda "cs"
    num_clean = (scenes >= 0.7).sum(dim=["x", "y"]) # Sacando el número de pixeles arriba de 0.7 == 70% confidence que no son nubes (esto se lo di a mano, se puede cambiar aquí...
    # ... o agregando el confidence level como una variable ig)
    area = scenes.notnull().sum(dim=["x", "y"]) # Sacando área total. Como imagen es un cuadrado a fuerzas, aquellos afuera de shp irregular lo pone como nan, entonces contamos todos los no nan
    percent_clean = num_clean / area # Ratio de pixeles no nubes
    clean_mask = percent_clean >= threshold # Mask de únicamente aquellas scenes con ratio arriba de threshold (0.9 ideally == menos de 10% de nubosidad)

    return clean_mask