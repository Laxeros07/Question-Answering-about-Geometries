from loader import load_layers
from processor import process_layers, process_within, process_touches, process_relates
from writer import write_layers, write_within, write_touches, write_touches, write_relates

# Calls all scripts to generate the csv files for the new model. 
# You can specify which csv files you want to generate by passing a list of the following strings to the main function: 
# "all", "layers", "within", "touches", "relates". 
# If you want to generate all csv files, simply pass ["all"] or leave the argument empty.
def main(generate=["all"]):
    # Load the layers which are needed in all processes
    cities, districts, administrativeDistricts, federalStates, all_geometries = load_layers()
    cities, districts, administrativeDistricts, federalStates, geometries, geometryTypes, hasFootprint = process_layers(cities, districts, administrativeDistricts, federalStates, all_geometries)

    if "all" in generate or "layers" in generate:
        write_layers(cities, districts, administrativeDistricts, federalStates, geometries, geometryTypes, hasFootprint)
    if "all" in generate or "within" in generate:
        within = process_within(cities, districts, administrativeDistricts, federalStates)
        write_within(within)
    if "all" in generate or "touches" in generate:
        touches = process_touches(cities, districts, administrativeDistricts)
        write_touches(touches)
    if "relates" in generate:
        # Takes really long to process, so only generate if specified
        relates = process_relates(cities, districts, administrativeDistricts)
        write_relates(relates)

if __name__ == "__main__":
    main(generate=["layers"])

