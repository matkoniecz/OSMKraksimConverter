# coding=utf-8
import math
from model.junction import Junction
from model.way import Way
from model.gateway import Gateway
from model.node import Node
from model.action import Action
from model.rule import Rule

class ConverterReader:
    """"
    class containing methods for converting OSM data to inner data structures
    """
    query = None
    gateways = set()
    junctions = set()
    ways = set()

    def __init__(self, query):
        self.query = query

    def read_to_internal_structure(self, result):
        nodes_that_represent_junctions = []
        nodes_set = set()
        ways_to_nodes = dict()

        loop_number = len(result.ways)
        i = 0
        # petla do wykrywania skrzyzowan
        for way in result.ways:
            for node in way.get_nodes(resolve_missing=False):
                nodes_that_represent_junctions.append(node)
                nodes_set.add(node)
                if way in ways_to_nodes:
                    ways_to_nodes[way].add(node)
                else:
                    ways_to_nodes[way] = {node}
            i += 1
            print i, "/", loop_number

        for node in nodes_set:
            nodes_that_represent_junctions.remove(node)
            if node in nodes_that_represent_junctions:
                nodes_that_represent_junctions.remove(node)

        nodes_that_represent_junctions = set(nodes_that_represent_junctions)

        # tworzenie obiektow Junction i Way
        for way in result.ways:
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
                    way.tags.get("lanes", "1"),
                    way.tags.get("highway", "n/a"))
            if way.tags.get("oneway", "n/a") == "yes":
                w.oneway = True
            self.ways.add(w)
            for node in ways_to_nodes[way]:
                if node in nodes_that_represent_junctions:
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

        # tworzenie obiektow Gateway
        for way in result.ways:
            n_first = way.nodes[0]
            n_last = way.nodes[-1]
            if n_first.id not in [x.id for x in self.junctions] and n_first.id not in [gateway.id for gateway in self.gateways]:
                x_gateway = int(round(self.measure(float(self.query.latitudeSouth), float(self.query.longitudeWest),
                                       float(self.query.latitudeSouth), float(n_first.lon))))
                y_gateway = int(round(self.measure(float(self.query.latitudeSouth), float(self.query.longitudeWest),
                                   float(n_first.lat), float(self.query.longitudeWest))))
                gateway = Gateway(n_first.id, x_gateway, y_gateway)
                self.gateways.add(gateway)

            if n_last.id not in [x.id for x in self.junctions] and n_last.id not in [gateway.id for gateway in self.gateways]:
                x_gateway = int(round(self.measure(float(self.query.latitudeSouth), float(self.query.longitudeWest),
                                         float(self.query.latitudeSouth), float(n_last.lon))))
                y_gateway = int(round(self.measure(float(self.query.latitudeSouth), float(self.query.longitudeWest),
                                     float(n_last.lat), float(self.query.longitudeWest))))
                gateway = Gateway(n_last.id, x_gateway, y_gateway)
                self.gateways.add(gateway)

        # tworzenie bloku nr 3
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
        for junction in self.junctions:
            for way in junction.arms.keys():
                if way.oneway and str(way.starting_point.id) == str(junction.id):
                    continue
                actions = []
                for possible_exit_for_given_way in junction.arms.keys():
                    if possible_exit_for_given_way.oneway and str(possible_exit_for_given_way.starting_point.id) != str(junction.id):
                            continue
                    action = Action(0, possible_exit_for_given_way, set())
                    actions.append(action)
                junction.arms[way] = set(actions)

                # for action in actions:
                #     for possible_exit_for_given_way in junction.arms.keys():
                #         if ways_priorities[possible_exit_for_given_way.priority] > ways_priorities[way.priority]:
                #             rule = Rule(possible_exit_for_given_way, 0)
                #             action.rules.add(rule)
                if way.oneway:
                    self.delete_from_set_of_actions(way, way, junction)

        for relation in result.relations:
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
                if junction is None:
                    continue
                if restriction == "no_left_turn" or way_from.oneway:
                    self.delete_from_set_of_actions(way_from, way_from, junction)
                if restriction[0:2] == "no":
                    self.delete_from_set_of_actions(way_from, way_to, junction)
                if restriction[0:4] == "only":
                    ways_to_delete = [way for way in junction.arms.keys() if way.id != way_to.id]
                    for way in ways_to_delete:
                        self.delete_from_set_of_actions(way_from, way, junction)

        for junction in self.junctions:
            for exit in junction.arms.keys():
                ways_with_given_exit = []
                for possible_arm_for_given_exit in junction.arms.keys():
                    action_with_given_exit = self.possible_arm_has_given_exit(junction, possible_arm_for_given_exit, exit)
                    if action_with_given_exit is not None:
                        ways_with_given_exit.append((possible_arm_for_given_exit, action_with_given_exit))
                self.sort_ways_by_priority(ways_with_given_exit, ways_priorities)
                for i in range(len(ways_with_given_exit))[1:]:
                    j = 0
                    action = ways_with_given_exit[i][1]
                    while j < i:
                        rule = Rule(ways_with_given_exit[j][0], 0)
                        action.rules.add(rule)
                        j += 1

        # testowe wypisywanie
        # print self.junctions
        # for junction in self.junctions:
        #     print "Junction ID:", junction.id, 'x:', junction.x, 'y:', junction.y
        #     print '---- Streets'
        #     for key in junction.arms.keys():
        #         print "---- Street name:", key.street_name, 'Street ID:', key.id, 'Lanes number:', key.lanes_number, 'Priority:', key.priority
        #         print '----**** Actions'
        #         for action in junction.arms[key]:
        #             print "----**** Lane no.:", action.lane
        #             print "----**** Exit street name:", action.exit.street_name, 'Exit street ID:', action.exit.id
        #             print "----****######## Rules"
        #             for rule in action.rules:
        #                 print "----****######## Entrance street name:", rule.entrance.street_name
        #                 print "----****######## Lane no.:", rule.lane
        #         print
        #     print
        #     print

    def measure(self, lat1, lon1, lat2, lon2):  # generally used geo measurement function
        R = 6378.137
        dLat = (lat2 - lat1) * math.pi / 180
        dLon = (lon2 - lon1) * math.pi / 180
        a = math.sin(dLat / 2) * math.sin(dLat / 2) + math.cos(lat1 * math.pi / 180) * math.cos(
            lat2 * math.pi / 180) * math.sin(dLon / 2) * math.sin(dLon / 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        d = R * c
        return d * 1000 / 7.5

    def get_junction_by_id(self, junction_id):
        for junction in self.junctions:
            if junction.id == junction_id:
                return junction

    def get_way_by_id(self, way_from_id):
        for way in self.ways:
            if way.id == way_from_id:
                return way

    def delete_from_set_of_actions(self, way_from, exit, junction):
        """

        :param way: way.Way
        :param junction: junction.Junction
        :return:
        """
        actions_to_delete = [action for action in junction.arms[way_from] if action.exit.id == exit.id]
        for action in actions_to_delete:
            junction.arms[way_from].remove(action)

    def possible_arm_has_given_exit(self, junction, possible_arm_for_given_exit, exit):
        if junction.arms[possible_arm_for_given_exit] is not None:
            for action in junction.arms[possible_arm_for_given_exit]:
                if str(action.exit.id) == str(exit.id):
                    return action
        return None

    def sort_ways_by_priority(self, ways_with_given_exit, ways_priorities):
        for i in range(len(ways_with_given_exit))[1:]:
            tmp = ways_with_given_exit[i]
            j = i - 1
            while j>=0 and ways_priorities[ways_with_given_exit[j][0].priority] < ways_priorities[tmp[0].priority]:
                ways_with_given_exit[j+1] = ways_with_given_exit[j]
                j -= 1

            ways_with_given_exit[j + 1] = tmp







