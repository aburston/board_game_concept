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

    A player also holds the point budget they were registered with, which is
    what bounds the army they may deploy. It is stated here for the same reason
    the number is, and arrives by the same several doors, with the HTTP tier as
    a fourth. `None` is the fifth case and means the budget is not this
    session's to know: a player reads their own record and nobody else's, so a
    player object built for an opponent has a number and no budget.
    """

    # a player's number, at each end
    FIRST = 1
    LAST = 999

    # the point budget a player is registered with when none is named, and the
    # ends of the range one may be named within. The cheapest type a player can
    # define costs 3 and the dearest costs 120, so the top of the range buys
    # eight of the dearest; the bottom buys nothing at all, deliberately, since
    # a player set up with nothing to deploy is the administrator's to decide
    # and not the rules' to refuse
    DEFAULT_BUDGET = 100
    MIN_BUDGET = 1
    MAX_BUDGET = 1000

    def __init__(self, number, budget=DEFAULT_BUDGET):
        self.number = number
        assert isinstance(number, int), "number must be an integer value"
        assert (number >= 0), "number must not be negative"
        assert self.FIRST <= number <= self.LAST, (
            f"a player's number must be from {self.FIRST} to {self.LAST}")

        self.budget = budget
        if budget is not None:
            assert isinstance(budget, int) and not isinstance(budget, bool), (
                "budget must be an integer value")
            assert self.MIN_BUDGET <= budget <= self.MAX_BUDGET, (
                f"a player's budget must be from {self.MIN_BUDGET} to "
                f"{self.MAX_BUDGET}")
