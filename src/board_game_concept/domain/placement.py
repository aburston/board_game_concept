"""Where a player may deploy during setup.

One module, asked by both of the places a deployment can reach the board: the
client's `add unit`, which refuses, and the turn's resolution, which rejects.
The same reason `budget.py` is one module - two enforcers restating the rule
would be two rules as far as a player reading the two messages is concerned.

The rule. A game of **exactly two players** is split into a top half and a
bottom half by rows: the lower-numbered player deploys in the rows nearer row
0, the higher-numbered one in the rows nearer the last. Columns are never
restricted, so a half is the full width of the board. Where the number of rows
is **odd** the single middle row is neutral and belongs to neither player.

Every other player count - one, three, more - is the **null case of the same
rule**: the area is every row, and the caller does not know it was ever a
special case. `deploy_unit`, the resolution and the published view all run
this for every game; "the whole board" is a value returned here rather than a
call the caller decided to skip, so a game that is not two-player behaves
exactly as it did before this rule existed.

The area is a pure function of the board size and the registered player
numbers. Nothing is stored: a game reloaded computes the same halves it had
before, and which half is whose cannot drift from what is enforced.
"""


def _placing(player_numbers):
    """The two players the split is between, in order, or None.

    `None` is the null case - one player, or three or more - and every caller
    reads it as "the whole board".
    """
    numbers = sorted(set(int(number) for number in player_numbers))
    return tuple(numbers) if len(numbers) == 2 else None


def neutral_row(size_y):
    """The row belonging to neither player, or None where there is none.

    A board with an odd number of rows has a single middle row that cannot be
    halved; it is neutral rather than given to whoever the arithmetic happened
    to round towards. An even board has no such row and the halves meet.
    """
    return size_y // 2 if size_y % 2 else None


def rows(player_number, player_numbers, size_y):
    """The rows this player may deploy in, in order.

    Every row where the game is not two-player, or where this session is not
    one of the two placing players - the observer and the administrator are
    watching rather than placing, and are told the whole board.
    """
    placing = _placing(player_numbers)
    if placing is None or int(player_number) not in placing:
        return list(range(size_y))
    middle = neutral_row(size_y)
    half = size_y // 2
    if int(player_number) == placing[0]:
        # the lower number takes the top: the rows nearer row 0
        return list(range(0, half))
    # and the higher number the bottom, which starts after the neutral row
    # where there is one and at the halfway mark where there is not
    return list(range(half + 1 if middle is not None else half, size_y))


def area(player_number, player_numbers, size_x, size_y):
    """What this player may deploy in, as the record every client reads.

    The rows rather than the squares: columns are never restricted, so a row
    list is the whole of the area and a square list would be ten times the
    payload for a rule that does not vary along a row. `restricted` is false
    when the area is the whole board, which is what a caption is drawn from.
    """
    allowed = rows(player_number, player_numbers, size_y)
    return {
        'size_x': int(size_x),
        'size_y': int(size_y),
        'rows': allowed,
        'neutral_row': (neutral_row(size_y)
                        if _placing(player_numbers) else None),
        'restricted': len(allowed) != int(size_y),
    }


def allows(player_number, player_numbers, x, y, size_x, size_y):
    """Whether this player may deploy on this square."""
    if x < 0 or y < 0 or x >= size_x or y >= size_y:
        return False
    return int(y) in rows(player_number, player_numbers, size_y)


def message(player_number, player_numbers, y, size_y):
    """The one sentence a placement refused for where it is is reported with.

    Built here rather than at each of the two places that refuse one, so the
    client's refusal and the turn's rejection cannot come to say different
    things about the same square. It says which of the two reasons it was,
    because "not your half" and "the neutral row" are different mistakes.
    """
    if neutral_row(size_y) == int(y):
        return (f"row {int(y)} is the neutral row and belongs to neither "
                "player, so nothing can be deployed in it")
    allowed = rows(player_number, player_numbers, size_y)
    where = (f"rows {allowed[0]} to {allowed[-1]}" if allowed else 'no row')
    return (f"player {int(player_number)} deploys in {where}, so row "
            f"{int(y)} is the other player's half")


def refusal(player_number, player_numbers, x, y, size_x, size_y):
    """Why this player cannot deploy here, or None if they can.

    A square that is not on the board at all is not this rule's to refuse:
    it answers None and leaves the placement to be refused for being out of
    bounds, where it belongs. Saying "that is the other player's half" of a
    row the board does not have would name the wrong mistake.
    """
    if x < 0 or y < 0 or x >= size_x or y >= size_y:
        return None
    if allows(player_number, player_numbers, x, y, size_x, size_y):
        return None
    return message(player_number, player_numbers, y, size_y)
