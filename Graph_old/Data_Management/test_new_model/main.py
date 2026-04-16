from loader import load_layers
from processor import process_layers, process_within
from writer import write_layers, write_within, write_touches

def main(generate=["all"]):
    cities, districts, administrativeDistricts, federalStates, all_geometries = load_layers()
    cities, districts, administrativeDistricts, federalStates, geometries, geometryTypes = process_layers(cities, districts, administrativeDistricts, federalStates, all_geometries)

    if "all" in generate or "layers" in generate:
        write_layers(cities, districts, administrativeDistricts, federalStates, geometries, geometryTypes)
    if "all" in generate or "within" in generate:
        within = process_within(cities, districts, administrativeDistricts, federalStates)
        write_within(within)

if __name__ == "__main__":
    main()

