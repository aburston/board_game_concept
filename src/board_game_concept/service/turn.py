"""Turning the crank: publishing orders, resolving turns, and waiting.

The commit barrier lives here rather than in storage, because "every player has
committed" is a rule about the game and not a fact about files. The repository
is asked who has committed; what that means is decided here.
"""

import sys

from ..domain import UnitType, budget
from ..storage.serialise import units_document
from . import identity
from .errors import GameError


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
    # held for writing: publishing an order file and resolving a turn, which
    # deletes every order file, must not overlap
    with repository.held():
        repository.write_player(
            number, _types_without_objects(game.players[number]),
            game.getPlayerObj(number).budget)
        repository.mark_committed(number, game.getTurnNumber())
        repository.write_orders(
            number,
            units_document(game.board, game.getPlayerObj(number),
                           in_play_only=True))

        # the draft has become the published orders, so there is nothing left
        # uncommitted to restore
        game.clearDraft()

    # tell the server there is something to look at, rather than leaving it to
    # notice on its own
    game.notifier.wake('server')
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


def _contended_squares(game, orders):
    """The squares more than one deployment is asking for this turn.

    Both are refused. Letting the first through made the winner whichever
    player the server happened to read first, which is player number order:
    a fixed advantage to the lowest-numbered player, in a race neither of them
    could see they were in.
    """
    claimed = {}
    for p_number, unit in orders:
        if not _is_deployment(game, p_number, unit):
            continue
        square = (int(unit['x']), int(unit['y']))
        claimed.setdefault(square, []).append(p_number)
    return {square for square, claimants in claimed.items() if len(claimants) > 1}


def _unaffordable_deployments(game, deployments):
    """The deployments no player's point budget will pay for this turn.

    Judged before any of them is applied, against the board as the turn began,
    so that every one of a player's deployments is charged against the same
    starting position however many there are. Keyed by `(player, unit name)`,
    which is what the loop below has in hand.

    `deployments` are the `(player, order)` pairs that are deployments and have
    not already been refused for some other reason.

    The client already refuses what a player cannot afford, so nothing typed
    at a prompt reaches this. What does is a loaded player file, or orders
    written by something other than the client, and neither of those has been
    through the rule on the way in.
    """
    by_player = {}
    for p_number, unit in deployments:
        try:
            unit_type = game.players[p_number]['types'][unit['type']]['obj']
        except KeyError:
            # an order naming a type its owner has not defined. The loop below
            # is where that has always been found, and it stays there
            continue
        by_player.setdefault(p_number, []).append(
            (str(unit['name']), unit_type))

    refused = {}
    for p_number, priced in by_player.items():
        player_obj = game.players[p_number]['obj']
        for name, reason in budget.charge(
                game.board, player_obj, priced).items():
            refused[(p_number, name)] = reason
    return refused


def _refused_deployments(game, orders):
    """Every deployment this turn will not carry out, and why.

    Both reasons a deployment can be refused before it is even attempted are
    decided here, against the board as the turn began: two players asking for
    one square, and an owner whose points will not pay for it. Judged up front
    rather than as the loop reaches each order, so that what one player is
    refused cannot depend on how far through the list the loop happens to be.

    Keyed by `(player, unit name)`, which is what the loop has in hand.
    """
    refusals = {}
    contended = _contended_squares(game, orders)
    standing = []
    for p_number, unit in orders:
        if not _is_deployment(game, p_number, unit):
            continue
        square = (int(unit['x']), int(unit['y']))
        if square in contended:
            refusals[(p_number, str(unit['name']))] = (
                f"two units were deployed at {square}, so both were refused")
            continue
        standing.append((p_number, unit))

    # only the deployments still standing are charged. One already refused for
    # its square never reaches the board, so charging it would spend points on
    # nothing - and could push another of that player's units over a budget it
    # actually fits inside
    refusals.update(_unaffordable_deployments(game, standing))
    return refusals


