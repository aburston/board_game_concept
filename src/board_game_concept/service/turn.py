"""Turning the crank: publishing orders, resolving turns, and waiting.

The commit barrier lives here rather than in storage, because "every player has
committed" is a rule about the game and not a fact about files. The repository
is asked who has committed; what that means is decided here.
"""

import hashlib
import json
import sys

from ..domain import UnitType, budget, placement
from ..domain.events import players_in
from ..storage.serialise import units_document
from . import identity
from . import turn_feed
from .errors import GameError

# the most turns a game is resolved for. Controllers are deterministic, so a
# game whose whole state repeats can never change and is stopped where it
# repeats; this is the backstop for one that wanders without repeating.
# Nobody waits for a turn any more, so it can be generous
TURN_CAP = 500

# how many turns may pass with nothing happening - no unit changing square,
# no blow landed, nothing destroyed, no flag fallen - before a game stops
# undecided. A sleeping unit's countdown and a thinking unit's meter keep a
# static board from ever repeating its whole state; a board nobody has moved
# or struck on for this long is one nobody is watching
QUIET_CAP = 50

# the event kinds that count as something happening
HAPPENINGS = frozenset(('moved', 'attacked', 'destroyed', 'flag_fallen'))


def _types_without_objects(player):
    """A player's types as they are written down, without the live objects.

    A copy: the session goes on resolving turns with the same players, and
    stripping the objects from the records it holds left the next turn with
    types it could not deploy from.
    """
    return {type_name: {key: value for key, value in record.items()
                        if key != 'obj'}
            for type_name, record in player['types'].items()}


def setup_refusal(game):
    """Why this player's setup may not be committed yet, or None if it may.

    Only a setup is held to this: a player committing a later turn has a flag
    already, fixed by the setup they committed, so this asks only of a session
    that still has a setup to commit.
    """
    if not game.getNewGame() or not identity.is_player(game.player_number):
        return None
    board = game.getBoard()
    if board is None:
        return None                 # the board is refused above, and first
    if board.flagOf(game.player_number) is None:
        return ("one of your units must carry your flag before this setup "
                "can be committed - `set flag <unit>` designates it")
    return None


def _squares_committed_by_others(repository, number):
    """The squares other players' committed setups already deploy onto.

    Read from the repository rather than from this session, which holds only
    its own view and cannot see where anybody else is. A published unit that
    is a deployment claims its square; a move claims nothing, because the unit
    is already standing somewhere the board knows about.
    """
    claimed = {}
    for other in repository.player_numbers():
        if int(other) == int(number):
            continue
        orders = repository.read_orders(other)
        if not orders:
            continue
        units = orders.get('units')
        # a player holding no units publishes "units: None", which reads back
        # as the string rather than as null
        if not units or units == 'None':
            continue
        for unit in units:
            try:
                square = (int(unit['x']), int(unit['y']))
            except (KeyError, TypeError, ValueError):
                continue
            claimed.setdefault(square, int(other))
    return claimed


def clash_refusal(game):
    """Why this setup may not be committed onto the squares it wants.

    A player cannot see anybody else's units while they are setting up, so two
    of them can choose one square without knowing it. This used to be found
    only when the turn resolved, and both deployments were refused: each
    player lost the unit, was told afterwards, and could do nothing about it,
    because their setup was committed and closed.

    Refusing the commit leaves the setup open instead - nothing published,
    nothing marked committed - so the player moves the unit and commits again.
    The setup committed first keeps the square, which is a change from "both
    are refused, so neither is favoured by the order they were read in": it is
    the price of the refused player being able to act on it.

    Only a setup is checked. Deployments happen nowhere else - `deploy_unit`
    refuses once setup is closed - so on any later turn there is nothing here
    to find.
    """
    if not game.getNewGame() or not identity.is_player(game.player_number):
        return None
    board = game.getBoard()
    if board is None:
        return None
    taken = _squares_committed_by_others(game.repository, game.player_number)
    if not taken:
        return None
    # every unit of this player's claims its square. During setup nothing has
    # been resolved by the server, so all of them are deployments waiting to
    # be placed - and the state is no guide, because a client settles its own
    # deployment onto its own board at once so that its owner can see it,
    # which leaves it holding `NOP` rather than `INITIAL`
    for unit in board.units:
        if unit.player is None or unit.player.number != game.player_number:
            continue
        if unit.destroyed:
            continue
        square = (int(unit.x), int(unit.y))
        if square in taken:
            return (f"{unit.name} is deployed at {square}, which another "
                    "player has already committed a unit to - deploy it "
                    "somewhere else and commit again")
    return None


