import unittest
from overpy import Way, Node, Result
from converter_normalizer import ConverterNormalizer


class TestStringMethods(unittest.TestCase):

    def test_removal_of_nodes_not_changing_topology_of_road_graph(self):
        # for us geometry of ways is not relevant, only topology is important
        # so nodes that are on exactly one way and
        # are not its start/end (forming dead end) should be discarded

        result = Result(elements=[], api=None)
        start = Node(node_id=1, lat=1, lon=10, attributes={}, result=result)
        discarding_1 = Node(
            node_id=2,
            lat=2,
            lon=20,
            attributes={},
            result=result)
        discarding_2 = Node(
            node_id=3,
            lat=3,
            lon=30,
            attributes={},
            result=result)
        discarding_3 = Node(
            node_id=4,
            lat=4,
            lon=40,
            attributes={},
            result=result)
        end = Node(node_id=5, lat=5, lon=50, attributes={}, result=result)

        result.append(start)
        result.append(discarding_1)
        result.append(discarding_2)
        result.append(discarding_3)
        result.append(end)

        node_list_for_way = [
            start.id,
            discarding_1.id,
            discarding_2.id,
            discarding_3.id,
            end.id]
        way = Way(
            way_id=1,
            center_lat=3,
            center_lon=30,
            node_ids=node_list_for_way,
            attributes={},
            result=result)
        result.append(way)

        self.assertEqual(len(result.ways), 1)
        self.assertEqual(len(result.nodes), 5)

        self.assertEqual(start.id, 1)
        self.assertEqual(start.lat, 1)
        self.assertEqual(start.lon, 10)
        self.assertEqual(end.id, 5)
        self.assertEqual(end.lat, 5)
        self.assertEqual(end.lon, 50)

        result = ConverterNormalizer.simplify_loaded_data(result)
        ConverterNormalizer.validate_returned_data(result)

        self.assertEqual(len(result.ways), 1)
        self.assertEqual(len(result.nodes), 2)
        node_a = result.nodes[0]
        node_b = result.nodes[1]
        if node_a.id != 1:
            node_a, node_b = node_b, node_a
        self.assertEqual(node_a.id, 1)
        self.assertEqual(node_a.lat, 1)
        self.assertEqual(node_a.lon, 10)
        self.assertEqual(node_b.id, 5)
        self.assertEqual(node_b.lat, 5)
        self.assertEqual(node_b.lon, 50)

    def test_the_simplest_merging_of_ways(self):
        # road between two junctions may be in OSM represented by any number of ways
        # typical case for split is that one of road attributes changes - for example
        # surface, lane count, part of bridge is tunnel or any other change
        # road may be also split without any reason whatsoever, and it is a
        # valid tagging

        # TODO - how tags should be merged? Throw them away?
        # Just use tags from random way? How tags are used by converter?

        result = Result(elements=[], api=None)
        start = Node(node_id=1, lat=1, lon=-10, attributes={}, result=result)
        middle = Node(node_id=2, lat=2, lon=-50, attributes={}, result=result)
        end = Node(node_id=3, lat=3, lon=-50, attributes={}, result=result)

        way_a = Way(
            way_id=1,
            center_lat=1.5,
            center_lon=-30,
            node_ids=[start.id,
                      middle.id],
            attributes={},
            result=result)
        way_b = Way(
            way_id=2,
            center_lat=2.5,
            center_lon=-50,
            node_ids=[middle.id,
                      end.id],
            attributes={},
            result=result)

        result.append(start)
        result.append(middle)
        result.append(end)
        result.append(way_a)
        result.append(way_b)

        self.assertEqual(len(result.ways), 2)
        self.assertEqual(len(result.nodes), 3)

        result = ConverterNormalizer.simplify_loaded_data(result)
        ConverterNormalizer.validate_returned_data(result)

        self.assertEqual(len(result.ways), 1)
        nodes = {}
        for node in result.nodes:
            nodes[node.id] = node
        self.assertTrue(1 in nodes)
        self.assertTrue(3 in nodes)
        node_a = nodes[1]
        node_b = nodes[3]
        self.assertEqual(node_a.id, 1)
        self.assertEqual(node_a.lat, 1)
        self.assertEqual(node_a.lon, -10)
        self.assertEqual(node_b.id, 3)
        self.assertEqual(node_b.lat, 3)
        self.assertEqual(node_b.lon, -50)

    def test_the_simplest_splitting_of_ways(self):
        # in OSM way may end at any place - juction is just node connected to multiple ways
        # it is possible to have a real junction formed by two ways joining, it is also
        # possible to have nodes that belong to two ways, without a real junction
        # (both ways end at that node and are representing a single road)

        result = Result(elements=[], api=None)
        start_of_long_way = Node(
            node_id=1,
            lat=1,
            lon=-10,
            attributes={},
            result=result)
        end_of_long_way = Node(
            node_id=2,
            lat=5,
            lon=-90,
            attributes={},
            result=result)
        junction = Node(
            node_id=4,
            lat=3,
            lon=-50,
            attributes={},
            result=result)
        node_for_short_way = Node(
            node_id=5,
            lat=3,
            lon=-100,
            attributes={},
            result=result)

        long_way = Way(
            way_id=1,
            center_lat=3,
            center_lon=-50,
            node_ids=[start_of_long_way.id,
                      junction.id,
                      end_of_long_way.id],
            attributes={},
            result=result)
        short_way = Way(
            way_id=2,
            center_lat=3,
            center_lon=-75,
            node_ids=[junction.id,
                      node_for_short_way.id],
            attributes={},
            result=result)

        result.append(start_of_long_way)
        result.append(end_of_long_way)
        result.append(junction)
        result.append(node_for_short_way)
        result.append(long_way)
        result.append(short_way)

        self.assertEqual(len(result.ways), 2)
        self.assertEqual(len(result.nodes), 4)

        result = ConverterNormalizer.simplify_loaded_data(result)
        ConverterNormalizer.validate_returned_data(result)

        expected_way_count = 3
        self.assertEqual(len(result.ways), expected_way_count)
        self.assertEqual(len(result.nodes), 4)
        for i in range(expected_way_count):
            self.assertEqual(len(result.ways[i].get_nodes()), 2)
        # TODO check topology

    def test_remove_duplicated_ways(self):
        result = Result(elements=[], api=None)
        start = Node(node_id=1, lat=1, lon=-10, attributes={}, result=result)
        end = Node(node_id=3, lat=3, lon=-50, attributes={}, result=result)

        way_a = Way(
            way_id=1,
            center_lat=1.5,
            center_lon=-30,
            node_ids=[start.id,
                      end.id],
            attributes={},
            result=result)
        way_b = Way(
            way_id=2,
            center_lat=1.5,
            center_lon=-30,
            node_ids=[start.id,
                      end.id],
            attributes={},
            result=result)
        result.append(start)
        result.append(end)
        result.append(way_a)
        result.append(way_b)
        self.assertEqual(len(result.ways), 2)
        self.assertEqual(len(result.nodes), 2)
        result = ConverterNormalizer.simplify_loaded_data(result)
        ConverterNormalizer.validate_returned_data(result)
        self.assertEqual(len(result.ways), 1)
        self.assertEqual(len(result.nodes), 2)
        node_a = result.nodes[0]
        node_b = result.nodes[1]
        if node_a.id != 1:
            node_a, node_b = node_b, node_a
        self.assertEqual(node_a.id, 1)
        self.assertEqual(node_a.lat, 1)
        self.assertEqual(node_a.lon, -10)
        self.assertEqual(node_b.id, 3)
        self.assertEqual(node_b.lat, 3)
        self.assertEqual(node_b.lon, -50)

    def test_p_shaped_topology(self):
        # this test possible case that caused an unexpected bug
        # due to splitting and deduplication P shape should be reduced to single way (| shape)

        result = Result(elements=[], api=None)
        start_of_long_way = Node(
            node_id=1,
            lat=1,
            lon=-10,
            attributes={},
            result=result)
        end_of_long_way = Node(
            node_id=2,
            lat=5,
            lon=-90,
            attributes={},
            result=result)
        junction = Node(
            node_id=4,
            lat=3,
            lon=-50,
            attributes={},
            result=result)

        long_way = Way(
            way_id=1,
            center_lat=3,
            center_lon=-50,
            node_ids=[start_of_long_way.id,
                      junction.id,
                      end_of_long_way.id],
            attributes={},
            result=result)
        short_way = Way(
            way_id=2,
            center_lat=3,
            center_lon=-75,
            node_ids=[junction.id,
                      start_of_long_way.id],
            attributes={},
            result=result)

        result.append(start_of_long_way)
        result.append(end_of_long_way)
        result.append(junction)
        result.append(long_way)
        result.append(short_way)

        self.assertEqual(len(result.ways), 2)
        self.assertEqual(len(result.nodes), 3)

        result = ConverterNormalizer.simplify_loaded_data(result)
        ConverterNormalizer.validate_returned_data(result)

        expected_way_count = 1
        self.assertEqual(len(result.ways), expected_way_count)
        self.assertEqual(len(result.nodes), 2)
        for i in range(expected_way_count):
            self.assertEqual(len(result.ways[i].get_nodes()), 2)
        # TODO check topology

    def test_p_shaped_topology_on_single_way(self):
        # this test possible case that caused an unexpected bug
        # due to splitting and deduplication P shape should be reduced to single way (| shape)

        result = Result(elements=[], api=None)
        start_of_way = Node(
            node_id=1,
            lat=1,
            lon=-10,
            attributes={},
            result=result)
        selfjunction = Node(
            node_id=2,
            lat=5,
            lon=-90,
            attributes={},
            result=result)
        loop = Node(
            node_id=4,
            lat=3,
            lon=-50,
            attributes={},
            result=result)

        way = Way(
            way_id=1,
            center_lat=3,
            center_lon=-50,
            node_ids=[start_of_way.id,
                      selfjunction.id,
                      loop.id,
                      selfjunction.id,],
            attributes={},
            result=result)

        result.append(start_of_way)
        result.append(selfjunction)
        result.append(loop)
        result.append(selfjunction)
        result.append(way)

        self.assertEqual(len(result.ways), 1)
        self.assertEqual(len(result.nodes), 3)

        result = ConverterNormalizer.simplify_loaded_data(result)
        ConverterNormalizer.validate_returned_data(result)

        expected_way_count = 1
        self.assertEqual(len(result.ways), expected_way_count)
        self.assertEqual(len(result.nodes), 2)
        for i in range(expected_way_count):
            self.assertEqual(len(result.ways[i].get_nodes()), 2)
        # TODO check topology

    def test_selfvalidator_only_one_way_between_nodes(self):
        result = Result(elements=[], api=None)
        start = Node(node_id=1, lat=1, lon=-10, attributes={}, result=result)
        end = Node(node_id=3, lat=3, lon=-50, attributes={}, result=result)

        way_a = Way(
            way_id=1,
            center_lat=1.5,
            center_lon=-30,
            node_ids=[start.id,
                      end.id],
            attributes={},
            result=result)
        way_b = Way(
            way_id=2,
            center_lat=1.5,
            center_lon=-30,
            node_ids=[start.id,
                      end.id],
            attributes={},
            result=result)
        result.append(start)
        result.append(end)
        result.append(way_a)
        result.append(way_b)
        #ConverterNormalizer.only_one_way_between_nodes(result)
        self.assertRaises(ConverterNormalizer.ConversionFailed, ConverterNormalizer.only_one_way_between_nodes, result)
        ConverterNormalizer.validate_returned_data(ConverterNormalizer.simplify_loaded_data(result))

    def test_selfvalidator_each_way_connects_two_nodes(self):
        result = Result(elements=[], api=None)
        start_of_long_way = Node(
            node_id=1,
            lat=1,
            lon=-10,
            attributes={},
            result=result)
        end_of_long_way = Node(
            node_id=2,
            lat=5,
            lon=-90,
            attributes={},
            result=result)
        junction = Node(
            node_id=4,
            lat=3,
            lon=-50,
            attributes={},
            result=result)
        node_for_short_way = Node(
            node_id=5,
            lat=3,
            lon=-100,
            attributes={},
            result=result)

        long_way = Way(
            way_id=1,
            center_lat=3,
            center_lon=-50,
            node_ids=[start_of_long_way.id,
                      junction.id,
                      end_of_long_way.id],
            attributes={},
            result=result)
        short_way = Way(
            way_id=2,
            center_lat=3,
            center_lon=-75,
            node_ids=[junction.id,
                      node_for_short_way.id],
            attributes={},
            result=result)

        result.append(start_of_long_way)
        result.append(end_of_long_way)
        result.append(junction)
        result.append(node_for_short_way)
        result.append(long_way)
        result.append(short_way)
        self.failUnlessRaises(ConverterNormalizer.ConversionFailed, ConverterNormalizer.each_way_connects_two_nodes, result)
        ConverterNormalizer.validate_returned_data(ConverterNormalizer.simplify_loaded_data(result))

    def test_selfvalidator_no_nodes_on_exactly_two_ways(self):
        result = Result(elements=[], api=None)
        start = Node(node_id=1, lat=1, lon=10, attributes={}, result=result)
        discarding_1 = Node(
            node_id=2,
            lat=2,
            lon=20,
            attributes={},
            result=result)
        middle = Node(
            node_id=4,
            lat=4,
            lon=40,
            attributes={},
            result=result)
        end = Node(node_id=5, lat=5, lon=50, attributes={}, result=result)

        result.append(start)
        result.append(middle)
        result.append(end)

        way_a = Way(
            way_id=1,
            center_lat=3,
            center_lon=30,
            node_ids=[start.id, middle.id],
            attributes={},
            result=result)
        result.append(way_a)
        way_b = Way(
            way_id=2,
            center_lat=3,
            center_lon=30,
            node_ids=[middle.id, end.id],
            attributes={},
            result=result)
        result.append(way_b)
        self.failUnlessRaises(ConverterNormalizer.ConversionFailed, ConverterNormalizer.no_nodes_on_exactly_two_ways, result)
        ConverterNormalizer.validate_returned_data(ConverterNormalizer.simplify_loaded_data(result))

    def test_crash_on_isolated_node(self):
        result = Result(elements=[], api=None)
        node = Node(node_id=251680825, lat=1, lon=1, attributes={},result=result)
        result.append(node)
        node = Node(node_id=30372051, lat=1, lon=1, attributes={},result=result)
        result.append(node)
        node = Node(node_id=1924449568, lat=1, lon=1, attributes={},result=result)
        result.append(node)
        node = Node(node_id=1325756454, lat=1, lon=1, attributes={},result=result)
        result.append(node)
        way = Way(way_id=216999581,center_lat=1,center_lon=1,node_ids=[30372051, 1325756454, 251680825],attributes={},result=result)
        result.append(way)
        ConverterNormalizer.validate_returned_data(ConverterNormalizer.simplify_loaded_data(result))

    def test_missing_attached_ways_recalculation_regression(self):
        result = Result(elements=[], api=None)
        node = Node(node_id=1, lat=1, lon=1, attributes={},result=result)
        result.append(node)
        node = Node(node_id=2, lat=1, lon=1, attributes={},result=result)
        result.append(node)
        node = Node(node_id=3, lat=1, lon=1, attributes={},result=result)
        result.append(node)
        node = Node(node_id=4, lat=1, lon=1, attributes={},result=result)
        result.append(node)
        way = Way(way_id=10,center_lat=1,center_lon=1,node_ids=[1, 2, ],attributes={},result=result)
        result.append(way)
        way = Way(way_id=11,center_lat=1,center_lon=1,node_ids=[3, 4, ],attributes={},result=result)
        result.append(way)
        way = Way(way_id=12,center_lat=1,center_lon=1,node_ids=[4, 1, ],attributes={},result=result)
        result.append(way)
        ConverterNormalizer.validate_returned_data(ConverterNormalizer.simplify_loaded_data(result))

if __name__ == '__main__':
    unittest.main()
