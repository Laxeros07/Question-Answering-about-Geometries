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

# calculate_cardinal_direction