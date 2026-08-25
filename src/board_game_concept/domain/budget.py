"""What a player has spent of their point budget, and what they may still buy.

One module, asked by both of the places a unit can reach the board: the
client's `add unit`, which refuses, and the turn's resolution, which rejects.
Two enforcers restating the arithmetic would be two rules as far as a player
reading the two messages is concerned, so the arithmetic and the sentence are
both here.

What a player has spent is derived from the board rather than counted. A
running total is a second record of a fact the board already holds, and the
only thing a second record can do is drift: one not decremented when a
deployment is refused, or decremented twice when a draft is replayed, is a
budget that quietly stops matching the army. `game-outcome` derives who is
eliminated from the board for the same reason.
"""


def spent(board, player):
    """The points this player has laid out on the units the board holds.

    Every unit, whatever state it is in: neither `destroyed` nor `on_board` is
    consulted. That absence is the no-refund rule - points buy a unit, not the
    time it survives for.
    """
    if board is None:
        return 0
    return sum(unit.cost for unit in board.units
               if unit.player is not None
               and unit.player.number == player.number)


def remaining(board, player):
    """What this player has left to spend.

    Asking this of a player whose budget is not this session's to know is a
    mistake in the caller rather than a number: an opponent's budget is
    unknown, not zero and not the default.
    """
    assert player.budget is not None, (
        f"player {player.number}'s budget is not this session's to know")
    return player.budget - spent(board, player)


def message(player, unit_type, left):
    """The one sentence a refused deployment is reported with.

    Built here rather than at each of the two places that refuse one, so the
    client's refusal and the turn's rejection cannot come to say different
    things about the same overspend.
    """
    return (f"deploying a {unit_type.name} costs {unit_type.cost} points, and "
            f"only {left} of player {player.number}'s {player.budget}-point "
            f"budget are left")


def refusal(board, player, unit_type):
    """Why this player cannot deploy this type, or None if they can."""
    left = remaining(board, player)
    if unit_type.cost <= left:
        return None
    return message(player, unit_type, left)


def charge(board, player, deployments):
    """Charge a player for several deployments at once, in a settled order.

    `deployments` are `(unit name, type)` pairs. They are charged in order of
    unit name, and what the budget can no longer pay for is refused: which of
    an unaffordable set survives is decided by the rules rather than by the
    order a file or a list happened to hold them in, which is the same reason
    nothing else in resolution reads a list's order.

    Returns `{unit name: why it was refused}` for the ones that did not fit,
    which is empty when the whole set is affordable.
    """
    left = remaining(board, player)
    refused = {}
    for name, unit_type in sorted(deployments, key=lambda pair: pair[0]):
        if unit_type.cost <= left:
            left -= unit_type.cost
            continue
        refused[name] = message(player, unit_type, left)
    return refused