def _apply_orders(game, reject):
    """Merge every player's published orders into the board."""
    orders = _published_orders(game)
    refused = _refused_deployments(game, orders)

    for p_number, unit in orders:
        owner = game.players[p_number]['obj']
        unit_type = game.players[p_number]['types'][unit['type']]['obj']
        name, x, y = unit['name'], unit['x'], unit['y']
        state = unit['state']

        # destruction is final. An order naming a unit the server holds as
        # destroyed is refused whatever it asks for, so no square falling empty
        # can bring one back
        known = game.board.findUnit(name, owner)
        if known is not None and known.destroyed:
            reject(p_number, unit, f"unit {name} has been destroyed")
            continue

        # a contested square, or a deployment its owner's budget will not pay
        # for. The budget is applied here as well as at the client because an
        # order file reaches this without having passed through one; either
        # way, the rest of that player's orders are carried out as usual
        if (p_number, str(name)) in refused:
            reject(p_number, unit, refused[(p_number, str(name))])
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
    """The players holding no unit that could ever act again.

    What counts is whether a unit has a future, not what it happens to hold
    this turn. A unit at zero energy used to be finished, because energy never
    came back, and not counting it was the honest reading; now a unit that
    stands still recovers a point a turn, so being at zero is a bad afternoon
    rather than a death, and judging a player on it would decide games on the
    timing of a snapshot.

    A **wall** is the one unit that has no future: its type was designed with
    no energy at all, so resting gives it nothing, it can never move and it
    can never strike. A player holding nothing but walls holds nothing that
    can play, and is out.

    Derived from the board every turn rather than tracked, so that who is out
    cannot drift out of step with what is standing.
    """
    if not has_started(game):
        return []
    out = []
    for number, player in game.players.items():
        alive = any(unit.player.number == number
                    and unit.on_board and not unit.destroyed
                    and unit.type_energy > 0
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
    """Apply every player's orders, end the turn, and publish the result.

    Only a session entitled to the whole game and allowed to change it may
    resolve one, which today is the administrator's. A player's session is
    built from that player's own published view and loads no other player's
    orders, so resolving from one would apply a single player's orders and
    republish a board holding only the units that player may see - every other
    player wiped off the record and eliminated for having nothing standing.
    The observer sees the whole game and changes nothing, so a turn resolved
    from one would be a read that wrote. Both are a caller's mistake rather
    than a rule of the game, and both are refused here where the damage would
    be done rather than left to whichever layer opened the session.
    """
    if not (game.seesEverything() and identity.may_change(game.player_number)):
        raise GameError(
            f"{identity.describe(game.player_number)} may not resolve a turn: "
            f"a turn is resolved by the administrator")
    if game.getSizeX() <= 1 or game.getSizeY() <= 1:
        print(f"the board size is too small ({game.getSizeX()}, {game.getSizeY()})")
        return False
    if game.getOutcome() is not None:
        # the game is over; there is no turn left to resolve
        return False

    repository = game.repository
    # held for writing, for the whole of it: the barrier check that
    # authorised this resolution and everything it publishes are one
    # span, and a commit arriving mid-flight must not land inside it
    with repository.held():
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

        # --- what this turn produced. All of it is written before anybody waiting
        # on the turn is let go, because a released player reads it

        for number, player in game.players.items():
            repository.write_player(number, _types_without_objects(player),
                                    player['obj'].budget)
            # written every turn, so it always describes the turn just resolved
            # rather than accumulating stale refusals
            repository.write_rejections(number, rejected.get(number, []),
                                        turn=turn_number)

        # the authoritative record, and then what each player is entitled to see
        repository.write_units(units_document(game.board, turn=turn_number))
        for number, player in game.players.items():
            repository.write_view(
                number,
                units_document(game.board, player['obj'], turn=turn_number))

        # --- and only now, the turn is over

        # this is what releases a player waiting on the turn: a client waits by
        # testing whether its own order file is still there, so the file has to
        # outlive every write above it. Nothing between here and the top of
        # resolution reads one - orders are applied from what `load` put in memory -
        # so the deletion is free to be last, and has to be
        repository.clear_orders()
        # the commits that opened this turn are spent with it
        repository.clear_commits()

        # the next turn's input, written after the deletion rather than before it.
        # Units that came in with a loaded player file become that player's orders
        # for the turn about to be resolved, and the server commits them on that
        # player's behalf - publishing orders for somebody without committing them
        # would leave the turn held open for a player who has nobody to type
        # `commit` for them. A `clear_orders` placed after this erases them
        for number, player in game.players.items():
            if 'units' in player:
                repository.write_orders(
                    number, _loaded_orders_document(game, number, player,
                                                   turn_number))
                repository.mark_committed(number, turn_number)

        # the administrator's setup has been committed like anyone else's
        game.clearDraft()

        # every player waiting on this turn can stop waiting
        for number in game.players:
            game.notifier.wake(number)

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


def _loaded_orders_document(game, number, player, turn):
    """The orders document for a loaded player, before their units are placed.

    The `player['units']` list comes from a file the caller wrote by hand and
    may lack the type-defaults (`type_attack`, `type_health`, `type_energy`)
    the emitter expects. Those are read from the player's type record, which
    is what they defaulted to before the unit spent anything.
    """
    types = player.get('types') or {}
    units = []
    for index, unit in enumerate(player['units']):
        type_record = types.get(unit.get('type')) or {}
        units.append({
            'id': index,
            'player': unit.get('player', number),
            'type': unit.get('type'),
            'name': unit.get('name'),
            'symbol': unit.get('symbol'),
            'attack': unit.get('attack'),
            'health': unit.get('health'),
            'energy': unit.get('energy'),
            # a loaded file may name a type by a key that does not match its
            # own `name`, and units may lack the type-defaults altogether;
            # `type_record`'s stats fall back to the unit's own, which is
            # what they defaulted to before the unit spent anything
            'type_attack': (unit.get('type_attack')
                            or type_record.get('attack')
                            or unit.get('attack')),
            'type_health': (unit.get('type_health')
                            or type_record.get('health')
                            or unit.get('health')),
            'type_energy': (unit.get('type_energy')
                            or type_record.get('energy')
                            or unit.get('energy')),
            'x': unit.get('x'), 'y': unit.get('y'),
            'state': unit.get('state'), 'direction': unit.get('direction'),
            'destroyed': unit.get('destroyed', False),
            'on_board': unit.get('on_board', False),
        })
    return {
        'board': {'size_x': game.board.size_x, 'size_y': game.board.size_y},
        'turn': turn,
        'player': number,
        'units': units,
    }


def _awaited_players(game):
    """The players the turn is held open for: everyone still in the game.

    A player who has been wiped out cannot commit again, and waiting for one
    froze the game for everyone else.
    """
    eliminated = set(game.getEliminated())
    return {number for number in game.players if number not in eliminated}


def barrier_met(game):
    """Whether every player still in the game has committed for its open turn.

    Said once and asked in two places: by the waiting, about the game it was
    given, and by the resolution, about the game it has just read. A barrier
    that meant one thing to the waiter and another to the resolver would be
    worse than the gap it exists to close.
    """
    return _awaited_players(game).issubset(
        set(game.repository.committed_players(game.getTurnNumber())))


def resolve_when_ready(game):
    """Read the game, ask whether the turn may be resolved, and resolve it.

    All three under one hold, which is the point: the question that authorises
    a resolution and the resolution itself must not come apart. Between them,
    another caller can resolve the turn and spend every commit that opened it,
    and this one would then resolve a game with no orders in it - advancing the
    turn and publishing a board nobody ordered.

    The read is inside for the same reason. `_apply_orders` works from what
    `load` put in memory, so asking about a game the resolution is not going to
    resolve would be no better than asking too early.

    Three answers, because two would not do. `None` means the barrier was not
    met, which is another caller having got there first and is the system
    working; `True` and `False` are `resolve`'s own, and `False` is a failure.
    """
    with game.repository.held():
        game.load()
        if not barrier_met(game):
            return None
        return resolve(game)


def wait_for_all_commits(game):
    """Wait until every player still in the game has committed.

    A hint, not an answer. `notify.py` says a signal "is only ever a hint: every
    caller re-checks the condition it actually cares about", and this is the
    caller that did not - it returned, and what it had found was acted on three
    steps later. Waking now sends the caller to ask again where it matters.

    The game is not held here. A barrier waits for as long as a player takes to
    decide, and a game held across that would be stopped rather than protected.
    """
    print("wait for player commit")
    awaited = _awaited_players(game)
    # the waiter is opened before the first check, so a commit signalled from
    # here on is buffered rather than lost, and one that arrived earlier is
    # found by the check itself
    turn_number = game.getTurnNumber()
    with game.notifier.waiter('server') as waiter:
        while not awaited.issubset(
                set(game.repository.committed_players(turn_number))):
            waiter.wait()


def wait_for_turn(game):
    """Wait until the server has consumed this player's orders."""
    with game.notifier.waiter(game.player_number) as waiter:
        while game.repository.has_orders(game.player_number):
            waiter.wait()
