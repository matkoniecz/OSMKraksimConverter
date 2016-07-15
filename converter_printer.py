import lxml.etree as ET


class ConverterPrinter:
    def __init__(self):
        pass

    @staticmethod
    def print_to_file(file_path, gateways, junctions, roads):
        road_net = ET.Element("roadnet")
        nodes = ET.SubElement(road_net, "nodes")

        for gateway in gateways:
            ET.SubElement(nodes, "gateway", id=str(gateway.id), x=str(gateway.x), y=str(gateway.y))

        tree = ET.ElementTree(road_net)
        tree.write(file_path + ".xml", pretty_print=True)

        pass
