import pandas as pd
import csv

# Writes the files

def write_layers(cities, administrativeCommunities, districts, administrativeDistricts, federalStates, geometries, geometryTypes, hasFootprint):
    cities = cities.drop(columns=["Parent"])
    cities = cities.drop(columns=["Geometry"])
    cities.to_csv('Graph\cities.csv', index=False, sep = ",")

    administrativeCommunities = administrativeCommunities.drop(columns=["Parent"])
    administrativeCommunities = administrativeCommunities.drop(columns=["Geometry"])
    administrativeCommunities.to_csv('Graph\\administrativeCommunities.csv', index=False, sep = ",") 

    districts = districts.drop(columns=["Parent"])
    districts = districts.drop(columns=["Geometry"])
    districts.to_csv('Graph\districts.csv', index=False, sep = ",") 

    administrativeDistricts = administrativeDistricts.drop(columns=["Parent"])
    administrativeDistricts = administrativeDistricts.drop(columns=["Geometry"])
    administrativeDistricts.to_csv('Graph\\administrativeDistricts.csv', index=False, sep = ",") 

    federalStates = federalStates.drop(columns=["Geometry"])
    federalStates.to_csv('Graph\\federalStates.csv', index=False, sep = ",")

    geometries.to_csv('Graph\geometries.csv', index=False)

    geometryTypes.to_csv('Graph\geometryTypes.csv', index=False)

    hasFootprint = pd.DataFrame(hasFootprint)
    hasFootprint.to_csv('Graph\hasFootprint.csv', index=False)

def write_within(within):
    within.to_csv('Graph\within.csv', index=False, sep = ",")

def write_touches(touches):
    with open('Graph\\touches.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Start_Point", "End_Point", "Rel_Position"])
        writer.writerows(touches)

def write_relates(relates):
    df = pd.DataFrame(relates)
    df.to_csv('Graph\relates.csv', index=False)