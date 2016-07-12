from model.node import Node


class Junction(Node):
    arms = dict()

    def __init__(self, arms):
        self.arms = arms

    def print_to_file(self):
        """

        :return: void
        """

        # implemenattion TO DO