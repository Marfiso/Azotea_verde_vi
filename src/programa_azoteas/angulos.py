# Librería para todo lo relacionado con ángulos del satélite
import calendar
import json
import numpy as np
import pandas as pd
import xml.etree.ElementTree as et
import programa_azoteas.data as pdata
from pyproj import Transformer


# FUNCIONES PARA ZENITH, usando el archivo que envió el profe
def get_fractional_year(year: int, day: int, hour: int): # Divisón cambia dependeindo si es año biciesto o no
    if calendar.isleap(year):
        den = 366
    else:
        den = 365

    frac_year = 2 * np.pi / den * (day - 1 + (hour - 12) / 24)
    return frac_year


def get_eqtime(frac_year: float):
    return 229.18 * (
        0.000075 
        + 0.001868 * np.cos(frac_year) 
        - 0.032077 * np.sin(frac_year) 
        - 0.014615 * np.cos(2 * frac_year) 
        - 0.040849 * np.sin(2 * frac_year)
    )


def get_declination(frac_year: float):
    return (
        0.006918 
        - 0.399912 * np.cos(frac_year) 
        + 0.070257 * np.sin(frac_year) 
        - 0.006758 * np.cos(2 * frac_year) 
        + 0.000907 * np.sin(2 * frac_year) 
        - 0.002697 * np.cos(3 * frac_year) 
        + 0.00148 * np.sin(3 * frac_year)
    )


def get_time_offset(eqtime: float, lon: float):
    return eqtime + 4 * lon + 60 * 6 # tz=-6


def get_true_solar_time(hour: float, min: float, sec: float, time_offset: float):
    return 60 * hour + min + sec / 60 + time_offset


def get_solar_hour_angle(tst: float):
    return tst / 4 - 180


def get_solar_zenith_angle(lon: float, lat: float, date):
    date = pd.to_datetime(date)

    year = date.year
    day = int(date.strftime('%j')) # Número de día del año, osea de los 365 días
    hour = date.hour
    minute = date.minute
    sec = date.second

    transformer = Transformer.from_crs("EPSG:32614", "EPSG:4326", always_xy=True)
    lon, lat = transformer.transform(lon, lat)

    frac_year = get_fractional_year(year=year, day=day, hour=hour)
    eqtime = get_eqtime(frac_year)
    time_offset = get_time_offset(eqtime, lon)
    decl = get_declination(frac_year)
    tst = get_true_solar_time(hour=hour, min=minute, sec=sec, time_offset=time_offset)
    ha = get_solar_hour_angle(tst)

    cosphi = np.sin(np.deg2rad(lat)) * np.sin(decl) + np.cos(np.deg2rad(lat)) * np.cos(decl) * np.cos(np.deg2rad(ha))
    phi = np.rad2deg(np.arccos(cosphi))

    return phi


# Función para obtener view angle given un metadata xml
def read_view_angle_from_xml(path):
    parse = et.parse(path)
    root = parse.getroot()
        
    for el in root.iter():
        if el.tag == "{http://schemas.planet.com/ps/v1/planet_product_metadata_geocorrected_level}spaceCraftViewAngle":
            return float(el.text)
        

# Función para obtener view angle given un metadata json
def read_view_angle_from_json(path):
    with open(path, "r") as f:
        data = json.load(f)
        return data["properties"]["view_angle"]
    

# Función para obtener el view angle del xml
# Hay archivos que no tienen metadata con xml, sino con json
# El archio de 20240607_172046_73_24f5 no tenía metadata at all (se eliminó de la carpte de scenes, fue el único)
# View angle is the spacecrafts across-track off-nadir viewing angle used for imaging, in degrees with + being east and - being west
def get_df_view_angle(directory):
    rows = []

    for fname in directory.glob("*AnalyticMS_SR_clip.tif"):
        date = pdata.get_time_from_name(fname.name)

        name = pdata.get_path_name_date(fname)

        name_xml = name + "_3B_AnalyticMS_metadata_clip.xml"
        path_xml = directory / name_xml
        
        name_json = name + "_metadata.json"
        path_json = directory / name_json
        
        if path_xml.exists():
            view_angle = read_view_angle_from_xml(path_xml)
        else:
            view_angle = read_view_angle_from_json(path_json)

        row = {
            "date": date,
            "view_angle": view_angle
        }
        rows.append(row)

    rows = pd.DataFrame(rows)
    rows = rows.set_index("date")
    
    return rows