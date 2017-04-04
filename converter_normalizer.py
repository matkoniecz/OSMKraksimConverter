# coding=utf-8
from overpy import Way, Node, Result

import pprint


class ConverterNormalizer(object):

    """TARGET - all ways start and end on junction, each way links two junctions, topology is unchanged from source
    step 1) all ways that are joining at junctions formed by exactly two roads are merged
    step 2) all nodes that are sitting on one road not at the end - thrown away

    now all connections between junctions are single steep

    step 3) split all ways with more than two nodes into separate ways
    now all connection between junction are ways without nodes in the middle
    TARGET - solve onewayness problem
    TARGET - junction_in_kraksim != junction_in_osm
    ??????
    """

    @staticmethod
    def calculate_attached_ways(ways):
        """calculates attacjed ways for every node from dictionary of ways

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
        return attached_ways

    @staticmethod
    def simplify_loaded_data(result):
        pp = pprint.PrettyPrinter(indent=4)
        # pp.pprint(result.ways)

        # transfer data to structure that allows editing
        lowest_available_way_id = 1
        ways = {}
        for way in result.ways:
            nodes = way.get_nodes(resolve_missing=False)
            list_of_nodes = []
            for node in nodes:
                list_of_nodes += [node.id]
            ways[way.id] = list_of_nodes
            if lowest_available_way_id <= way.id:
                lowest_available_way_id = way.id + 1

        attached_ways = ConverterNormalizer.calculate_attached_ways(ways)

        # step 1
        for node in result.nodes:
            if len(attached_ways[node.id]) == 2:
                way_a = ways[attached_ways[node.id][0]]
                way_b = ways[attached_ways[node.id][1]]
                if way_a[0] == node.id or way_a[-1] == node.id:
                    if way_b[0] == node.id or way_b[-1] == node.id:
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
                        if way_a[-1] != way_b[0]:
                            way_b = way_b[::-1]

                        assert(way_a[-1] == way_b[0])
                        # remove from the second way node that appears in both
                        way_b = way_b[1:]

                        # merge second way into the first
                        ways[attached_ways[node.id][0]] += way_b

                        # recalculate, as way deletion
                        # makes part of data invalid
                        attached_ways = ConverterNormalizer.calculate_attached_ways(ways)

        # step 2
        for node in result.nodes:
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

        # step 3
        new_ways = []
        for way_id, nodes_list in ways.items():
            free_nodes = []
            for index, node_id in enumerate(nodes_list):
                # do not split at start on end where way terminates
                free_nodes.append(node_id)
                print way_id
                if node_id == nodes_list[0]:
                    print "start"
                    continue
                if node_id == nodes_list[-1]:
                    print "end"
                    continue
                print "middle"
                if len(attached_ways[node_id]) > 1:
                    print "<", node_id, "> on ", way_id
                    # split nodes since beginning the way (or previous split)
                    # into a separate way so junctions end all ways and
                    # no way passes through more than two junctions
                    new_ways.append({"parent": way_id, "nodes": free_nodes})
                    free_nodes = [node_id]
            ways[way_id] = free_nodes
        print new_ways

        remade_result = Result(elements=[], api=None)
        nodes_left = set()
        for way_id, nodes_list in ways.items():
            for node in nodes_list:
                nodes_left.add(node)
        for new_way in new_ways:
            for node in new_way["nodes"]:
                nodes_left.add(node)

        for id in nodes_left:
            remade_result.append(result.get_node(id))

        for way_id, nodes_list in ways.items():
            base_way = result.get_way(way_id)
            remade_way = ConverterNormalizer.remade_way(
                base_way, remade_result, nodes_list)
            remade_result.append(remade_way)

        for new_way in new_ways:
            base_way = result.get_way(new_way["parent"])
            remade_way = ConverterNormalizer.remade_way(
                base_way,
                remade_result,
                new_way["nodes"],
                lowest_available_way_id)
            lowest_available_way_id += 1
            remade_result.append(remade_way)

        print "020202020202-------------"
        pp.pprint(remade_result.ways)
        pp.pprint(remade_result.nodes)
        return remade_result

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
