# -*- coding: utf-8 -*-
import codecs

import lxml.etree as ET
# import sys    # sys.setdefaultencoding is cancelled by site.py
# reload(sys)    # to re-enable sys.setdefaultencoding()
# sys.setdefaultencoding('utf-8')
import re, htmlentitydefs


def unescape(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text  # leave as is

    return re.sub("&#?\w+;", fixup, text)


def correct_xml_file(file_path):
    f = codecs.open(file_path + ".xml", "r+", "utf-8")
    text = unescape(f.read())
    f.close()
    f = codecs.open(file_path + ".xml", "w+", "utf-8")
    f.write(text)
    f.close()


def generate_traffic(file_path, gateways):
    traffic_net = ET.Element("traffic")
    for gateway_1 in gateways:
        for gateway_2 in gateways:
            if not gateway_1.id == gateway_2.id:
                scheme_branch = ET.SubElement(traffic_net, "scheme", count="100")
                gateway_1_branch = ET.SubElement(scheme_branch, "gateway", id=str(gateway_1.id))
                ET.SubElement(gateway_1_branch, "uniform", a="0", b="8000")
                ET.SubElement(scheme_branch, "gateway", id=str(gateway_2.id))

                tree = ET.ElementTree(traffic_net)
                tree.write(file_path + "_generator.xml", pretty_print=True)


class ConverterPrinter:
    def __init__(self):
        pass

    @staticmethod
    def print_to_file(file_path, gateways, junctions, roads):
        road_net = ET.Element("RoadNet")

        # ------------------------ Blok nr 1 ----------------------------------
        nodes_branch = ET.SubElement(road_net, "nodes")
        for gateway in gateways:
            ET.SubElement(nodes_branch, "gateway", id=str(gateway.id), x=str(gateway.x), y=str(gateway.y))

        for junction in junctions:
            ET.SubElement(nodes_branch, "intersection", id=str(junction.id), x=str(junction.x), y=str(junction.y))

        # ------------------------ Blok nr 2 ----------------------------------
        roads_branch = ET.SubElement(road_net, "roads")
        for road in roads:
            road_branch = ET.SubElement(roads_branch, "road", id=str(road.id), street=road.street_name,
                          attrib={'from':str(road.starting_point.id), 'to':str(road.ending_point.id)})
            uplink_branch = ET.SubElement(road_branch, "uplink")
            ET.SubElement(uplink_branch, "main", length=str(road.calculate_length()), numberOfLanes=str(road.lanes_number))
            if not road.oneway:
                downlink_branch = ET.SubElement(road_branch, "downlink")
                ET.SubElement(downlink_branch, "main", length=str(road.calculate_length()), numberOfLanes=str(road.lanes_number))

        # ------------------------ Blok nr 3 ----------------------------------
        intersection_descriptions_branch = ET.SubElement(road_net, "intersectionDescriptions")
        for junction in junctions:
            intersection_branch = ET.SubElement(intersection_descriptions_branch, "intersection", id=str(junction.id))
            for arm in junction.arms.keys():
                arm_actions_branch = ET.SubElement(intersection_branch, "armActions", arm=str(arm.ending_point.id), dir="NS")
                for action in junction.arms[arm]:
                    action_branch = ET.SubElement(arm_actions_branch, "action", lane=str(action.lane),
                                                  exit=str(action.exit.ending_point.id))
                    for rule in action.rules:
                        rule_branch = ET.SubElement(action_branch, "rule", entrance=str(rule.entrance.ending_point.id), lane=str(rule.lane))


        tree = ET.ElementTree(road_net)
        tree.write(file_path + ".xml", pretty_print=True)

        correct_xml_file(file_path)

        generate_traffic(file_path, gateways)

        pass

