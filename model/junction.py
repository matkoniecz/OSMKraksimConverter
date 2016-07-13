from model.node import Node


class Junction(Node):
    arms = None

    def __init__(self, arms, id, x, y):
        self.arms = arms
        self.id = id
        self.x = x
        self.y = y

    def print_to_file(self):
        """

        :return: void
        """

        # implemenattion TO DO