import sys
import time
from query_loader import ConverterQueryLoader
from converter_reader import *
from query_loader import Query

if __name__ == "__main__":
    query = Query(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    print str(query)
    cql = ConverterQueryLoader()
    result = cql.execute_query(str(query))
    converter_reader = ConverterReader()
    converter_reader.read_to_internal_structure(result)

    # for way in result.ways:
    #     print("Name: %s" % way.tags.get("name", "n/a"))
    #     print("  Highway: %s" % way.tags.get("highway", "n/a"))
    #     print("  Nodes:")
    #     for node in way.nodes:
    #         print("    Lat: %f, Lon: %f" % (node.lat, node.lon))
