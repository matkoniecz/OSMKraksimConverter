class Rule:
    entrance = None
    lane = 0

    def __init__(self, entrance, lane):
        """

        :param entrance: way.Way
        :param lane: short
        """
        self.entrance = entrance
        self.lane = lane