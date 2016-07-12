from overpy import Overpass

class Query:
    'Holds query and its parameters, that is coordinates'
    #
    latitudeSouth = 0
    latitudeNorth = 0
    longitudeWest = 0
    longitudeEast = 0

    def __init__(self, latitudeSouth, longitudeWest, latitudeNorth, longitudeEast):
        self.latitudeSouth = latitudeSouth
        self.latitudeNorth = latitudeNorth
        self.longitudeWest = longitudeWest
        self.longitudeEast = longitudeEast

    def __repr__(self):
        return "Query(%r,%r,%r,%r)" % (self.latitudeSouth, self.longitudeWest, self.latitudeNorth, self.longitudeEast)

    def __str__(self):
        return "(way(" + self.latitudeSouth + "," + self.longitudeWest + "," + self.latitudeNorth + "," + self.longitudeEast + ')["highway"~"motorway|trunk|primary|secondary|tertiary"];node(w);relation(' + self.latitudeSouth + "," + self.longitudeWest + "," + self.latitudeNorth + "," + self.longitudeEast + ')["restriction"~"no_right_turn|no_left_turn|no_u_turn|no_straight_on|only_right_turn|only_left_turn|only_straight_on"];way(r););out;'


class ConverterQueryLoader:

    overpass = None

    def __init__(self):
        self.overpass = Overpass()

    def execute_query(self, query):
        return self.overpass.query(query)
