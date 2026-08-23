class Player:
    def __init__(self, number):
        self.number = number
        assert isinstance(number, int), "number must be an integer value"
        assert (number >= 0), "number must not be negative"