def publish(game):
    """Publish this player's orders and wait for the turn to be resolved."""
    if game.getSizeX() <= 1 or game.getSizeY() <= 1:
        print(f"the board size is too small ({game.getSizeX()}, "
              f"{game.getSizeY()})")
        return False

    # raised rather than answered False, because unlike a board too small to
    # play on this has a reason worth reading, and every client already
    # reports what a refused command says
    refusal = setup_refusal(game)
    if refusal is not None:
        raise GameError(refusal)

    number = game.player_number
    repository = game.repository
    # held for writing: publishing an order file and resolving a turn, which
    # deletes every order file, must not overlap
    with repository.held():
        # asked under the same lock as the writes it guards, and before the
        # first of them: two players committing at the same moment are
        # serialised, so the second reads what the first wrote and is refused
        # rather than both landing on one square. A refusal here leaves the
        # setup exactly as it was, to be fixed and committed again
        clash = clash_refusal(game)
        if clash is not None:
            raise GameError(clash)
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

    Every reason a deployment can be refused before it is even attempted is
    decided here, against the board as the turn began: a square that is not
    the player's to deploy in, two players asking for one square, and an owner
    whose points will not pay for it. Judged up front rather than as the loop
    reaches each order, so that what one player is refused cannot depend on
    how far through the list the loop happens to be.

    Keyed by `(player, unit name)`, which is what the loop has in hand.
    """
    refusals = {}
    contended = _contended_squares(game, orders)
    numbers = list(game.players.keys())
    standing = []
    for p_number, unit in orders:
        if not _is_deployment(game, p_number, unit):
            continue
        square = (int(unit['x']), int(unit['y']))
        # where this player may deploy at all. Asked here as well as at the
        # client because an order file is written by hand or loaded from disk
        # and never passed through one. A game that is not two-player allows
        # the whole board, so this refuses nothing it did not refuse before
        outside = placement.refusal(
            p_number, numbers, square[0], square[1],
            game.board.size_x, game.board.size_y)
        if outside is not None:
            refusals[(p_number, str(unit['name']))] = outside
            continue
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
                _carry_flag(game, owner, name, unit)
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
                    _carry_flag(game, owner, name, unit)
                except AssertionError as e:
                    reject(p_number, unit, e)
        else:
            # an order the server cannot make sense of is refused, rather
            # than taking the turn down with it
            reject(p_number, unit, f"invalid unit state {str(state)}")


def has_started(game):
    """Whether the game has begun: whether a player's setup has been resolved.

    The administrator's commit that ends setup is resolved like a turn, and at
    that point no player has committed a setup of their own. Judging
    elimination there would declare every player out before the game had
    started.

    This used to ask whether any unit had reached the board, which is the same
    question on every turn but one. A first turn in which *every* deployment
    was refused - two armies deployed onto the same squares, so both were
    refused for it - left the board empty and answered "not started": nobody
    was eliminated and nothing was decided, while setup was over and no more
    units could be added. The game could then be neither played nor finished,
    and there was nothing anybody could do about it.

    A commit marker outlives the turn it was made for - it is also what tells
    a player their setup is over - so this is durable, and a game read back
    from either backend answers it as it answered when the turn resolved.
    """
    return bool(game.board.units) or bool(game.repository.committed_players())


def eliminated_players(game):
    """The players holding no unit that could ever act again.

    What counts is whether a unit has a future, not what it happens to hold
    this turn. A unit at zero energy used to be finished, because energy never
    came back, and not counting it was the honest reading; now every unit
    standing on the board recovers energy each turn (R3.9), so being at zero
    is a bad afternoon rather than a death, and judging a player on it would
    decide games on the timing of a snapshot.

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
        # a flag that is not standing puts its player out whatever else they
        # hold: what keeps a player in the game is something that can act
        # *and* a flag still standing. Derived from the board like the clause
        # beside it, so a game restored from storage answers what it answered
        # before.
        #
        # Not standing covers a carrier that has been destroyed and one that
        # never arrived. A setup is refused unless a unit carries the flag,
        # but a deployment can still be refused as the turn resolves - a
        # contested square, or a budget that will not pay - and a player left
        # with an army and no flag would be the one player the flag could
        # never be taken from
        if game.board.flagOf(number) is None or game.board.flagFallen(number):
            out.append(number)
            continue
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

        # setup ends with a resolution of its own, before anything is on the board.
        # That is not a turn of the game and is not numbered as one
        turn_number = game.getTurnNumber() + 1 if has_started(game) else 0

        # run every controller, resolve all moves and end the turn
        events = game.board.commit(turn=turn_number)
        _report_turn(game, events, reject)

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

        # where every flag is, for every player to read whatever they have
        # made contact with. Written beside the authoritative record because
        # that is what it is read off: the square and the owner, and nothing
        # about the unit standing on it
        repository.write_flags(_flags_document(game))

        # the authoritative record, and then what each player is entitled to see
        repository.write_units(units_document(game.board, turn=turn_number))
        views = {}
        for number, player in game.players.items():
            views[number] = units_document(game.board, player['obj'],
                                           turn=turn_number)
            repository.write_view(number, views[number])

        # what the turn did, and what each seat may be told it did. Written
        # here rather than when it is read, because the board this names is
        # the board the turn was resolved on: a unit destroyed this turn is
        # still standing in it, and is what tells a seat the fight was its own
        feed = turn_feed.entries(events)
        repository.write_turn_events(turn_number, feed)
        for number, player in game.players.items():
            repository.write_events(number, turn_number,
                                    turn_feed.for_seat(feed, number))
            _remember_types(repository, number, views[number], turn_number)

        # the record of the turn, for the replay: the board and the units as
        # the turn left them, the flags, what happened, what every army
        # knows and what every controller did. Kept for every turn, so the
        # game can be read from its first turn to its last
        repository.write_turn(turn_number, turn_record(
            game, turn_number, feed, progress))

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


