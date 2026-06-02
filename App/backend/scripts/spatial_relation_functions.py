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
    csv_path = Path(__file__).parent.parent / "data" / "geometries.csv"
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
# input: ID of the start entity, 
#        name of the start entity, 
#        type of the target entity (e.g. "City"),
#        the cardinal direction
# output: a Cypher query which is executed in the agent
def calculate_cardinal_direction(start_id, start_name, target_type, direction):

    # get type from the id by reading the first letter
    start_type = start_id[0]

    # get all entites of start_type from the geometries.csv
    csv_path = Path(__file__).parent.parent / "data" / "geometries.csv"
    df = pd.read_csv(csv_path)

    # Create index of df
    df.set_index("ID", inplace=True)
    df = df.loc[df.index.str.startswith(start_type)]

    # df -> shapley geometry
    start_df = df.loc[start_id]
    start_geom = shape(json.loads(start_df["Geometry"]))

    # Get start centroid
    start_centroid = start_geom.centroid

    # GeoJSON -> shapely geometry
    df["Geometry"] = df["Geometry"].apply(
        lambda x: shape(json.loads(x))
    )

    # DataFrame -> GeoDataFrame
    gdf = gpd.GeoDataFrame(df, geometry="Geometry", crs="EPSG:4326")

    # Calculate the cardinal direction for each entity and filter only the specified ones
    ids_in_direction = []
    for _, row in gdf.iterrows():
        centroid = row["Geometry"].centroid
        # returns a string which holds the cardinal direction
        cardinal_direction = get_cardinal_direction((start_centroid.x, start_centroid.y), (centroid.x, centroid.y))

        if cardinal_direction == direction:
            # row.name is the id because we set the index to ID
            ids_in_direction.append(row.name)
    
    # No entities in the specified direction
    if not ids_in_direction:
        return "RETURN null AS result LIMIT 0"

    # Generate a Cypher query to get the names of the IDs in the specified direction
    query = f"""
        MATCH (other:{target_type})
        WHERE other.ID IN {ids_in_direction}

        WITH collect(DISTINCT {{
            id: other.ID,
            name: other.Name
        }}) AS target

        RETURN {{
            start: {{
                id: "{start_id}",
                name: "{start_name}"
            }},
            target: target
        }} AS result
        """
    
    return query