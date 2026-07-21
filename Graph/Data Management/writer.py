import pandas as pd
import csv

# Writes the files

def write_layers(cities, administrativeCommunities, districts, administrativeDistricts, federalStates, states, geometries, geometryTypes, hasFootprint):
    cities = cities.drop(columns=["Parent"])
    cities = cities.drop(columns=["Geometry"])
    cities.to_csv('App\\neo4j_data\\cities.csv', index=False, sep = ",")

    administrativeCommunities = administrativeCommunities.drop(columns=["Parent"])
    administrativeCommunities = administrativeCommunities.drop(columns=["Geometry"])
    administrativeCommunities.to_csv('App\\neo4j_data\\administrativeCommunities.csv', index=False, sep = ",") 

    districts = districts.drop(columns=["Parent"])
    districts = districts.drop(columns=["Geometry"])
    districts.to_csv('App\\neo4j_data\\districts.csv', index=False, sep = ",") 

    administrativeDistricts = administrativeDistricts.drop(columns=["Parent"])
    administrativeDistricts = administrativeDistricts.drop(columns=["Geometry"])
    administrativeDistricts.to_csv('App\\neo4j_data\\administrativeDistricts.csv', index=False, sep = ",") 

    federalStates = federalStates.drop(columns=["Parent"])
    federalStates = federalStates.drop(columns=["Geometry"])
    federalStates.to_csv('App\\neo4j_data\\federalStates.csv', index=False, sep = ",")

    states = states.drop(columns=["Geometry"])
    states.to_csv('App\\neo4j_data\\states.csv', index=False, sep = ",")

    geometries.to_csv('App\\backend\data\geometries.csv', index=False)

    geometryTypes.to_csv('App\\neo4j_data\\geometryTypes.csv', index=False)

    hasFootprint = pd.DataFrame(hasFootprint)
    hasFootprint.to_csv('App\\neo4j_data\\hasFootprint.csv', index=False)

def write_within(within):
    within.to_csv('App\\neo4j_data\\within.csv', index=False, sep = ",")

def write_touches(touches):
    with open('App\\neo4j_data\\touches.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Start_Point", "End_Point", "Rel_Position"])
        writer.writerows(touches)

def write_relates(relates):
    df = pd.DataFrame(relates)
    df.to_csv('App\\neo4j_data\\relates.csv', index=False)