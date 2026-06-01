import numpy as np
import geopandas as gpd
import pandas as pd
import math
import csv
from shapely.geometry import LineString, MultiPoint, MultiPolygon, Polygon, shape
from pathlib import Path
import json

# calculates distances and spatial relations on the fly

# get geometries
# input: a list of ids
# output: a pandas GeoDataFrame of the ids and geometries
def get_geometries(ids):

    # loading dataframe
    csv_path = Path("App_new/backend/data/geometries.csv")
    df = pd.read_csv(csv_path)

    geometries = []
    id_list = []

    for id in ids:
        row = df[df["ID"] == id]

        geometry_str = row.iloc[0]["Geometry"]

        # JSON -> dict -> shapely geometry
        geometry = shape(json.loads(geometry_str))

        geometries.append(geometry)
        id_list.append(id)

    # build GeoDataFrame
    gdf = gpd.GeoDataFrame(
        {"ID": id_list},
        geometry=geometries,
        crs="EPSG:4326"
    )

    return gdf



# calculate_distance
# Calculates the distance between the borders of the geometries
# input: the result of the query ([{'result': {'start': {'name': 'Selm', 'id': 'C238'}, 'target': [{'name': 'Bocholt', 'id': 'C101'}]}}]))
# output: the input with the new attribute "distance"
def calculate_distances(neo_result):

    # filtering ids
    ids = []
    for item in neo_result:

        ids.append(item["start"]["id"])
        # if there are several targets (not the case yet)
        ids.extend(
            target["id"]
            for target in item["target"]
        )

    polygons = get_geometries(ids)
    polygons = polygons.to_crs(epsg=25832)
    # only works for two entities
    distance = polygons.loc[0]["geometry"].distance(polygons.loc[1]["geometry"])

    neo_result[0]["distance"] = distance
    return neo_result

# calculate_radius

# Calculate the realtive postion of two points
# Source: https://mapscaping.com/how-to-calculate-bearing-between-two-coordinates/
# input: two points (lat, long)
# output: the cardinal direction of the second point in relation to the first point
def get_cardinal_direction(pointA, pointB):
    import math
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

# calculate_cardinal_direction
def calculate_cardinal_direction(neo_result, direction):

    # get type from the id
    start_type = neo_result[0]["start"]["id"][0]
    # geojson -> gdf
    start_gdf = get_geometries([neo_result[0]["start"]["id"]])
    start_gdf = start_gdf.to_crs(epsg=25832)
    start_centroid = start_gdf.geometry.centroid.iloc[0]

    # get all entites of start_type from the geometries.csv
    csv_path = Path("App_new\\backend\data\geometries.csv")

    df = pd.read_csv(csv_path)
    df = df[df["ID"].str.startswith(start_type)]

    for index, row in df.iterrows():
        geometry_str = row["Geometry"]
        geometry = shape(json.loads(geometry_str))
        geometry = geometry.to_crs(epsg=25832)
        centroid = geometry.centroid

        cardinal_direction = get_cardinal_direction((start_centroid.x, start_centroid.y), (centroid.x, centroid.y))

        neo_result[0]["target"] = []
        if cardinal_direction == direction:
            neo_result[0]["target"].append({"name": row["Name"], "id": row["ID"]})
# Überlegen: entweder csv so erweitern, dass dort auch die namen gespeichert werden
# das führt dazu, dass evtl der alte code dahingehend nochmal geändert werden muss, dass man jetzt doch die Städtenamen hat
# oder hier nochmal eine cypher query machen, um die namen zu bekommen


    
    return neo_result