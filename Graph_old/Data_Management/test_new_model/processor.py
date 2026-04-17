import numpy as np
import geopandas as gpd
import pandas as pd
import math

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

def point_to_array(p):

    pointA = [p.x, p.y]  
    return pointA

# Calculate the realtive postion of two points
# Source: https://mapscaping.com/how-to-calculate-bearing-between-two-coordinates/
def calc_bearing(pointA, pointB):
    # Convert latitude and longitude to radians
    lat1 = math.radians(float(pointA[1]))
    long1 = math.radians(float(pointA[0]))
    lat2 = math.radians(float(pointB[1]))
    long2 = math.radians(float(pointB[0]))
    
    # Calculate the bearing
    bearing = math.atan2(
        math.sin(long2 - long1) * math.cos(lat2),
        math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(long2 - long1)
    )
    
    # Convert the bearing to degrees
    bearing = math.degrees(bearing)
    
    # Make sure the bearing is positive
    bearing = (bearing + 360) % 360
    
    #return bearing
    #print(bearing)
    if bearing < 22.5:
        return "northern"
    elif bearing < 67.5:
        return "northeastern"
    elif bearing < 112.5:
        return "eastern"
    elif bearing < 157.5:
        return "southeastern"
    elif bearing < 202.5:
        return "southern"
    elif bearing < 247.5:
        return "southwestern"
    elif bearing < 292.5:
        return "western"
    elif bearing < 337.5:
        return "northwestern"
    else:
        return "northern"
    
def buildArray(polygons):
    neighbors_list = []
    for idx, geom in polygons.geometry.items():
        possible_matches = polygons[polygons.geometry.intersects(geom)]
        
        neighbors = possible_matches[possible_matches.index != idx]["Name"].tolist()
        
        neighbors_list.append(",".join(neighbors))

    result_array = []
    i = 0
    for n in neighbors_list:
        name = polygons.Name[i]
        startID = None
        centroidA = None
        # Search startID for name
        j = 0
        for el in polygons.Name:
            if el == name:
                startID = polygons.loc[j]["ID"]
                centroidA = polygons.loc[j]["Centroid"]
                break
            j = j+1
        for c in n.split(","):
            endID = None
            centroidB = None
            # Search endID for name
            k = 0
            for el in polygons.Name:
                if el == c:
                    endID = polygons.loc[k]["ID"]
                    centroidB = polygons.loc[k]["Centroid"]
                    break
                k = k+1

            # Calculate the relation between the two centroids of the polygons
            rel = calc_bearing(centroidA, centroidB)
            # Append the result to the result_array
            result_array.append([startID, endID, rel])
        i = i+1

    return result_array
    
def calculate_touches(cities, districts, administrativeDistricts):

    cities_array = buildArray(cities)
    districts_array = buildArray(districts)
    administrativeDistricts_array = buildArray(administrativeDistricts)

    return cities_array + districts_array + administrativeDistricts_array

def calculate_distances(polygons):
    start_point = []
    end_point = []
    distance = []
    rel = []

    polygons = gpd.GeoDataFrame(polygons, geometry="Geometry", crs="EPSG:4326")
    polygons = polygons.to_crs(epsg=25832)

    for i in range(len(polygons)):
        for j in range(len(polygons)):
            start_point.append(polygons.loc[i]["ID"])
            end_point.append(polygons.loc[j]["ID"])
            distance.append(polygons.loc[i]["Geometry"].distance(polygons.loc[j]["Geometry"]))
            centroidA = polygons.loc[i]["Centroid"]
            centroidB = polygons.loc[j]["Centroid"]
            centroidA = point_to_array(centroidA)
            centroidB = point_to_array(centroidB)
            # Calculate the relation between the two centroids of the polygons
            rel.append(calc_bearing(centroidA, centroidB))
    return start_point, end_point, distance, rel

def process_relates(cities, districts, administrativeDistricts):
    start_point_c, end_point_c, distance_c, rel_c = calculate_distances(cities)
    start_point_d, end_point_d, distance_d, rel_d = calculate_distances(districts)
    start_point_a, end_point_a, distance_a, rel_a = calculate_distances(administrativeDistricts)

    # initialize data of lists.
    data = {'Start_point': start_point_a + start_point_d + start_point_c,
            'End_point': end_point_a + end_point_d + end_point_c,
            'Distance_between': distance_a + distance_d + distance_c,
            'Spatial_relation': rel_a + rel_d + rel_c}
    
    return data