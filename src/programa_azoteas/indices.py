# Librería para funciones relacionadas a los índices (por ahora, sólo usamos ndvi, evi y savi)
import pandas as pd


# Fución para sacar Normalized Differential Vegetation Index (NDVI) de imágenes
# No se le pasa shape de clip porque los valores de afuera de la shape los pone como nan bc denominador es 0
def ndvi_scenes(data):
    arr_ndvi = (data.sel(band="nir") - data.sel(band="r")) / (data.sel(band="nir") + data.sel(band="r"))
    
    return arr_ndvi


# Función para sacar Enhance Vegetation Index (EVI) de las imágenes
# Hay que pasarle un shape para clip porque los valores de afuera los pone como 0, no como nan
def evi_scenes(data, shape):
    arr_evi = 2.5 * ((data.sel(band="nir") - data.sel(band="r")) / (data.sel(band="nir") + 6 * data.sel(band="r") - 7.5 * data.sel(band="b") + 1))
    arr_evi = arr_evi.rio.clip([shape])
    
    return arr_evi


# Función para sacar squared R-B NDVI index (SRBNI)
def srbni_scenes(data):
    arr_rbni = (data.sel(band="nir")**2 - data.sel(band="r") * data.sel(band="b")) / (data.sel(band="nir")**2 + data.sel(band="r") * data.sel(band="b"))

    return arr_rbni


# Función para sacar Soil Adjusted Vegetation Index (SAVI)
def savi_scenes(data, shape):
    arr_savi = 1.5 * ((data.sel(band="nir") - data.sel(band="r")) / (data.sel(band="nir") + data.sel(band="r") + 0.5))
    arr_savi = arr_savi.rio.clip([shape])

    return arr_savi


# Función para plot de varios índices de vegetación sobre misma área, pasando un df
def plot_index_comparison(df: pd.DataFrame, cut: str, ax):
    dates = df.index.unique(level="date").sort_values().to_numpy() # Sacando los índices de fechas para el eje y

    subdf = df.loc[cut] # Creando mini df con base en el área que se pasa
    indices = df.index.unique(level="name").sort_values() # Sacando lista de nombre de índices de vegetación

    for index in indices:
        temp_df = subdf.loc[index] # Localizando tipo de índice sobre el df del área
        x = temp_df.index
        y = temp_df["value"]
        ax.plot(x, y, label=index)

    ax.legend()
    ax.set_xticks(dates[::2])
    ax.set_title(cut)