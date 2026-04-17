from loader import load_layers
from processor import process_layers, process_within, process_touches, process_relates
from writer import write_layers, write_within, write_touches, write_touches, write_relates

def main(generate=["all"]):
    cities, districts, administrativeDistricts, federalStates, all_geometries = load_layers()
    cities, districts, administrativeDistricts, federalStates, geometries, geometryTypes, hasFootprint = process_layers(cities, districts, administrativeDistricts, federalStates, all_geometries)

    if "all" in generate or "layers" in generate:
        write_layers(cities, districts, administrativeDistricts, federalStates, geometries, geometryTypes, hasFootprint)
    if "all" in generate or "within" in generate:
        within = process_within(cities, districts, administrativeDistricts, federalStates)
        write_within(within)
    if "all" in generate or "touches" in generate:
        touches = process_touches(cities, districts, administrativeDistricts, federalStates)
        write_touches(touches)
    if "relates" in generate:
        relates = process_relates(cities, districts, administrativeDistricts)
        write_relates(relates)

if __name__ == "__main__":
    main(generate=["relates"])

