# coding=UTF8
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

def generate_minimal_test_case_if_errors_are_present(result, latitudeSouth, longitudeWest, latitudeNorth, longitudeEast):
    if result == None:
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
    latitude_delta = latitudeNorth - latitudeSouth
    longitude_delta = longitudeEast - longitudeWest

    print "Δlatitude = " + str(latitude_delta)
    print "Δlongitude = " + str(longitude_delta)

    epsilon = 1.0/10/1000

    # bottom-left quadrant
    result, _ = get_data(latitudeSouth, longitudeWest, latitudeMiddle, longitudeMiddle)
    if latitude_delta > epsilon and is_normalization_failed(result):
        return binary_search_for_problems(latitudeSouth, longitudeWest, latitudeMiddle, longitudeMiddle)

    # upper-left quadrant
    result, _ = get_data(latitudeMiddle, longitudeWest, latitudeNorth, longitudeMiddle)
    if longitude_delta > epsilon and is_normalization_failed(result):
        return binary_search_for_problems(latitudeMiddle, longitudeWest, latitudeNorth, longitudeMiddle)

    # bottom-right quadrant
    result, _ = get_data(latitudeSouth, longitudeMiddle, latitudeMiddle, longitudeEast)
    if latitude_delta > epsilon and is_normalization_failed(result):
        return binary_search_for_problems(latitudeSouth, longitudeMiddle, latitudeMiddle, longitudeEast)

    # upper-right quadrant
    result, _ = get_data(latitudeMiddle, longitudeMiddle, latitudeNorth, longitudeEast)
    if longitude_delta > epsilon and is_normalization_failed(result):
        return binary_search_for_problems(latitudeMiddle, longitudeMiddle, latitudeNorth, longitudeEast)

    anonunce_completion_of_binary_search(latitudeSouth, longitudeWest, latitudeNorth, longitudeEast)

def anonunce_completion_of_binary_search(latitudeSouth, longitudeWest, latitudeNorth, longitudeEast):
    coords = str(latitudeSouth) + ' ' + str(longitudeWest) + ' ' + str(latitudeNorth) + ' ' + str(longitudeEast)
    print 'following areas is smallest found by binary search: ' + coords
    result, query = download_data(latitudeSouth, longitudeWest, latitudeNorth, longitudeEast)
    print str(query)
    ways, _ = ConverterNormalizer.build_ways_from_query_data(result, 1)

    nodes = []
    print '    def test_name(self):'
    print '        result = Result(elements=[], api=None)'
    for way_id, node_list in ways.items():
        nodes_in_way = '['
        for node_id in node_list:
            nodes_in_way += str(node_id) + ', '
            if node_id not in nodes:
                nodes.append(node_id)
                print '        node = Node(node_id=' + str(node_id) + ', lat=1, lon=1, attributes={},result=result)'
                print '        result.append(node)'
        nodes_in_way += ']'
        print '        way = Way(way_id=' + str(way_id) + ',center_lat=1,center_lon=1,node_ids='+nodes_in_way+',attributes={},result=result)'
        print '        result.append(way)'
    print '        ConverterNormalizer.validate_returned_data(ConverterNormalizer.simplify_loaded_data(result))'


if __name__ == "__main__":
    latitudeSouth, longitudeWest, latitudeNorth, longitudeEast = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    result, query = get_data(latitudeSouth, longitudeWest, latitudeNorth, longitudeEast)
    if result != None:
        converter_reader = ConverterReader(query)
        converter_reader.read_to_internal_structure(result)
        ConverterPrinter.print_to_file(sys.argv[5], converter_reader.gateways, converter_reader.junctions,
                                       converter_reader.ways)
    generate_minimal_test_case_if_errors_are_present(result, latitudeSouth, longitudeWest, latitudeNorth, longitudeEast)

    # for way in result.ways:
    #     print("Name: %s" % way.tags.get("name", "n/a"))
    #     print("  Highway: %s" % way.tags.get("highway", "n/a"))
    #     print("  Nodes:")
    #     for node in way.nodes:
    #         print("    Lat: %f, Lon: %f" % (node.lat, node.lon))
