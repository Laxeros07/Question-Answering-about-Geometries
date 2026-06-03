import numpy as np
import geopandas as gpd
import pandas as pd
import math

# Processes the data

# Creates unique IDs for the layers by adding a prefix to the index of the layer.
def createIds(df, prefix):
    names = df.Name

    i = 1
    ID = []
    for _ in names:
        ID.append(prefix+str(i))
        i = i+1
    return ID

# Creates the centroids of the geometries in the layers.
def createCentroids(df):
    geometry = df.geometry

    centroids = []
    for g in geometry:
        centroids.append(g.centroid)
    return centroids

# Calculate the area of a geometry
def createAreas(df):
    geometry = df.geometry

    areas = []
    for g in geometry:
        gdf = gpd.GeoDataFrame({'geometry': [g]}, crs="EPSG:4326")
        gdf_utm = gdf.to_crs(epsg=25832)
        area_m2 = gdf_utm['geometry'].area[0]
        areas.append(round(area_m2 / 1000000, 2))
    return areas

# Main process function which calculates all needed attributes for the layers and returns them as dictionaries.
def process_layers(cities, administrativeCommunities, districts, administrativeDistricts, federalStates, all_geometries):
    # Create own IDs with a prefix
    ids_c = createIds(cities, "C")
    ids_v = createIds(administrativeCommunities, "V")
    ids_d = createIds(districts, "D")
    ids_a = createIds(administrativeDistricts, "A")
    ids_f = createIds(federalStates, "F")
    ids_all = np.concatenate((ids_c, ids_v, ids_d, ids_a, ids_f))

    # Assign the IDs to the dataframes
    cities["ID"] = ids_c
    administrativeCommunities["ID"] = ids_v
    districts["ID"] = ids_d
    administrativeDistricts["ID"] = ids_a
    federalStates["ID"] = ids_f

    # Calculate centroids
    centroids_c = createCentroids(cities)
    centroids_v = createCentroids(administrativeCommunities)
    centroids_d = createCentroids(districts)
    centroids_a = createCentroids(administrativeDistricts)
    centroids_f = createCentroids(federalStates)

    # areas_c = createAreas(cities)
    # areas_v = createAreas(administrativeCommunities)
    # areas_d = createAreas(districts)
    # areas_a = createAreas(administrativeDistricts)
    # areas_f = createAreas(federalStates)

    # Merge the layers to find out their next higher level
    cities = cities.merge(
        administrativeCommunities,
        on=["SN_V1", "SN_V2", "SN_K", "SN_R", "SN_L"],
        how="left"
    )
    cities["Parent"] = cities["ID_y"]
    # For the cities who do not have an administrative community as parent, use the next higher level: district
    cities = cities.merge(
        districts[["SN_K", "SN_R", "SN_L", "ID"]],
        on=["SN_K", "SN_R", "SN_L"],
        how="left"
    )
    cities["Parent"] = cities["ID_y"].fillna(cities["ID"])


    administrativeCommunities = administrativeCommunities.merge(
        districts,
        on=["SN_K", "SN_R", "SN_L"],
        how="left"
    )
    administrativeCommunities["Parent"] = administrativeCommunities["ID_y"]

    districts = districts.merge(
        administrativeDistricts,
        on=["SN_R", "SN_L"],
        how="left"
    )
    districts["Parent"] = districts["ID_y"]

    administrativeDistricts = administrativeDistricts.merge(
        federalStates,
        on="SN_L",
        how="left"
    )
    administrativeDistricts["Parent"] = administrativeDistricts["ID_y"]

    # For the districts who do not have an administrative district as parent, use the next higher level: federal State
    districts = districts.merge(
        federalStates[["SN_L", "ID"]],
        on="SN_L",
        how="left"
    )
    districts["Parent"] = districts["ID_y"].fillna(districts["ID"])

    # Old: Export with area
    # cities = {"ID":ids_c, "Name": cities.Name_x, "Parent": cities.Name_y, "Centroid": centroids_c, "Area": areas_c, "Geometry": cities.geometry_y}
    # administrativeCommunities = {"ID":ids_v, "Name": administrativeCommunities.Name_x, "Parent": administrativeCommunities.Name_y, "Centroid": centroids_v, "Area": areas_v, "Geometry": administrativeCommunities.geometry_y}
    # districts = {"ID":ids_d, "Name": districts.Name_x, "Parent": districts.Name_y, "Centroid": centroids_d, "Area": areas_d, "Geometry": districts.geometry_y}
    # administrativeDistricts = {"ID":ids_a, "Name": administrativeDistricts.Name_x, "Parent": administrativeDistricts.Name_y, "Centroid": centroids_a, "Area": areas_a, "Geometry": administrativeDistricts.geometry_y}
    # federalStates = {"ID":ids_f, "Name": federalStates.Name, "Centroid": centroids_f, "Area": areas_f, "Geometry": federalStates.geometry}
    
    # Export as Dataframe
    cities = pd.DataFrame({"ID":cities.ID_x, "Name": cities.Name_x, "Parent": cities.Parent, "Centroid": centroids_c, "Geometry": cities.geometry_x})
    administrativeCommunities = pd.DataFrame({"ID":administrativeCommunities.ID_x, "Name": administrativeCommunities.Name_x, "Parent": administrativeCommunities.Parent, "Centroid": centroids_v, "Geometry": administrativeCommunities.geometry_x})
    districts = pd.DataFrame({"ID":districts.ID_x, "Name": districts.Name_x, "Parent": districts.Parent, "Centroid": centroids_d, "Geometry": districts.geometry_x})
    administrativeDistricts = pd.DataFrame({"ID":administrativeDistricts.ID_x, "Name": administrativeDistricts.Name_x, "Parent": administrativeDistricts.Parent, "Centroid": centroids_a, "Geometry": administrativeDistricts.geometry_x})
    federalStates = pd.DataFrame({"ID":federalStates.ID, "Name": federalStates.Name, "Centroid": centroids_f, "Geometry": federalStates.geometry})
    geometries = pd.DataFrame({"ID":ids_all,"Geometry": all_geometries})
    geometryTypes = pd.DataFrame({"ID": ids_all})
    hasFootprint = pd.DataFrame({"Start_Point": ids_all, "End_Point": ids_all})

    return cities, administrativeCommunities, districts, administrativeDistricts, federalStates, geometries, geometryTypes, hasFootprint

