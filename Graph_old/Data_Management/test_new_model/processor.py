import numpy as np
import geopandas as gpd

def createIds(df, prefix):
    names = df.Name

    i = 1
    ID = []
    for name in names:
        ID.append(prefix+str(i))
        i = i+1
    return ID

def createCentroids(df):
    geometry = df.geometry

    centroids = []
    for g in geometry:
        centroids.append(g.centroid)
    return centroids

def createAreas(df):
    geometry = df.geometry

    areas = []
    for g in geometry:
        gdf = gpd.GeoDataFrame({'geometry': [g]}, crs="EPSG:4326")
        gdf_utm = gdf.to_crs(epsg=25832)
        area_m2 = gdf_utm['geometry'].area[0]
        areas.append(round(area_m2 / 1000000, 2))
    return areas

def process_layers(cities, districts, administrativeDistricts, federalStates, all_geometries):
    ids_c = createIds(cities, "C")
    ids_d = createIds(districts, "D")
    ids_a = createIds(administrativeDistricts, "A")
    ids_f = createIds(federalStates, "F")
    ids_all = np.concatenate((ids_c, ids_d, ids_a, ids_f))

    centroids_c = createCentroids(cities)
    centroids_d = createCentroids(districts)   
    centroids_a = createCentroids(administrativeDistricts)
    centroids_f = createCentroids(federalStates)

    areas_c = createAreas(cities)
    areas_d = createAreas(districts)
    areas_a = createAreas(administrativeDistricts)
    areas_f = createAreas(federalStates)

    cities = {"ID":ids_c, "Name": cities.Name, "NameD": cities["NameD"], "Centroid": centroids_c, "Area": areas_c, "Geometry": cities.geometry}
    districts = {"ID":ids_d, "Name": districts.Name, "NameAD": districts["NameAD"], "Centroid": centroids_d, "Area": areas_d, "Geometry": districts.geometry}
    administrativeDistricts = {"ID":ids_a, "Name": administrativeDistricts.Name, "NameFS": administrativeDistricts["NameFS"], "Centroid": centroids_a, "Area": areas_a, "Geometry": administrativeDistricts.geometry}
    federalStates = {"ID":ids_f, "Name": federalStates.Name, "Centroid": centroids_f, "Area": areas_f, "Geometry": federalStates.geometry}
    geometries={"ID":ids_all,"Geometry": all_geometries}
    geometryTypes = {"ID": ids_all}
    hasFootprint = {"Start_Point": ids_all, "End_Point": ids_all}

    return cities, districts, administrativeDistricts, federalStates, geometries, geometryTypes, hasFootprint

def process_within(cities, districts, administrativeDistricts, federalStates):
    # Within relation
    c_names = cities["Name"]
    c_d = cities["NameD"]

    d_names = districts["Name"]
    d_ad = districts["NameAD"]

    ad_name = administrativeDistricts["Name"]
    ad_f = administrativeDistricts["NameFS"]

    fs_name = federalStates["Name"]

    c_lies_in = []
    d_lies_in = []
    within = {"Start_Point": c_lies_in, "End_Point": d_lies_in}

    j=0
    for city_id in cities["ID"]:   
        i=0
        for district in d_names:    
            if c_d[j] == district:
                # print(city_id)
                # print(c_d[j])
                # print(d_names[i])
                within["Start_Point"].append(city_id)
                within["End_Point"].append(districts["ID"][i])
            i = i +1   
        j= j+1

    j=0
    for district_id in districts["ID"]:   
        i=0
        for ad_Dis in ad_name:    
            if d_ad[j] == ad_Dis:
                # print(city_id)
                # print(c_d[j])
                # print(d_names[i])
                within["Start_Point"].append(district_id)
                within["End_Point"].append(administrativeDistricts["ID"][i])
            i = i +1   
        j= j+1 


    j=0
    for adistrict in administrativeDistricts["ID"]:   
        i=0
        for federalState in fs_name:    
            if ad_f[j] == federalState:
                # print(city_id)
                # print(c_d[j])
                # print(d_names[i])
                within["Start_Point"].append(adistrict)
                within["End_Point"].append(federalStates["ID"][i])
            i = i +1   
        j= j+1 

    return within