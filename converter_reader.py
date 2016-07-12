import overpy
import time

class ConverterReader:
	'class containing methods for converting OSM data to inner data structures'
	gateways = []
	junctions = []
	
	def __init__(self):
		pass
		
	def readToInternalStructure(self, result):
		nodes = []
		nodesSet = set()
		for way in result.ways:
			for node in way.get_nodes(resolve_missing=True):
				time.sleep(0.1) #overpy.exception.OverpassTooManyRequests, zeby to wyrzucic trzeba zaimplementowac wlasne "resolve_missing"(lapac ten wyjatek i powtarzac kwerende) 
				nodes.append(node)
				nodesSet.add(node)