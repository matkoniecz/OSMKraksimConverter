class Way:
    id = ''
    street_name = ''
    starting_point = ''
    ending_point = ''
    lanes_number = ''
    priority = ''

    def __init__(self, id, street_name, starting_point, ending_point, lanes_number, priority):
        self.id = id
        self.street_name = street_name
        self.starting_point = starting_point
        self.ending_point = ending_point
        self.lanes_number = lanes_number
        self.priority = priority

    def calculate_length(self):
        """

        :return: int
        """
        # Implementation TO DO
        return 0

    def print_to_file(self):
        """

        :return: void
        """