import overpy
import time
import math
from model.junction import Junction
from model.way import Way
from model.gateway import Gateway
from model.node import Node


class ConverterReader:
    """"
    class containing methods for converting OSM data to inner data structures
    """
    query = None
    gateways = set()
    junctions = set()

    def __init__(self, query):
        self.query = query

    def read_to_internal_structure(self, result):
        nodes = []
        nodes_set = set()
        ways_to_nodes = dict()

        loop_number = len(result.ways)
        i = 0
        for way in result.ways:
            for node in way.get_nodes(resolve_missing=True):
                time.sleep(
                    0.5)  # overpy.exception.OverpassTooManyRequests, zeby to wyrzucic trzeba zaimplementowac wlasne "resolve_missing"(lapac ten wyjatek i powtarzac kwerende)
                nodes.append(node)
                nodes_set.add(node)
                if way in ways_to_nodes:
                    ways_to_nodes[way].add(node)
                else:
                    ways_to_nodes[way] = {node}
            i += 1
            print i, "/", loop_number

        for node in nodes_set:
            nodes.remove(node)

        nodes = set(nodes)
        for way in result.ways:
            for node in ways_to_nodes[way]:
                if node in nodes:
                    x_start = int(round(self.measure(float(self.query.latitudeSouth), float(self.query.longitudeWest),
                                           float(self.query.latitudeSouth), float(way.nodes[0].lon))))
                    y_start = int(round(self.measure(float(self.query.latitudeSouth), float(self.query.longitudeWest),
                                           float(way.nodes[0].lat), float(self.query.longitudeWest))))
                    starting_point = Node(way.nodes[0].id, x_start, y_start)

                    x_end = int(round(self.measure(float(self.query.latitudeSouth), float(self.query.longitudeWest),
                                         float(self.query.latitudeSouth), float(way.nodes[-1].lon))))
                    y_end = int(round(self.measure(float(self.query.latitudeSouth), float(self.query.longitudeWest),
                                         float(way.nodes[-1].lat), float(self.query.longitudeWest))))
                    ending_point = Node(way.nodes[-1].id, x_end, y_end)
                    w = Way(way.id,
                            way.tags.get("name", "n/a"),
                            starting_point,
                            ending_point,
                            way.tags.get("lanes", "n/a"),
                            way.tags.get("highway", "n/a"))
                    if node.id in [x.id for x in self.junctions]:
                        for junction in self.junctions:
                            if junction.id == node.id:
                                junction.arms[w] = None

                    else:
                        x_junction = int(round(self.measure(float(self.query.latitudeSouth), float(self.query.longitudeWest),
                                               float(self.query.latitudeSouth), float(node.lon))))
                        y_junction = int(round(self.measure(float(self.query.latitudeSouth), float(self.query.longitudeWest),
                                                  float(node.lat), float(self.query.longitudeWest))))
                        junction = Junction(dict(),node.id, x_junction, y_junction)
                        junction.arms[w] = None
                        self.junctions.add(junction)

        # testowe wypisywanie
        # print self.junctions
        for junction in self.junctions:
            print "ID:", junction.id, 'x:', junction.x, 'y:', junction.y,
            for key in junction.arms.keys():
                print key.street_name, " ",
            print

        for way in result.ways:
            n_first = way.nodes[0]
            n_last = way.nodes[-1]
            if n_first.id not in [x.id for x in self.junctions]:
                x_gateway = int(round(self.measure(float(self.query.latitudeSouth), float(self.query.longitudeWest),
                                       float(self.query.latitudeSouth), float(n_first.lon))))
                y_gateway = int(round(self.measure(float(self.query.latitudeSouth), float(self.query.longitudeWest),
                                   float(n_first.lat), float(self.query.longitudeWest))))
                gateway = Gateway(n_first.id, x_gateway, y_gateway)
                self.gateways.add(gateway)
                print 'ID:', gateway.id, 'x:', gateway.x, 'y:', gateway.y
            if n_last.id not in [x.id for x in self.junctions]:
                x_gateway = int(round(self.measure(float(self.query.latitudeSouth), float(self.query.longitudeWest),
                                         float(self.query.latitudeSouth), float(n_last.lon))))
                y_gateway = int(round(self.measure(float(self.query.latitudeSouth), float(self.query.longitudeWest),
                                     float(n_last.lat), float(self.query.longitudeWest))))
                gateway = Gateway(n_last.id, x_gateway, y_gateway)
                self.gateways.add(gateway)
                print 'ID:', gateway.id, 'x:', gateway.x, 'y:', gateway.y

    def measure(self, lat1, lon1, lat2, lon2):  # generally used geo measurement function
        R = 6378.137
        dLat = (lat2 - lat1) * math.pi / 180
        dLon = (lon2 - lon1) * math.pi / 180
        a = math.sin(dLat / 2) * math.sin(dLat / 2) + math.cos(lat1 * math.pi / 180) * math.cos(
            lat2 * math.pi / 180) * math.sin(dLon / 2) * math.sin(dLon / 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        d = R * c
        return d * 1000 / 7.5



