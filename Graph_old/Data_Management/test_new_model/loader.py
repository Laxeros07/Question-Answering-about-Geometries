import geopandas as gpd
import numpy as np

def load_layers():
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

    converted_df_all = np.concatenate((converted_df_c.geometry, converted_df_d.geometry, converted_df_a.geometry, converted_df_f.geometry))

    return converted_df_c, converted_df_d, converted_df_a, converted_df_f, converted_df_all