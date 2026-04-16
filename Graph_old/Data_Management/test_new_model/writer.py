import pandas as pd
import csv

def write_layers(cities, districts, administrativeDistricts, federalStates, geometries, geometryTypes):
    df_cities = pd.DataFrame(cities) 
    df_cities = df_cities.drop(columns=["NameD"])
    df_cities = df_cities.drop(columns=["Geometry"])
    df_cities.to_csv('Graph_old\Data_Management\\test_new_model\\cities.csv', index=False, sep = ",") 

    df_districts = pd.DataFrame(districts)
    df_districts = df_districts.drop(columns=["NameAD"])
    df_districts = df_districts.drop(columns=["Geometry"])
    df_districts.to_csv('Graph_old\Data_Management\\test_new_model\\districts.csv', index=False, sep = ",") 

    df_administrativeDistricts = pd.DataFrame(administrativeDistricts)
    df_administrativeDistricts = df_administrativeDistricts.drop(columns=["NameFS"])
    df_administrativeDistricts = df_administrativeDistricts.drop(columns=["Geometry"])
    df_administrativeDistricts.to_csv('Graph_old\Data_Management\\test_new_model\\administrativeDistricts.csv', index=False, sep = ",") 

    df_federalStates = pd.DataFrame(federalStates)
    df_federalStates = df_federalStates.drop(columns=["Geometry"])
    df_federalStates.to_csv('Graph_old\Data_Management\\test_new_model\\federalStates.csv', index=False, sep = ",")

    df_geometries = pd.DataFrame(geometries)
    df_geometries.to_csv('Graph_old\Data_Management\\test_new_model\\geometries.csv')

    df_geometries = pd.DataFrame(geometryTypes)
    df_geometries.to_csv('Graph_old\Data_Management\\test_new_model\\geometryTypes.csv')

def write_within(within):
    df_lies_in = pd.DataFrame(within) 
    df_lies_in.to_csv('Graph_old\Data_Management\\test_new_model\\within.csv', index=False, sep = ",")

def write_touches(cities, districts, administrativeDistricts):
    #Save the result_array as csv
    with open('Graph/touches.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["StartID", "EndID", "Rel_Position"])
        writer.writerows(cities)
        writer.writerows(districts)
        writer.writerows(administrativeDistricts)