import overpy
import time


class ConverterReader:
    'class containing methods for converting OSM data to inner data structures'
    gateways = set()
    junctions = set()

    def __init__(self):
        pass

    def readToInternalStructure(self, result):
        nodes = []
        nodes_set = set()
        for way in result.ways:
            for node in way.get_nodes(resolve_missing=True):
                time.sleep(
                    0.1)  # overpy.exception.OverpassTooManyRequests, zeby to wyrzucic trzeba zaimplementowac wlasne "resolve_missing"(lapac ten wyjatek i powtarzac kwerende)
                nodes.append(node)
                nodes_set.add(node)

        for node in nodes_set:
            nodes.remove(node)

        nodes_set = set()
        # for node in nodes:
        #     if node in nodes_set:
        #         junction = None
        #     else:
        #         c = Junction()


