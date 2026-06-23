import geopandas as gpd
import numpy as np

# Loads the layers 
def load_layers():
    # Import .shp file into a GeoPandas DataFrame
    geopandas_c = gpd.read_file('Graph\Data Management\Geometries\Shapes\Gemeinde.shp')
    geopandas_v = gpd.read_file('Graph\Data Management\Geometries\Shapes\Verwaltungsgemeinde.shp')
    geopandas_d = gpd.read_file('Graph\Data Management\Geometries\Shapes\Kreis.shp')
    geopandas_a = gpd.read_file('Graph\Data Management\Geometries\Shapes\Regierungsbezirk.shp')
    geopandas_f = gpd.read_file('Graph\Data Management\Geometries\Shapes\Land.shp')

    # geopandas_c = geopandas_c.set_crs("EPSG:31467")
    # geopandas_v = geopandas_v.set_crs("EPSG:31467")
    # geopandas_d = geopandas_d.set_crs("EPSG:31467")
    # geopandas_a = geopandas_a.set_crs("EPSG:31467")
    # geopandas_f = geopandas_f.set_crs("EPSG:31467")

    # Convert geospatial data to latitude/longitude coordinate system
    # converted_df_c = geopandas_c.to_crs('EPSG:4326')
    # converted_df_v = geopandas_v.to_crs('EPSG:4326')
    # converted_df_d = geopandas_d.to_crs('EPSG:4326')
    # converted_df_a = geopandas_a.to_crs('EPSG:4326')
    # converted_df_f = geopandas_f.to_crs('EPSG:4326')

    # filter nrw and niedersachsen out of the federal states layer
    #geopandas_f = geopandas_f[geopandas_f['Name'].isin(['Schleswig-Holstein', 'Hamburg', 'Nordrhein-Westfalen', 'Niedersachsen', 'Bremen', 'Hessen', 'Rheinland-Pfalz'])]
    # clip all the other layers to the extent of the federal states layer
    #geopandas_v = geopandas_v[geopandas_v['SN_L'].isin(["01", "02", "03", "04", "05", "06", "07"])]
    #geopandas_c = geopandas_c[geopandas_c['SN_L'].isin(["01", "02", "03", "04", "05", "06", "07"])]
    #geopandas_d = geopandas_d[geopandas_d['SN_L'].isin(["01", "02", "03", "04", "05", "06", "07"])]
    #geopandas_a = geopandas_a[geopandas_a['SN_L'].isin(["01", "02", "03", "04", "05", "06", "07"])]

    # Concatenate all dataframes together
    converted_df_all = np.concatenate((geopandas_c.geometry, geopandas_v.geometry, geopandas_d.geometry, geopandas_a.geometry, geopandas_f.geometry))

    return geopandas_c, geopandas_v, geopandas_d, geopandas_a, geopandas_f, converted_df_all