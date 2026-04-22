import pandas as pd
import csv

# Writes the files

def write_layers(cities, districts, administrativeDistricts, federalStates, geometries, geometryTypes, hasFootprint):
    df_cities = pd.DataFrame(cities) 
    df_cities = df_cities.drop(columns=["NameD"])
    df_cities = df_cities.drop(columns=["Geometry"])
    df_cities.to_csv('Graph\cities.csv', index=False, sep = ",") 

    df_districts = pd.DataFrame(districts)
    df_districts = df_districts.drop(columns=["NameAD"])
    df_districts = df_districts.drop(columns=["Geometry"])
    df_districts.to_csv('Graph\districts.csv', index=False, sep = ",") 

    df_administrativeDistricts = pd.DataFrame(administrativeDistricts)
    df_administrativeDistricts = df_administrativeDistricts.drop(columns=["NameFS"])
    df_administrativeDistricts = df_administrativeDistricts.drop(columns=["Geometry"])
    df_administrativeDistricts.to_csv('Graph\\administrativeDistricts.csv', index=False, sep = ",") 

    df_federalStates = pd.DataFrame(federalStates)
    df_federalStates = df_federalStates.drop(columns=["Geometry"])
    df_federalStates.to_csv('Graph\\federalStates.csv', index=False, sep = ",")

    df_geometries = pd.DataFrame(geometries)
    df_geometries.to_csv('Graph\geometries.csv', index=False)

    df_geometryTypes = pd.DataFrame(geometryTypes)
    df_geometryTypes.to_csv('Graph\geometryTypes.csv', index=False)

    df_hasFootprint = pd.DataFrame(hasFootprint)
    df_hasFootprint.to_csv('Graph\hasFootprint.csv', index=False)

def write_within(within):
    df_lies_in = pd.DataFrame(within) 
    df_lies_in.to_csv('Graph\within.csv', index=False, sep = ",")

def write_touches(touches):
    with open('Graph\touches.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["StartID", "EndID", "Rel_Position"])
        writer.writerows(touches)

def write_relates(relates):
    df = pd.DataFrame(relates)
    df.to_csv('Graph\relates.csv', index=False)