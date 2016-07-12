from model.node import Node


class Junction(Node):
    arms = None

    def __init__(self, arms, id):
        self.arms = arms
        self.id = id

    def print_to_file(self):
        """

        :return: void
        """

        # implemenattion TO DO