"""Turning the crank: publishing orders, resolving turns, and waiting.

The commit barrier lives here rather than in storage, because "every player has
committed" is a rule about the game and not a fact about files. The repository
is asked who has committed; what that means is decided here.
"""

import sys

import yaml

from ..domain import Empty, UnitType
from ..storage.serialise import serialise_orders, serialise_units


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
        number, serialise_orders(game.board, game.getPlayerObj(number)))

    # tell the server there is something to look at, rather than leaving it to
    # notice on its own
    repository.wake('server')
    return True


def _published_orders(game):
    """Every order published for this turn, as `(player number, order)`."""
    orders = []
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
            orders.append((int(unit['player']), unit))
    return orders


def _is_deployment(game, p_number, unit):
    """Whether this order asks for a unit the board does not hold yet."""
    if unit['state'] not in (UnitType.INITIAL, UnitType.NOP):
        return False
    owner = game.players[p_number]['obj']
    return game.board.findUnit(unit['name'], owner) is None


def _contended_cells(game, orders):
    """The cells more than one deployment is asking for this turn.

    Both are refused. Letting the first through made the winner whichever
    player the server happened to read first, which is player number order:
    a fixed advantage to the lowest-numbered player, in a race neither of them
    could see they were in.
    """
    claimed = {}
    for p_number, unit in orders:
        if not _is_deployment(game, p_number, unit):
            continue
        cell = (int(unit['x']), int(unit['y']))
        claimed.setdefault(cell, []).append(p_number)
    return {cell for cell, claimants in claimed.items() if len(claimants) > 1}


def _apply_orders(game, reject):
    """Merge every player's published orders into the board."""
    orders = _published_orders(game)
    contended = _contended_cells(game, orders)

    for p_number, unit in orders:
        owner = game.players[p_number]['obj']
        unit_type = game.players[p_number]['types'][unit['type']]['obj']
        name, x, y = unit['name'], unit['x'], unit['y']
        state = unit['state']

        # destruction is final. An order naming a unit the server holds as
        # destroyed is refused whatever it asks for, so no cell falling empty
        # can bring one back
        known = game.board.findUnit(name, owner)
        if known is not None and known.destroyed:
            reject(p_number, unit, f"unit {name} has been destroyed")
            continue

        if (int(x), int(y)) in contended and _is_deployment(game, p_number, unit):
            reject(p_number, unit,
                   f"two units were deployed at ({x}, {y}), so both were refused")
            continue

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
            if known is None:
                # a unit the player has created but the server has not placed
                # yet: this is its deployment
                try:
                    game.board.add(owner, x, y, name, unit_type)
                except AssertionError as e:
                    reject(p_number, unit, e)
        else:
            # an order the server cannot make sense of is refused, rather
            # than taking the turn down with it
            reject(p_number, unit, f"invalid unit state {str(state)}")


def has_started(game):
    """Whether the game has begun: whether any unit has ever reached the board.

    The administrator's commit that ends setup is resolved like a turn, and at
    that point nobody has deployed anything. Judging elimination there would
    declare every player out before the game had started.
    """
    return bool(game.board.units)


def eliminated_players(game):
    """The players holding no unit that is on the board and not destroyed.

    Derived from the board every turn rather than tracked, so that who is out
    cannot drift out of step with what is standing.
    """
    if not has_started(game):
        return []
    out = []
    for number, player in game.players.items():
        alive = any(unit.player.number == number
                    and unit.on_board and not unit.destroyed
                    for unit in game.board.units)
        if not alive:
            out.append(number)
    return sorted(out)


def decide(game, turn_number, eliminated):
    """The outcome of the game, or None while it is still being played.

    A game registered with fewer than two players is never decided: there is
    nobody to be the last player standing against. That is what keeps a
    one-player game usable as a sandbox.
    """
    if len(game.players) < 2 or not has_started(game):
        return None
    standing = [number for number in game.players if number not in eliminated]
    if len(standing) > 1:
        return None
    return {
        'decided': True,
        'winner': standing[0] if standing else None,
        'turn': turn_number,
    }


