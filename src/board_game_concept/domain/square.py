# what a board square holds when nothing else does


class Empty:
    # a blank rather than a printable glyph: the grid's rules already say
    # where the squares are, so the character inside one only has to speak
    # when something is standing there - and every printable character is
    # then left for a player to give one of their own unit types
    def __str__(self):
        return " "
