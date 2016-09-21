# coding=utf-8
import math
from model.junction import Junction
from model.way import Way
from model.gateway import Gateway
from model.node import Node
from model.action import Action
from model.rule import Rule


def possible_arm_has_given_exit(junction, possible_arm_for_given_exit, exit):
    if junction.arms[possible_arm_for_given_exit] is not None:
        for action in junction.arms[possible_arm_for_given_exit]:
            if str(action.exit.id) == str(exit.id):
                return action
    return None


def measure(lat1, lon1, lat2, lon2):  # generally used geo measurement function
    R = 6378.137
    dLat = (lat2 - lat1) * math.pi / 180
    dLon = (lon2 - lon1) * math.pi / 180
    a = math.sin(dLat / 2) * math.sin(dLat / 2) + math.cos(lat1 * math.pi / 180) * math.cos(
        lat2 * math.pi / 180) * math.sin(dLon / 2) * math.sin(dLon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    d = R * c
    return 15*(d * 1000 / 7.5)


def sort_ways_by_priority(ways_with_given_exit, ways_priorities):
    for i in range(len(ways_with_given_exit))[1:]:
        tmp = ways_with_given_exit[i]
        j = i - 1
        while j>=0 and ways_priorities[ways_with_given_exit[j][0].priority] < ways_priorities[tmp[0].priority]:
            ways_with_given_exit[j+1] = ways_with_given_exit[j]
            j -= 1

        ways_with_given_exit[j + 1] = tmp


def delete_from_set_of_actions(way_from, exit, junction):
    """

    :param way_from: way.Way
    :param exit: way.Way
    :param junction: junction.Junction
    :return:
    """
    actions_to_delete = [action for action in junction.arms[way_from] if action.exit.id == exit.id]
    for action in actions_to_delete:
        junction.arms[way_from].remove(action)


def fill_dictionary():
    ways_priorities = dict()
    ways_priorities['residential'] = 0
    ways_priorities['unclassified'] = 0
    ways_priorities['tertiary'] = 1
    ways_priorities['secondary_link'] = 2
    ways_priorities['secondary'] = 2
    ways_priorities['primary'] = 3
    ways_priorities['primary_link'] = 3
    ways_priorities['trunk'] = 4
    ways_priorities['motorway'] = 5

    return ways_priorities


class ConverterReader:
    """"
    class containing methods for converting OSM data to inner data structures
    """
    query = None
    gateways = set()
    junctions = set()
    ways = set()
    ways_to_nodes = dict()

    def __init__(self, query):
        self.query = query

    def read_to_internal_structure(self, result):

        # wykrywanie skrzyzowan
        nodes_that_represent_junctions = self.find_junctions(result.ways)

        # tworzenie obiektow Way i Junction
        self.create_ways_and_junctions(result.ways, nodes_that_represent_junctions)

        # tworzenie obiektow Gateway
        self.create_gateways(result.ways)

        # zapewnienie dwukierunkowosci drog z lub do gateway'ow
        self.provide_bidirectional_ways_to_gateways()

        # uzupelnienie slownika z priorytetami drog
        ways_priorities = fill_dictionary()

        # tworzenie struktury obiektowej dla bloku nr 3 pliku wejściowego
        self.create_actions()         # stworzenie akcji

        # usuwanie niepotrzebnych akcji na bazie restrykcji wczytanych z relacji
        self.delete_some_actions(result.relations)

        # tworzenie obiektow Rule
        self.create_rules(ways_priorities)

        # wypisanie stworzonej struktury obiektowej
        # self.print_object_internal_structure()

    def get_junction_by_id(self, junction_id):
        for junction in self.junctions:
            if junction.id == junction_id:
                return junction

    def get_way_by_id(self, way_from_id):
        for way in self.ways:
            if way.id == way_from_id:
                return way

    def find_junctions(self, query_ways):
        nodes_that_represent_junctions = []
        nodes_set = set()

        for way in query_ways:
            all_nodes_of_way = way.get_nodes(resolve_missing=False)
            for node in all_nodes_of_way[0], all_nodes_of_way[-1]:
                nodes_that_represent_junctions.append(node)
                nodes_set.add(node)
                self.correct_border_coordinates(node)
                if way in self.ways_to_nodes:
                    self.ways_to_nodes[way].append(node)
                else:
                    self.ways_to_nodes[way] = [node]

        for node in nodes_set:
            nodes_that_represent_junctions.remove(node)

        return set(nodes_that_represent_junctions)

    def create_ways_and_junctions(self, query_ways, nodes_that_represent_junctions):
        for way in query_ways:
            x_start = int(round(measure(float(self.query.latitudeNorth), float(self.query.longitudeWest),
                                        float(self.query.latitudeNorth), float(way.nodes[0].lon))))
            y_start = int(round(measure(float(self.query.latitudeNorth), float(self.query.longitudeWest),
                                        float(way.nodes[0].lat), float(self.query.longitudeWest))))
            starting_point = Node(way.nodes[0].id, x_start, y_start)

            x_end = int(round(measure(float(self.query.latitudeNorth), float(self.query.longitudeWest),
                                      float(self.query.latitudeNorth), float(way.nodes[-1].lon))))
            y_end = int(round(measure(float(self.query.latitudeNorth), float(self.query.longitudeWest),
                                      float(way.nodes[-1].lat), float(self.query.longitudeWest))))
            ending_point = Node(way.nodes[-1].id, x_end, y_end)
            w = Way(way.id,
                    way.tags.get("name", "n/a"),
                    starting_point,
                    ending_point,
                    way.tags.get("lanes", "1"),
                    way.tags.get("highway", "n/a"))
            if way.tags.get("oneway", "n/a") == "yes":
                w.oneway = True
            self.ways.add(w)
            for node in self.ways_to_nodes[way][0], self.ways_to_nodes[way][-1]:
                if node in nodes_that_represent_junctions:
                    if node.id in [x.id for x in self.junctions]:
                        for junction in self.junctions:
                            if junction.id == node.id:
                                junction.arms[w] = None

                    else:
                        x_junction = int(round(measure(float(self.query.latitudeNorth), float(self.query.longitudeWest),
                                                       float(self.query.latitudeNorth), float(node.lon))))
                        y_junction = int(round(measure(float(self.query.latitudeNorth), float(self.query.longitudeWest),
                                                       float(node.lat), float(self.query.longitudeWest))))
                        junction = Junction(dict(), node.id, x_junction, y_junction)
                        junction.arms[w] = None
                        self.junctions.add(junction)

    def create_gateways(self, query_ways):
        for way in query_ways:
            n_first = way.nodes[0]
            n_last = way.nodes[-1]
            if n_first.id not in [x.id for x in self.junctions] and n_first.id not in [gateway.id for gateway in
                                                                                       self.gateways]:
                x_gateway = int(round(measure(float(self.query.latitudeNorth), float(self.query.longitudeWest),
                                              float(self.query.latitudeNorth), float(n_first.lon))))
                y_gateway = int(round(measure(float(self.query.latitudeNorth), float(self.query.longitudeWest),
                                              float(n_first.lat), float(self.query.longitudeWest))))
                gateway = Gateway(n_first.id, x_gateway, y_gateway)
                self.gateways.add(gateway)

            if n_last.id not in [x.id for x in self.junctions] and n_last.id not in [gateway.id for gateway in
                                                                                     self.gateways]:
                x_gateway = int(round(measure(float(self.query.latitudeNorth), float(self.query.longitudeWest),
                                              float(self.query.latitudeNorth), float(n_last.lon))))
                y_gateway = int(round(measure(float(self.query.latitudeNorth), float(self.query.longitudeWest),
                                              float(n_last.lat), float(self.query.longitudeWest))))
                gateway = Gateway(n_last.id, x_gateway, y_gateway)
                self.gateways.add(gateway)

    def provide_bidirectional_ways_to_gateways(self):
        gateway_ids = [gateway.id for gateway in self.gateways]
        for way in self.ways:
            if way.starting_point.id in gateway_ids or way.ending_point.id in gateway_ids:
                way.oneway = False

    def create_actions(self):
        for junction in self.junctions:
            for way in junction.arms.keys():
                if way.oneway and str(way.starting_point.id) == str(junction.id):
                    continue
                actions = []
                for possible_exit_for_given_way in junction.arms.keys():
                    if (possible_exit_for_given_way.oneway and str(
                            possible_exit_for_given_way.starting_point.id) != str(junction.id)) \
                            or str(possible_exit_for_given_way.id) == str(way.id):
                        continue
                    action = Action(0, possible_exit_for_given_way, set())
                    actions.append(action)
                junction.arms[way] = set(actions)

                if way.oneway:
                    delete_from_set_of_actions(way, way, junction)

    def delete_some_actions(self, query_relations):
        for relation in query_relations:
            flag_to = False
            flag_via = False
            flag_from = False
            for relation_member in relation.members:
                if relation_member.role == "to":
                    flag_to = True
                    exit_id = relation_member.ref
                if relation_member.role == 'via':
                    flag_via = True
                    junction_id = relation_member.ref
                if relation_member.role == "from":
                    flag_from = True
                    way_from_id = relation_member.ref
            if flag_to and flag_via and flag_from:
                restriction = relation.tags.get("restriction", "n/a")
                junction = self.get_junction_by_id(junction_id)
                way_from = self.get_way_by_id(way_from_id)
                way_to = self.get_way_by_id(exit_id)
                if junction is None or way_from is None or way_to is None:
                    continue
                if restriction == "no_left_turn" or way_from.oneway:
                    delete_from_set_of_actions(way_from, way_from, junction)
                if restriction[0:2] == "no":
                    delete_from_set_of_actions(way_from, way_to, junction)
                if restriction[0:4] == "only":
                    ways_to_delete = [way for way in junction.arms.keys() if way.id != way_to.id]
                    for way in ways_to_delete:
                        delete_from_set_of_actions(way_from, way, junction)

    def create_rules(self, ways_priorities):
        for junction in self.junctions:
            for exit in junction.arms.keys():
                ways_with_given_exit = []
                for possible_arm_for_given_exit in junction.arms.keys():
                    action_with_given_exit = possible_arm_has_given_exit(junction, possible_arm_for_given_exit, exit)
                    if action_with_given_exit is not None:
                        ways_with_given_exit.append((possible_arm_for_given_exit, action_with_given_exit))
                sort_ways_by_priority(ways_with_given_exit, ways_priorities)
                for i in range(len(ways_with_given_exit))[1:]:
                    j = 0
                    action = ways_with_given_exit[i][1]
                    while j < i:
                        rule = Rule(ways_with_given_exit[j][0], 0)
                        action.rules.add(rule)
                        j += 1

    def print_object_internal_structure(self):
        for junction in self.junctions:
            print "Junction ID:", junction.id, 'x:', junction.x, 'y:', junction.y
            print '---- Streets'
            for key in junction.arms.keys():
                print "---- Street name:", key.street_name, 'Street ID:', key.id, 'Lanes number:', key.lanes_number, 'Priority:', key.priority
                print '----**** Actions'
                for action in junction.arms[key]:
                    print "----**** Lane no.:", action.lane
                    print "----**** Exit street name:", action.exit.street_name, 'Exit street ID:', action.exit.id
                    print "----****######## Rules"
                    for rule in action.rules:
                        print "----****######## Entrance street name:", rule.entrance.street_name
                        print "----****######## Lane no.:", rule.lane
                print
            print
            print

    def correct_border_coordinates(self, node):
        if float(node.lat) < float(self.query.latitudeSouth):
            self.query.latitudeSouth = node.lat
        if float(node.lat) > float(self.query.latitudeNorth):
            self.query.latitudeNorth = node.lat
        if float(node.lon) < float(self.query.longitudeWest):
            self.query.longitudeWest = node.lon
        if float(node.lon) > float(self.query.longitudeEast):
            self.query.longitudeEast = node.lon
