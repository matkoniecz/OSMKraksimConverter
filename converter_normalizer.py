# coding=utf-8
from overpy import Way, Node, Result

import pprint
import traceback

class ConverterNormalizer(object):

    """TARGET - all ways start and end on junction, each way links two junctions, topology is unchanged from source
    step 1) all ways that are joining at junctions formed by exactly two roads are merged
    step 2) all nodes that are sitting on one road not at the end - thrown away

    now all connections between junctions are single step

    step 3) split all ways with more than two nodes into separate ways
    now all connection between junction are ways without nodes in the middle
    TARGET - solve onewayness problem
    TARGET - junction_in_kraksim != junction_in_osm
    ??????
    """

    @staticmethod
    def calculate_attached_ways(ways, nodes_list):
        """calculates attached ways for every node from dictionary of ways

        Args:
            ways (dict): keys: way_id, values: list of nodes ids forming way

        Returns:
            dict: keys: node_id, values: list_of_ways passing through that node
        """
        attached_ways = {}
        for way_id, nodes in ways.items():
            for node_id in nodes:
                if not node_id in attached_ways:
                    attached_ways[node_id] = []
                attached_ways[node_id] += [way_id]
        for node_id in nodes_list:
            try:
                attached_ways[node_id]
            except:
                attached_ways[node_id] = []
        return attached_ways

    @staticmethod
    def simplify_loaded_data(result):
        result = ConverterNormalizer.edit_loaded_data(result)
        try:
            ConverterNormalizer.validate_returned_data(result)
        except ConverterNormalizer.ConversionFailed, error:
            print "Inconsistency in produced data was detected. This should not happen. Kraksim may fail to load produced map."
            print str(ConverterNormalizer.ConversionFailed) + ' ' + str(error)
        return result

    class ConversionFailed(Exception):
        def __init__(self, str):
            super(ConverterNormalizer.ConversionFailed, self).__init__(str)

    @staticmethod
    def validate_returned_data(result):
        if result == None:
            raise ConverterNormalizer.ConversionFailed("normalizator crashed during generation")
        ConverterNormalizer.only_one_way_between_nodes(result)
        ConverterNormalizer.each_way_connects_two_nodes(result)
        ConverterNormalizer.no_nodes_on_exactly_two_ways(result)

    @staticmethod
    def only_one_way_between_nodes(result):
        existing_ways = {}
        for way in result.ways:
            nodes = way.get_nodes(resolve_missing=False)
            way_id = str(nodes[0].id) + '_' + str(nodes[1].id)
            present = True
            try:
                existing_ways[way_id]
            except KeyError as e:
                present = False

            if present:
                error_message = "connection between nodes " + str(nodes[0].id) + " and " + str(nodes[1].id) + " is duplicated"
                error_message += " - ways " + str(way_id) + " " + str(existing_ways[way_id])
                raise ConverterNormalizer.ConversionFailed(error_message)
            existing_ways[way_id] = way_id

    @staticmethod
    def each_way_connects_two_nodes(result):
        for way in result.ways:
            nodes = way.get_nodes(resolve_missing=False)
            if len(nodes) != 2:
                error_message = str(way.id) + " has " + str(len(nodes)) + " nodes - " + str(nodes)
                raise ConverterNormalizer.ConversionFailed(error_message)

    @staticmethod
    def no_nodes_on_exactly_two_ways(result):
        touching_ways_by_node = {}
        for way in result.ways:
            nodes = way.get_nodes(resolve_missing=False)
            for node in nodes:
                try:
                    touching_ways_by_node[node.id]
                except KeyError as e:
                    touching_ways_by_node[node.id] = 0
                touching_ways_by_node[node.id] += 1
        for node_id, attached_ways_count in touching_ways_by_node.items():
            if attached_ways_count == 2:
                error_message = str(node_id) + " is attached to exactly two ways. Such nodes are supposed to be eliminated"
                raise ConverterNormalizer.ConversionFailed(error_message)

    @staticmethod
    def build_ways_from_query_data(result, lowest_available_way_id):
        # dictionary indexed by way id, entries are list of nodes that form the way
        ways = {}

        for way in result.ways:
            nodes = way.get_nodes(resolve_missing=False)
            list_of_nodes = []
            for node in nodes:
                list_of_nodes += [node.id]
            ways[way.id] = list_of_nodes
            if lowest_available_way_id <= way.id:
                lowest_available_way_id = way.id + 1
        return ways, lowest_available_way_id


    @staticmethod
    def edit_loaded_data(result):
        print "enter converter_normalizer::edit_loaded_data"
        try:
            while True:
                lowest_available_way_id = 1

                # transfer data to structure that allows editing
                ways, lowest_available_way_id = ConverterNormalizer.build_ways_from_query_data(result, lowest_available_way_id)

                # indexed by nodes, entries are lists of way ids passing through a given node
                ways, lowest_available_way_id = ConverterNormalizer.join_ways(result.nodes, ways, lowest_available_way_id)
                ways, lowest_available_way_id = ConverterNormalizer.remove_nodes_that_are_not_affecting_topology(result.nodes, ways, lowest_available_way_id)
                result, ways, lowest_available_way_id = ConverterNormalizer.split_ways_on_crossings(result, ways, lowest_available_way_id)
                ways, lowest_available_way_id = ConverterNormalizer.remove_zero_length_parts(ways, lowest_available_way_id)
                result, removed_ways_count = ConverterNormalizer.generate_new_result_from_ways_structure(result, ways, lowest_available_way_id)
                # with nonzero removed ways it is possible that one of unwanted situations appeared again
                if removed_ways_count == 0:
                    break
        except Exception, error:
            print error
            print traceback.format_exc()
            print "exit converter_normalizer::edit_loaded_data"
            return None
        print "exit converter_normalizer::edit_loaded_data"
        return result

    @staticmethod
    def join_ways(nodes, ways, lowest_available_way_id):
        attached_ways = ConverterNormalizer.calculate_attached_ways(ways, [node.id for node in nodes])
        # step 1
        # find pair of ways that both end at the same node, and the node is touching only these two ways
        # as additional condition: these two ways are different ways (self-joining ways may appear at roundabouts)
        # such ways may be safely merged
        for node in nodes:
            if ConverterNormalizer.is_this_node_fulfilling_step_1_conditions(node, ways, attached_ways):
                way_a = ways[attached_ways[node.id][0]]
                way_b = ways[attached_ways[node.id][1]]
                # both ways end at a given node
                # node connects only to these two ways
                # merge way into one
                #
                # so delete one way and move its nodes
                # to the second one
                # it may require reversing direction of
                # nodes
                #
                # TODO - is it OK to ignore tags from deleted way?
                # TODO HACK - not handled that some tags
                # depend on direction of the way
                # especially oneway

                del ways[attached_ways[node.id][1]]  # deletes way_b

                # reverse ways so that
                # - way_a ends on the common node
                # - way_b starts on the common node
                if way_a[-1] != node.id:
                    way_a = way_a[::-1]

                if way_b[0] != node.id:
                    way_b = way_b[::-1]

                # way_a must end at the same node as way_b starts
                error = str(way_a[-1]) + ' and ' + str(way_b[0]) + ' was supposed to be the same id'
                assert(way_a[-1] == way_b[0]), error

                # remove from the second way node that appears in both
                way_b = way_b[1:]

                # merge second way into the first
                ways[attached_ways[node.id][0]] += way_b

                #recalculate attached ways
                attached_ways = ConverterNormalizer.calculate_attached_ways(ways, [node.id for node in nodes])
        return ways, lowest_available_way_id

    @staticmethod
    def remove_nodes_that_are_not_affecting_topology(nodes, ways, lowest_available_way_id):
        attached_ways = ConverterNormalizer.calculate_attached_ways(ways, [node.id for node in nodes])
        # step 2
        for node in nodes:
            if len(attached_ways[node.id]) == 1:
                # node is on the exactly one way
                way_id = attached_ways[node.id][0]
                way = ways[way_id]
                if way[0] != node.id and way[-1] != node.id:
                    # not the first, not the last node
                    # should be deleted

                    # node should be deleted from cleaned dataset and removed
                    # from sole way where it resides to achieve this one must
                    # recreate way (I see no support for modification of
                    # Way structure after it is created)
                    ways[way_id].remove(node.id)
        return ways, lowest_available_way_id

    @staticmethod
    def remove_zero_length_parts(ways, lowest_available_way_id):
        # if way has two the same ids after each other it means that either way was self-looping or that OSM data was broken
        # in both cases one of duplicated ids may be removed
        for way_id, nodes_list in ways.items():
            if nodes_list[0] == nodes_list[-1] and len(nodes_list) == 2:
                del ways[way_id]
            for index, node_id in enumerate(nodes_list):
                if index > 0:
                    if nodes_list[index] == nodes_list[index-1]:
                        del nodes_list[index]
        return ways, lowest_available_way_id


    @staticmethod
    def split_ways_on_crossings(result, ways, lowest_available_way_id):
        attached_ways = ConverterNormalizer.calculate_attached_ways(ways, [node.id for node in result.nodes])
        # step 3
        new_ways = []
        for way_id, nodes_list in ways.items():
            free_nodes = []
            for index, node_id in enumerate(nodes_list):
                free_nodes.append(node_id)
                # do not split at start on end where way terminates
                if node_id == nodes_list[0]:
                    continue
                if node_id == nodes_list[-1]:
                    continue
                if len(attached_ways[node_id]) > 1:
                    # split nodes since beginning the way (or previous split)
                    # into a separate way so junctions end all ways and
                    # no way passes through more than two junctions
                    new_ways.append({"parent": way_id, "nodes": free_nodes})
                    free_nodes = [node_id]
            ways[way_id] = free_nodes

        for new_way in new_ways:
            base_way = result.get_way(new_way["parent"])
            remade_way = ConverterNormalizer.remade_way(
                base_way,
                result,
                new_way["nodes"],
                lowest_available_way_id)
            result.append(remade_way)
            ways[lowest_available_way_id] = new_way["nodes"]
            lowest_available_way_id += 1

        return result, ways, lowest_available_way_id

    @staticmethod
    def generate_new_result_from_ways_structure(result, ways, lowest_available_way_id):
        remade_result = Result(elements=[], api=None)
        nodes_left = set()
        for way_id, nodes_list in ways.items():
            for node in nodes_list:
                nodes_left.add(node)

        for id in nodes_left:
            remade_result.append(result.get_node(id))

        removed_ways_count = 0

        unique_ids = set()
        for way_id, nodes_list in ways.items():
            # node_a to node_b, node_b to node_a are considered the same by Kraksim
            if nodes_list[0] < nodes_list[1]:
                nodes_list = nodes_list[::-1]
            kraksim_id = str(nodes_list[0]) + str(nodes_list[1])
            if kraksim_id in unique_ids:
                removed_ways_count += 1
            else:
                unique_ids.add(kraksim_id)
                base_way = result.get_way(way_id)
                remade_way = ConverterNormalizer.remade_way(
                    base_way, remade_result, nodes_list)
                remade_result.append(remade_way)

        return remade_result, removed_ways_count

    @staticmethod
    def is_this_node_fulfilling_step_1_conditions(node, ways, attached_ways):
        # true junction, with more than two ways
        if len(attached_ways[node.id]) != 2:
            return False

        # self-joining way (roundabout)
        if attached_ways[node.id][0] == attached_ways[node.id][1]:
            return False

        way_a = ways[attached_ways[node.id][0]]
        way_b = ways[attached_ways[node.id][1]]
        if way_a[0] == node.id or way_a[-1] == node.id:
            if way_b[0] == node.id or way_b[-1] == node.id:
                if way_b[0] in way_a and way_b[-1] in way_a:
                    # cycle would be created
                    return False
                if way_a[0] in way_b and way_a[-1] in way_b:
                    # cycle would be created
                    return False
                return True
        return False

    @staticmethod
    def remade_node(node, belongs_to_result):
        return Node(node_id=node.id, lat=node.lat, lon=node.lon, attributes={}, result=belongs_to_result)

    @staticmethod
    def remade_way(
        way,
        belongs_to_result,
        node_ids_override=None,
            way_id_override=None):
        node_ids_list = []
        for node in way.get_nodes(resolve_missing=False):
            node_ids_list += [node.id]
        if node_ids_override is not None:
            node_ids_list = node_ids_override

        id = way.id
        if way_id_override is not None:
            id = way_id_override

        way = Way(
            id,
            center_lat=way.center_lat,
            center_lon=way.center_lon,
            node_ids=node_ids_list,
            attributes={},
            result=belongs_to_result,
            tags=way.tags)
        return way
