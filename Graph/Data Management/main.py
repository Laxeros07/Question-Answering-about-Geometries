import geopandas as gpd

# Import .shp file into a GeoPandas DataFrame
geopandas_state = gpd.read_file('Graph\Data Management\Geometries\Shapes\VG5000_STA.shp')

# Convert geospatial data to latitude/longitude coordinate system
converted_df = geopandas_state.to_crs('EPSG:4326')

# Write data to CSV
# converted_df.to_csv('Graph\Data_Management\states.csv', index=False)