def turn_record(game, turn_number, feed, progress):
    """One turn as the record the replay reads."""
    board = game.board
    return {
        'turn': turn_number,
        'board': {'size_x': board.size_x, 'size_y': board.size_y},
        'units': units_document(board, turn=turn_number)['units'],
        'flags': _flags_document(game),
        'events': feed,
        'maps': {str(number): army_map.record()
                 for number, army_map in sorted(board.maps.items())},
        'traces': list(board.traces),
        'progress': dict(progress),
    }


def state_record(game):
    """The whole state of the game as plain data, for telling whether it has
    been here before: every unit's square, health, energy, memory, meter,
    sleep and inbox, and every army's map.

    Not the turn number, which is the one thing that always differs - and
    not the stamp on a square a friendly unit is standing on, which is the
    turn number again under another name: a unit that stands still restamps
    its square every turn and would make a game that never changes look as
    though it did. A program that reads the turn and acts on a particular
    one can still make a repeated state play on differently; the cap is the
    backstop for that.
    """
    units = units_document(game.board)['units']
    for unit in units:
        unit.pop('id', None)
    standing = {}
    for unit in game.board.units:
        if unit.on_board and not unit.destroyed and unit.player is not None:
            standing.setdefault(unit.player.number, set()).add((unit.x, unit.y))
    maps = {}
    for number, army_map in sorted(game.board.maps.items()):
        record = army_map.record()
        held = standing.get(number, set())
        record['visited'] = [[x, y, turn] for x, y, turn in record['visited']
                             if (x, y) not in held]
        maps[str(number)] = record
    return {
        'units': units,
        'maps': maps,
        'eliminated': sorted(game.getEliminated()),
    }