# Calculates the within relation
def process_within(cities, administrativeCommunities, districts, administrativeDistricts, federalStates):
    
    # Dataframe which only contains the Start ID and the End ID
    within = within = pd.concat([
        cities[["ID", "Parent"]].rename(columns={"ID": "Start_Point", "Parent": "End_Point"}),
        administrativeCommunities[["ID", "Parent"]].rename(columns={"ID": "Start_Point", "Parent": "End_Point"}),
        districts[["ID", "Parent"]].rename(columns={"ID": "Start_Point", "Parent": "End_Point"}),
        administrativeDistricts[["ID", "Parent"]].rename(columns={"ID": "Start_Point", "Parent": "End_Point"})
    ], ignore_index=True)

    return within

# Calculate the realtive postion of two points
# Source: https://mapscaping.com/how-to-calculate-bearing-between-two-coordinates/
def calc_bearing(pointA, pointB):
    # Convert latitude and longitude to radians
    lat1 = math.radians(float(pointA.y))
    long1 = math.radians(float(pointA.x))
    if pointB is None:
        return None
    lat2 = math.radians(float(pointB.y))
    long2 = math.radians(float(pointB.x))
    
    # Calculate the bearing
    bearing = math.atan2(
        math.sin(long2 - long1) * math.cos(lat2),
        math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(long2 - long1)
    )
    
    # Convert the bearing to degrees
    bearing = math.degrees(bearing)
    
    # Make sure the bearing is positive
    bearing = (bearing + 360) % 360
    
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
    
def buildTouchesArray(polygons):
    gdf = gpd.GeoDataFrame(polygons, geometry="Geometry", crs="EPSG:4326").reset_index(drop=True)

    # Spatial join to find all the neighboring 
    pairs = gpd.sjoin(
        gdf[["ID", "Name", "Centroid", "Geometry"]],
        gdf[["ID", "Name", "Centroid", "Geometry"]],
        predicate="intersects",
        how="inner",
        lsuffix="a",
        rsuffix="b"
    )

    # remove self matches
    pairs = pairs[pairs["ID_a"] != pairs["ID_b"]]

    # calculate direction
    pairs["rel"] = pairs.apply(
        lambda r: calc_bearing(r["Centroid_a"], r["Centroid_b"]),
        axis=1
    )

    # export as arrays in an array
    result = pairs[["ID_a", "ID_b", "rel"]].values.tolist()

    return result

# Calculates the touches relation
def process_touches(cities, administrativeCommunities, districts, administrativeDistricts):

    cities_array = buildTouchesArray(cities)
    administrativeCommunities_array = buildTouchesArray(administrativeCommunities)
    districts_array = buildTouchesArray(districts)
    administrativeDistricts_array = buildTouchesArray(administrativeDistricts)

    return cities_array + administrativeCommunities_array + districts_array + administrativeDistricts_array

# Calculates the distance between the borders of the geometries
def calculate_distances(polygons):
    start_point = []
    end_point = []
    distance = []
    rel = []

    # Convert to UTM coordinate system to calculate the distance in meters
    polygons = gpd.GeoDataFrame(polygons, geometry="Geometry", crs="EPSG:4326")
    polygons = polygons.to_crs(epsg=25832)

    for i in range(len(polygons)):
        for j in range(len(polygons)):
            start_point.append(polygons.loc[i]["ID"])
            end_point.append(polygons.loc[j]["ID"])
            distance.append(polygons.loc[i]["Geometry"].distance(polygons.loc[j]["Geometry"]))
            centroidA = polygons.loc[i]["Centroid"]
            centroidB = polygons.loc[j]["Centroid"]
            # Calculate the relation between the two centroids of the polygons
            rel.append(calc_bearing(centroidA, centroidB))
    return start_point, end_point, distance, rel

# Calculates the relates relation
def process_relates(cities, administrativeCommunities, districts, administrativeDistricts):
    start_point_c, end_point_c, distance_c, rel_c = calculate_distances(cities)
    start_point_v, end_point_v, distance_v, rel_v = calculate_distances(administrativeCommunities)
    start_point_d, end_point_d, distance_d, rel_d = calculate_distances(districts)
    start_point_a, end_point_a, distance_a, rel_a = calculate_distances(administrativeDistricts)

    # initialize data of lists.
    data = {'Start_point': start_point_a + start_point_d + start_point_v + start_point_c,
            'End_point': end_point_a + end_point_d + end_point_v + end_point_c,
            'Distance_between': distance_a + distance_d + distance_v + distance_c,
            'Spatial_relation': rel_a + rel_d + rel_v + rel_c}
    
    return data