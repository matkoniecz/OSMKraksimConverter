import math

class Way:
    id = ''
    street_name = ''
    starting_point = None
    ending_point = None
    lanes_number = ''
    priority = ''
    oneway = False

    def __init__(self, id, street_name, starting_point, ending_point, lanes_number, priority):
        self.id = id
        self.street_name = street_name
        self.starting_point = starting_point
        self.ending_point = ending_point
        self.lanes_number = lanes_number
        self.priority = priority

    def calculate_length(self):
        """

        :return: float
        """
        return int(math.ceil(math.sqrt((self.starting_point.x - self.ending_point.x) ** 2
                                   + (self.starting_point.y - self.ending_point.y) ** 2)))

    def print_to_file(self):
        """

        :return: void
        """