def state_hash(game):
    """A hash of `state_record`, over a canonical serialisation."""
    text = json.dumps(state_record(game), sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def _stop_undecided(game, reason, since=None):
    """Record that the game stopped without a decision, and why."""
    turn_number = game.getTurnNumber()
    outcome = {'decided': False, 'winner': None, 'turn': turn_number,
               'reason': reason}
    if since is not None:
        outcome['since'] = since
    progress = {'turn': turn_number, 'eliminated': game.getEliminated(),
                'outcome': outcome}
    game.repository.write_progress(progress)
    game.setProgress(progress)
    # the last turn's record carries how the game ended
    record = game.repository.read_turn(turn_number)
    if record is not None:
        record['progress'] = dict(progress)
        game.repository.write_turn(turn_number, record)


def resolve_game(game):
    """Resolve every turn of the game, one after another, to its end.

    Called when the last setup is committed, and nobody is waited for from
    here on: every order comes from a unit's controller. Stops when the game
    is decided, when its whole state repeats - the controllers are
    deterministic, so nothing can ever change again - when nothing has
    happened for `QUIET_CAP` turns, or at `TURN_CAP`. Whichever comes first
    ends the game. Each turn is recorded as it goes, so a game is a record
    to be read.

    Answers what `resolve` answers: `False` if a turn could not be resolved,
    `True` once the game has been played to its end.
    """
    seen = {}
    eventful = None
    while True:
        if game.getOutcome() is not None:
            return True
        if not resolve(game):
            return False
        if game.getOutcome() is not None:
            return True
        turn_number = game.getTurnNumber()
        if turn_number == 0:
            # the administrator's setup resolution: the game has not begun
            return True
        key = state_hash(game)
        if key in seen:
            _stop_undecided(game, 'repeated', since=seen[key])
            return True
        seen[key] = turn_number
        # the turn the armies were placed counts as something happening: it
        # is the turn the quiet is measured from when nothing ever moves
        if eventful is None or _something_happened(game, turn_number):
            eventful = turn_number
        elif turn_number - eventful >= QUIET_CAP:
            _stop_undecided(game, 'quiet', since=eventful)
            return True
        if turn_number >= TURN_CAP:
            _stop_undecided(game, 'cap')
            return True
        if not game.players or not game.repository.committed_players():
            return True


def _something_happened(game, turn_number):
    """Whether this turn's record holds an event that counts as something
    happening: a unit changing square, a blow, a destruction, a fallen flag.
    Thinking, sleeping and resting are not among them."""
    record = game.repository.read_turn(turn_number) or {}
    return any((entry or {}).get('kind') in HAPPENINGS
               for entry in record.get('events') or [])


def _carry_flag(game, owner, name, order):
    """Give a unit just deployed the flag its owner designated it with.

    A player designates during setup and publishes their army as orders, so
    the designation arrives with the order that deploys the unit - it is not
    a second thing to be told about, and a deployment that lost it would put
    a player in a game they could not lose.
    """
    if not order['flag']:
        return
    deployed = game.board.findUnit(name, owner)
    if deployed is not None:
        deployed.flag = True


def _flags_document(game):
    """Where each flag is, as the record every player may read.

    Three fields and no more: the player it belongs to, the square it is on,
    and whether it is still standing. A fallen flag is on no square - naming
    the square it fell on would be a position its owner no longer holds, told
    to everybody for ever.

    Every player in a game that has begun is named here, whether or not the
    board holds a carrier for them. A carrier can be refused as the turn
    resolves - a contested square, or a budget that will not pay - and a
    player whose flag simply never appeared is as out as one whose flag fell;
    saying nothing about them would leave them the only player who could not
    be told so.
    """
    carriers = game.board.flagBearers()
    published = []
    for number in sorted(game.players):
        carrier = carriers.get(number)
        if carrier is None and not has_started(game):
            # setup is being resolved and nobody has deployed anything yet:
            # every flag is still to come rather than missing
            continue
        standing = (carrier is not None and carrier.on_board
                    and not carrier.destroyed)
        published.append({
            'player': number,
            'x': carrier.x if standing else None,
            'y': carrier.y if standing else None,
            'standing': standing,
        })
    return published


def _remember_types(repository, number, view, turn_number):
    """Add the enemy designs this seat met this turn to what it has met.

    A sighting lasts one turn: an enemy nobody touched is off your board and
    out of your list of types by the next resolution, which is `visibility`
    working. What that enemy was built with is a different thing from where
    it is - it is what you learned by fighting it, and a player who has met a
    unit and cannot say what it was built with is being asked to keep notes
    on paper.

    Only the design is kept. No square, no unit name, no count: nothing here
    says where anybody is, then or now.
    """
    known = {(entry['owner'], entry['name']): dict(entry)
             for entry in repository.read_known_types(number)}
    for unit in view.get('units') or []:
        owner = unit['player']
        if owner == number:
            continue
        seen = known.get((owner, unit['type']))
        if seen is None:
            known[(owner, unit['type'])] = {
                'owner': owner,
                'name': unit['type'],
                'symbol': unit['symbol'],
                # the design, not the state the unit was in when it was met:
                # a wounded enemy is not a weaker type
                'attack': unit['type_attack'],
                'health': unit['type_health'],
                'energy': unit['type_energy'],
                'first_seen': turn_number,
                'last_seen': turn_number,
            }
        else:
            seen['last_seen'] = turn_number
    repository.write_known_types(
        number, sorted(known.values(),
                       key=lambda entry: (entry.get('first_seen') or 0,
                                          entry['owner'], entry['name'])))


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
            for number in players_in(event.detail):
                unit = _owned(game, number, event.detail['unit'])
                if unit is not None:
                    reject(number, order_for(unit), event.detail['reason'])
        elif event.kind == 'undecided':
            where = f"({event.detail['x']}, {event.detail['y']})"
            # whose unit each survivor is comes from the event, not from the
            # name: two players may both hold a `pawn1`, and matching by
            # name told each about the other's contests
            for owner, name in _survivors(event.detail):
                unit = _owned(game, owner, name)
                if unit is not None:
                    reject(owner, order_for(unit),
                           f"the contest at {where} was undecided")


def _owned(game, number, name):
    """The unit of that name that this player owns, or None."""
    player = game.players.get(number)
    if player is None:
        return None
    return game.board.findUnit(name, player['obj'])


def _survivors(detail):
    """The `(owner, name)` pairs an undecided contest names."""
    pairs = []
    for item in str(detail.get('survivors') or '').split(','):
        if ':' not in item:
            continue
        owner, name = item.split(':', 1)
        if owner:
            pairs.append((int(owner), name))
    return pairs


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
            # a hand-written file may say which unit carries the flag, and
            # one that says nothing carries none. Defaulted here with the
            # other fields a person writing a file need not think about,
            # rather than everywhere the document is read
            'flag': unit.get('flag', False),
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

    A game that is over has no open turn, so its barrier is never met: the
    setup commit was the last thing anyone was waited for, and a caller woken
    after the resolution finds nothing to resolve.
    """
    if game.getOutcome() is not None:
        return False
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
        # the barrier is met once and for all: every setup is committed, and
        # the game is played to its end from here, nobody waited for
        return resolve_game(game)


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