def resolve(game):
    """Apply every player's orders, end the turn, and publish the result."""
    if game.getSizeX() <= 1 or game.getSizeY() <= 1:
        print(f"the board size is too small ({game.getSizeX()}, {game.getSizeY()})")
        return False
    if game.getOutcome() is not None:
        # the game is over; there is no turn left to resolve
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
    events = game.board.commit()
    _report_turn(game, events, reject)
    repository.clear_orders()

    # setup ends with a resolution of its own, before anything is on the board.
    # That is not a turn of the game and is not numbered as one
    turn_number = game.getTurnNumber() + 1 if has_started(game) else 0
    eliminated = eliminated_players(game)
    outcome = decide(game, turn_number, eliminated)
    progress = {'turn': turn_number, 'eliminated': eliminated}
    if outcome is not None:
        progress['outcome'] = outcome
    repository.write_progress(progress)
    game.setProgress(progress)

    for number, player in game.players.items():
        repository.write_player(number, _types_without_objects(player))
        if 'units' in player:
            # units that came in with a loaded player file become that
            # player's orders for the turn about to be resolved
            repository.write_orders(number, _as_orders(player['units']))
        # written every turn, so it always describes the turn just resolved
        # rather than accumulating stale refusals
        repository.write_rejections(number, rejected.get(number, []),
                                    turn=turn_number)

    # the authoritative record, and then what each player is entitled to see
    repository.write_units(serialise_units(game.board, turn=turn_number))
    for number, player in game.players.items():
        repository.write_view(
            number, serialise_units(game.board, player['obj'], turn=turn_number))

    # every player waiting on this turn can stop waiting
    for number in game.players:
        repository.wake(number)

    return True


def _report_turn(game, events, reject):
    """Tell each player what the turn would not do for them.

    The engine reports what happened and knows nothing about players' files;
    turning the events that name a unit into refusals is this layer's job. An
    order refused while it was being applied was already reported; these are
    the ones that failed while the turn was being resolved, which used to be
    dropped in silence.
    """
    def order_for(unit):
        return {
            'name': unit.name,
            'type': unit.type_name,
            'x': unit.x,
            'y': unit.y,
        }

    for event in events:
        if event.kind == 'refused':
            unit = _named(game, event.detail['unit'])
            if unit is not None:
                reject(unit.player.number, order_for(unit),
                       event.detail['reason'])
        elif event.kind == 'undecided':
            where = f"({event.detail['x']}, {event.detail['y']})"
            for name in event.detail['units'].split(','):
                unit = _named(game, name)
                if unit is not None:
                    reject(unit.player.number, order_for(unit),
                           f"the contest at {where} was undecided")


def _named(game, name):
    """The unit of that name, or None if the board no longer holds one."""
    try:
        return game.board.getUnitByName(name)[0]
    except AssertionError:
        return None


def _as_orders(units):
    return yaml.safe_dump({'units': units})


def _awaited_players(game):
    """The players the turn is held open for: everyone still in the game.

    A player who has been wiped out cannot commit again, and waiting for one
    froze the game for everyone else.
    """
    eliminated = set(game.getEliminated())
    return {number for number in game.players if number not in eliminated}


def wait_for_all_commits(game):
    """Hold the turn open until every player still in the game has committed."""
    print("wait for player commit")
    awaited = _awaited_players(game)
    # the waiter is opened before the first check, so a commit signalled from
    # here on is buffered rather than lost, and one that arrived earlier is
    # found by the check itself
    with game.repository.waiter('server') as waiter:
        while not awaited.issubset(set(game.repository.committed_players())):
            waiter.wait()


def wait_for_turn(game):
    """Wait until the server has consumed this player's orders."""
    with game.repository.waiter(game.player_number) as waiter:
        while game.repository.has_orders(game.player_number):
            waiter.wait()
