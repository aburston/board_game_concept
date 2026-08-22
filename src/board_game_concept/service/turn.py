"""Turning the crank: publishing orders, resolving turns, and waiting.

The commit barrier lives here rather than in storage, because "every player has
committed" is a rule about the game and not a fact about files. The repository
is asked who has committed; what that means is decided here.
"""

import sys

import yaml

from ..domain import Empty, UnitType
from ..storage.serialise import serialise_units


def _types_without_objects(player):
    """A player's types as they are written down, without the live objects."""
    types = player['types']
    for type_name in types:
        types[type_name].pop('obj', None)
    return types


def publish(game):
    """Publish this player's orders and wait for the turn to be resolved."""
    if game.getSizeX() <= 1 or game.getSizeY() <= 1:
        print(f"the board size is too small ({game.getSizeX()}, "
              f"{game.getSizeY()})")
        return False

    number = game.player_number
    repository = game.repository
    repository.write_player(number, _types_without_objects(game.players[number]))
    repository.mark_committed(number)
    repository.write_orders(
        number, serialise_units(game.board, game.getPlayerObj(number)))

    # tell the server there is something to look at, rather than leaving it to
    # notice on its own
    repository.wake('server')
    return True


def _apply_orders(game, reject):
    """Merge every player's published orders into the board."""
    for player_number in list(game.players.keys()):
        player = game.players[player_number]
        if 'moves' not in player:
            continue
        units = player['moves']['units']
        # a player holding no units publishes "units: None", which reads back
        # as the string rather than as null
        if not units or units == 'None':
            continue
        for unit in units:
            p_number = int(unit['player'])
            owner = game.players[p_number]['obj']
            unit_type = game.players[p_number]['types'][unit['type']]['obj']
            name, x, y = unit['name'], unit['x'], unit['y']
            state = unit['state']

            if state == UnitType.INITIAL:
                try:
                    game.board.add(owner, x, y, name, unit_type)
                except AssertionError as e:
                    reject(p_number, unit, e)
            elif state == UnitType.MOVING:
                # the order names a unit, and a square may hold several, so it
                # is resolved against the unit rather than against the square
                try:
                    actual_unit = game.board.getUnitByName(name, owner)[0]
                except AssertionError as e:
                    reject(p_number, unit, e)
                    continue
                actual_unit.move(unit['direction'])
            elif state == UnitType.NOP:
                if isinstance(game.board.getUnitByCoords(x, y), Empty):
                    # a unit the player has created but the server has not
                    # placed yet: this is its deployment
                    try:
                        game.board.add(owner, x, y, name, unit_type)
                    except AssertionError as e:
                        reject(p_number, unit, e)
            else:
                # an order the server cannot make sense of is refused, rather
                # than taking the turn down with it
                reject(p_number, unit, f"invalid unit state {str(state)}")


def resolve(game):
    """Apply every player's orders, end the turn, and publish the result."""
    if game.getSizeX() <= 1 or game.getSizeY() <= 1:
        print(f"the board size is too small ({game.getSizeX()}, {game.getSizeY()})")
        return False

    repository = game.repository
    repository.ensure()
    repository.write_board(game.board.size_x, game.board.size_y)

    # orders refused this turn, collected per player so each can be told what
    # the server would not do for them
    rejected = {}

    def reject(p_number, unit, reason):
        print(f"rejected order from player {p_number}: {reason}",
              file=sys.stderr)
        rejected.setdefault(p_number, []).append({
            'unit': str(unit['name']),
            'type': str(unit['type']),
            'x': int(unit['x']),
            'y': int(unit['y']),
            'reason': str(reason),
        })

    _apply_orders(game, reject)

    # resolve all moves and end the turn
    game.board.commit()
    repository.clear_orders()

    for number, player in game.players.items():
        repository.write_player(number, _types_without_objects(player))
        if 'units' in player:
            # units that came in with a loaded player file become that
            # player's orders for the turn about to be resolved
            repository.write_orders(number, _as_orders(player['units']))
        # written every turn, so it always describes the turn just resolved
        # rather than accumulating stale refusals
        repository.write_rejections(number, rejected.get(number, []))

    # the authoritative record, and then what each player is entitled to see
    repository.write_units(serialise_units(game.board))
    for number, player in game.players.items():
        repository.write_view(
            number, serialise_units(game.board, player['obj']))

    # every player waiting on this turn can stop waiting
    for number in game.players:
        repository.wake(number)

    return True


def _as_orders(units):
    return yaml.safe_dump({'units': units})


def wait_for_all_commits(game):
    """Hold the turn open until every registered player has committed."""
    print("wait for player commit")
    # the waiter is opened before the first check, so a commit signalled from
    # here on is buffered rather than lost, and one that arrived earlier is
    # found by the check itself
    with game.repository.waiter('server') as waiter:
        while len(game.repository.committed_players()) != len(game.players):
            waiter.wait()


def wait_for_turn(game):
    """Wait until the server has consumed this player's orders."""
    with game.repository.waiter(game.player_number) as waiter:
        while game.repository.has_orders(game.player_number):
            waiter.wait()
