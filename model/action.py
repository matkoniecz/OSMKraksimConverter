class Action:
    lane = -2
    exit = None
    rules = set()

    def __init__(self, lane, exit, rules):
        """

        :param lane: int
        :param exit: way.Way
        :param rules: set<rule.Rule>
        """
        self.lane = lane
        self.exit = exit
        self.rules = rules

    def print_to_file(self):
        """

        :return: void
        """

        # TO DO