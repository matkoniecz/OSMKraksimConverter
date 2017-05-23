import sys
from converter_printer import ConverterPrinter
from query_loader import ConverterQueryLoader
from converter_reader import *
from converter_normalizer import ConverterNormalizer
from query_loader import Query

def download_data(latitudeSouth, longitudeWest, latitudeNorth, longitudeEast):
    query = Query(latitudeSouth, longitudeWest, latitudeNorth, longitudeEast)
    cql = ConverterQueryLoader()
    print str(query)
    result = cql.execute_query(str(query))
    print result
    print "Kwerenda wykonana"
    return result, query

def get_data(latitudeSouth, longitudeWest, latitudeNorth, longitudeEast):
    result, query = download_data(latitudeSouth, longitudeWest, latitudeNorth, longitudeEast)
    result = ConverterNormalizer.simplify_loaded_data(result)
    return result, query

def is_normalization_failed(result):
    try:
        ConverterNormalizer.validate_returned_data(result)
    except ConverterNormalizer.ConversionFailed, error:
        return True
    return False

def generate_minimal_test_case_if_errors_are_present(latitudeSouth, longitudeWest, latitudeNorth, longitudeEast):
    result, _ = get_data(latitudeSouth, longitudeWest, latitudeNorth, longitudeEast)
    latitudeSouth = float(latitudeSouth)
    longitudeWest = float(longitudeWest)
    latitudeNorth = float(latitudeNorth)
    longitudeEast = float(longitudeEast)
    if is_normalization_failed(result):
        binary_search_for_problems(latitudeSouth, longitudeWest, latitudeNorth, longitudeEast)

def binary_search_for_problems(latitudeSouth, longitudeWest, latitudeNorth, longitudeEast):
    latitudeMiddle = (latitudeSouth + latitudeNorth) / 2
    longitudeMiddle = (longitudeWest + longitudeEast) / 2

    # bottom-left quadrant
    result, _ = get_data(latitudeSouth, longitudeWest, latitudeMiddle, longitudeMiddle)
    if is_normalization_failed(result):
        return binary_search_for_problems(latitudeSouth, longitudeWest, latitudeMiddle, longitudeMiddle)

    # upper-left quadrant
    result, _ = get_data(latitudeMiddle, longitudeWest, latitudeNorth, longitudeMiddle)
    if is_normalization_failed(result):
        return binary_search_for_problems(latitudeMiddle, longitudeWest, latitudeNorth, longitudeMiddle)

    # bottom-right quadrant
    result, _ = get_data(latitudeSouth, longitudeMiddle, latitudeMiddle, longitudeEast)
    if is_normalization_failed(result):
        return binary_search_for_problems(latitudeSouth, longitudeMiddle, latitudeMiddle, longitudeEast)

    # upper-right quadrant
    result, _ = get_data(latitudeMiddle, longitudeMiddle, latitudeNorth, longitudeEast)
    if is_normalization_failed(result):
        return binary_search_for_problems(latitudeMiddle, longitudeMiddle, latitudeNorth, longitudeEast)

    coords = str(latitudeSouth) + ' ' + str(longitudeWest) + ' ' + str(latitudeNorth) + ' ' + str(longitudeEast)
    print 'following areas is smallest found by binary search: ' + coords
    print str(Query(latitudeSouth, longitudeWest, latitudeNorth, longitudeEast))

if __name__ == "__main__":
    latitudeSouth, longitudeWest, latitudeNorth, longitudeEast = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    result, query = get_data(latitudeSouth, longitudeWest, latitudeNorth, longitudeEast)
    converter_reader = ConverterReader(query)
    converter_reader.read_to_internal_structure(result)
    ConverterPrinter.print_to_file(sys.argv[5], converter_reader.gateways, converter_reader.junctions,
                                   converter_reader.ways)
    generate_minimal_test_case_if_errors_are_present(latitudeSouth, longitudeWest, latitudeNorth, longitudeEast)

    # for way in result.ways:
    #     print("Name: %s" % way.tags.get("name", "n/a"))
    #     print("  Highway: %s" % way.tags.get("highway", "n/a"))
    #     print("  Nodes:")
    #     for node in way.nodes:
    #         print("    Lat: %f, Lon: %f" % (node.lat, node.lon))
