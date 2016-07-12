import sys
import time
from query_loader import ConverterQueryLoader
from query_loader import Query

if __name__ == "__main__":
    query = Query(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    print str(query)
    cql = ConverterQueryLoader()
    result = cql.execute_query(str(query))
    # print result.ways
    for way in result.ways:
        print("Name: %s" % way.tags.get("name", "n/a"))
        print("  Highway: %s" % way.tags.get("highway", "n/a"))
        print("  Nodes:")
        for node in way.get_nodes(resolve_missing=True):
            time.sleep(0.1)
            print("    Lat: %f, Lon: %f" % (node.lat, node.lon))
