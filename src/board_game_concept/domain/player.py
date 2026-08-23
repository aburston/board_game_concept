class Player:
    """One player of a game, known by their number.

    The range is stated here rather than by whoever registers a player, because
    a number arrives by more than one door: typed at the server prompt, read
    from a player configuration file, and read back from a game on disk. A check
    at any one of those is a check the others do not get, and the one that was
    forgotten is the one that lets a bad number in.

    The numbers outside it are not players at all - 0 is the administrator and
    1000 is the observer - and neither owns units or takes orders, so neither is
    describable by this class. Who they are is `service/identity.py`'s to say.
    """

    # a player's number, at each end
    FIRST = 1
    LAST = 999

    def __init__(self, number):
        self.number = number
        assert isinstance(number, int), "number must be an integer value"
        assert (number >= 0), "number must not be negative"
        assert self.FIRST <= number <= self.LAST, (
            f"a player's number must be from {self.FIRST} to {self.LAST}")
