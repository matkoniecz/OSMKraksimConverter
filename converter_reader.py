import overpy
import time
from model.junction import Junction
from model.way import Way
from model.gateway import Gateway


class ConverterReader:
    """"
    class containing methods for converting OSM data to inner data structures
    """
    gateways = set()
    junctions = set()

    def __init__(self):
        pass

    def read_to_internal_structure(self, result):
        nodes = []
        nodes_set = set()
        ways_to_nodes = dict()

        for way in result.ways:
            for node in way.get_nodes(resolve_missing=True):
                time.sleep(
                    1)  # overpy.exception.OverpassTooManyRequests, zeby to wyrzucic trzeba zaimplementowac wlasne "resolve_missing"(lapac ten wyjatek i powtarzac kwerende)
                nodes.append(node)
                nodes_set.add(node)
                if way in ways_to_nodes:
                    ways_to_nodes[way].add(node)
                else:
                    ways_to_nodes[way] = {node}

        for node in nodes_set:
            nodes.remove(node)

        nodes = set(nodes)
        for way in result.ways:
            for node in ways_to_nodes[way]:
                if node in nodes:
                    w = Way(way.id,
                            way.tags.get("name", "n/a"),
                            way.nodes[0],
                            way.nodes[-1],
                            way.tags.get("lanes", "n/a"),
                            way.tags.get("highway", "n/a"))
                    if node.id in [x.id for x in self.junctions]:
                        for junction in self.junctions:
                            if junction.id == node.id:
                                junction.arms[w] = None

                    else:
                        junction = Junction(dict(),node.id)
                        junction.arms[w] = None
                        self.junctions.add(junction)

        # testowe wypisywanie
        print self.junctions
        for junction in self.junctions:
            for key in junction.arms.keys():
                print key.street_name, " ",
            print

        for way in result.ways:
            n_first = way.nodes[0]
            n_last = way.nodes[-1]
            if n_first.id not in [x.id for x in self.junctions]:
                gateway = Gateway(n_first.id)
                self.gateways.add(gateway)
                print gateway.id
            if n_last.id not in [x.id for x in self.junctions]:
                gateway = Gateway(n_last.id)
                self.gateways.add(gateway)
                print gateway.id





