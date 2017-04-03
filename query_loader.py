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
        return '''<union>
                      <query type="way">
                        <bbox-query s="'''+self.latitudeSouth+'''" w="'''+self.longitudeWest+'''" n="'''+self.latitudeNorth+'''" e="'''+self.longitudeEast+'''"/>
                        <has-kv k="highway" regv="motorway|motorway_link|trunk|trunk_link|primary|primary_link|secondary|secondary_link|tertiary|tertiary_link|unclassified|residential"/>
                      </query>
                      <recurse type="way-node"/>
                      <query type="relation">
                        <bbox-query s="'''+self.latitudeSouth+'''" w="'''+self.longitudeWest+'''" n="'''+self.latitudeNorth+'''" e="'''+self.longitudeEast+'''"/>
                        <has-kv k="restriction" regv="no_right_turn|no_left_turn|no_u_turn|no_straight_on|only_right_turn|only_left_turn|only_straight_on"/>
                      </query>
                  </union>
                  <print />'''


class ConverterQueryLoader:

    overpass = None

    def __init__(self):
        self.overpass = Overpass()

    def execute_query(self, query):
        return self.overpass.query(query)
