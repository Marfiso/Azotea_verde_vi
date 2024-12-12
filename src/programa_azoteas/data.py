# Funciones para obtener información a partir de data que se pasaa
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Función para sacar datetime de nombre de (para archivos de planet)
def get_time_from_name(name):
    components = name.split("_") # name está como path
    date = components[0]
    time = components[1]
    dati = pd.to_datetime(date + time)
    new_dt = dati.replace(hour = dati.hour - 6) # Restando 6h porque los datos están en UTC y México está en UTC-6
    return new_dt


# Función para obtener dataframe con los valores promedio por mes del VI del área determinada
# y las diferencias entre los valores del VI por mes
def get_df_monthly(data, shape):
    cut_area = data.rio.clip([shape])

    mean_values = []
    dates = []

    for x in range(0, cut_area.shape[0]):
        dates.append(cut_area[x].time.dt.strftime('%Y-%m').item())
        mean_values.append(cut_area[x].mean().item())
    
    df = pd.DataFrame(mean_values, dates)
    df = df.rename(columns={0:"value"})

    differences = np.diff(df["value"]).tolist()
    differences.insert(0, 0)
    df["dif"] = differences
    return df


# Función para obtener hora promedio de toma de imágenes
def df_time_toma(data):
    hours = data.time.dt.hour.values
    date = data.time.dt.strftime('%Y-%m').values

    df = pd.DataFrame(zip(date, hours), columns=["date", "hour"]).groupby("date")["hour"].mean()
    return df


# Función para obtener el nombre del archivo (fecha de la escena) given un path
def get_path_name_date(path):
    name = path.name.split("_3B")[0]
    return name


# Función para display tif como rgb
def plot_rgb(data):
    data = data[[2, 1, 0]] # Tomando únicamente axis de blue, green y red, en orden RGB
    data = np.moveaxis(data, 0, -1) # Moviendo el valor de 3 (referente a número de bandas) al final
    data = data.astype(float)
    data = data / np.nanmax(data) # Normalizando, dividiendo entre el valor max de todo el array
    return plt.imshow(data)



# Para datos de sentinel
# Función para obtener el timestamp (hora de inicio de toma) con base en el nombre del archivo
def get_time_sentinel_name(name):
    components = name.split("_")
    dt_inicio = components[0].split("T")
    date = dt_inicio[0]
    time = dt_inicio[1]
    dati = pd.to_datetime(date + time)
    new_dt = dati.replace(hour = dati.hour - 6) # Corrección de UTC-6 (México)
    return new_dt

