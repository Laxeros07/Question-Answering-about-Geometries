import geopandas as gpd
import csv
import pandas as pd
import centroid
import numpy as np

# Import .shp file into a GeoPandas DataFrame
geopandas_f = gpd.read_file('Graph_old\Data_Management\Shapes_NRW\\federalStates.shp')
geopandas_a = gpd.read_file('Graph_old\Data_Management\Shapes_NRW\\administrativeDistricts.shp')
geopandas_d = gpd.read_file('Graph_old\Data_Management\Shapes_NRW\\districts.shp')
geopandas_c = gpd.read_file('Graph_old\Data_Management\Shapes_NRW\\cities.shp')

# Convert geospatial data to latitude/longitude coordinate system
converted_df_f = geopandas_f.to_crs('EPSG:4326')
converted_df_a = geopandas_a.to_crs('EPSG:4326')
converted_df_d = geopandas_d.to_crs('EPSG:4326')
converted_df_c = geopandas_c.to_crs('EPSG:4326')

#converted_df_all = np.concatenate(converted_df_c, converted_df_d, converted_df_a, converted_df_f))

def createIds(df, prefix):
    names = df.Name

    i = 1
    ID = []
    for name in names:
        ID.append(prefix+str(i))
        i = i+1
    return ID

ids_c = createIds(converted_df_c, "C")
ids_d = createIds(converted_df_d, "D")
ids_a = createIds(converted_df_a, "A")
ids_f = createIds(converted_df_f, "F")

ids_all = np.concatenate((ids_c, ids_d, ids_a, ids_f))

def createCentroids(df):
    geometry = df.geometry

    centroids = []
    for g in geometry:
        centroids.append(centroid.calculate_centroid(g))
    return centroids

centroids_c = createCentroids(converted_df_c)
centroids_d = createCentroids(converted_df_d)   
centroids_a = createCentroids(converted_df_a)
centroids_f = createCentroids(converted_df_f)

def createAreas(df):
    geometry = df.geometry

    areas = []
    for g in geometry:
        areas.append(centroid.calculate_area(g))
    return areas

# Area
areas_c = createAreas(converted_df_c)
areas_d = createAreas(converted_df_d)
areas_a = createAreas(converted_df_a)
areas_f = createAreas(converted_df_f)

cities = {"ID":ids_c, "Name": converted_df_c.Name, "Geometry": converted_df_c.geometry, "Centroid": centroids_c, "Area": areas_c}
districts = {"ID":ids_d, "Name": converted_df_d.Name, "Geometry": converted_df_d.geometry, "Centroid": centroids_d, "Area": areas_d}
administrativeDistricts = {"ID":ids_a, "Name": converted_df_a.Name, "Geometry": converted_df_a.geometry, "Centroid": centroids_a, "Area": areas_a}
federalStates = {"ID":ids_f, "Name": converted_df_f.Name, "Geometry": converted_df_f.geometry, "Centroid": centroids_f, "Area": areas_f}

df_cities = pd.DataFrame(cities) 
df_cities.to_csv('Graph_old\Data_Management\\test_new_model\id_cities.csv', index=False, sep = ",") 

df_districts = pd.DataFrame(districts)
df_districts.to_csv('Graph_old\Data_Management\\test_new_model\id_districts.csv', index=False, sep = ",") 

df_administrativeDistricts = pd.DataFrame(administrativeDistricts)
df_administrativeDistricts.to_csv('Graph_old\Data_Management\\test_new_model\id_administrativeDistricts.csv', index=False, sep = ",") 

df_federalStates = pd.DataFrame(federalStates)
df_federalStates.to_csv('Graph_old\Data_Management\\test_new_model\id_federalStates.csv', index=False, sep = ",") 

