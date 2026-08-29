"""Playing whole games against the service layer.

The CLI surface suites drive the roles as subprocesses, which is what the
command surface is checked against. This drives the same service layer those
roles call, so a test can play a game for as many turns as it likes without
paying for a process per session.

A session here is exactly what a role holds: `Game(repository, number)`, loaded,
acted on through `service.games`, and committed. Nothing is reached around.
"""

import os

from board_game_concept import Game, YamlGameRepository
from board_game_concept.service import games
from board_game_concept.service.commands import (
    AddPlayer, AddType, AddUnit, Move, SetBoard, SetFlag)
from board_game_concept.storage.serialise import units_document

# "the first unit deployed", told apart from `None`, which means no flag at all
_FIRST = object()
from board_game_concept.storage.sqlite_repository import SqliteGameRepository


# environment override for the harness's default backend. A test that pins
# itself to a backend still overrides this via `backend=`
BACKEND_ENV = 'BOARD_GAME_BACKEND'
DEFAULT_BACKEND = os.environ.get(BACKEND_ENV, 'yaml')


def make_repository(backend, gameno, base_path):
    if backend == 'sqlite':
        return SqliteGameRepository(gameno, base_path=base_path)
    if backend == 'yaml':
        return YamlGameRepository(gameno, base_path=base_path)
    raise ValueError(f"unknown backend: {backend}")


class GameHarness:
    """One game, and a way to open a session on it as any role."""

    def __init__(self, base_path, gameno='harness', backend=None):
        self.base_path = str(base_path)
        self.gameno = gameno
        self.backend = backend or DEFAULT_BACKEND

    def repository(self):
        return make_repository(self.backend, self.gameno, self.base_path)

    def session(self, player_number):
        """A loaded session for a player, or for the administrator as 0."""
        session = Game(self.repository(), player_number)
        session.load()
        return session

    # --- setting a game up

    def create(self, size_x, size_y, player_numbers, budget=None):
        """Size the board and register the players, as the administrator does.

        A player is named as a number, or as a `(number, budget)` pair where
        the test cares what that player has to spend. `budget` sets it for
        every player named as a bare number - which is what a test about some
        other rule wants, so that a fixture built when deploying was free is
        not quietly turned into a test of the point budget.
        """
        server = self.session(0)
        games.set_board_size(server, SetBoard(size_x=size_x, size_y=size_y))
        for entry in player_numbers:
            if isinstance(entry, tuple):
                number, player_budget = entry
            else:
                number, player_budget = entry, budget
            if player_budget is None:
                games.add_player(server, AddPlayer(number=number))
            else:
                games.add_player(server,
                                 AddPlayer(number=number,
                                           budget=player_budget))
        assert server.serverSave()
        return server

    def deploy(self, player_number, types, units, flag=_FIRST, commit=True):
        """Define types, deploy units and carry the flag, as a player does.

        `types` are `(name, symbol, attack, health, energy)` tuples and `units`
        are `(type_name, unit_name, x, y)`.

        A setup is refused unless one unit carries the player's flag, so the
        first unit deployed carries it unless the test says otherwise: a test
        about some other rule should not have to know about flags, and one
        about flags names the carrier it wants. `flag=None` commits without
        one, which the service layer refuses for a player - it is there for a
        test that wants to see that refusal.
        """
        client = self.session(player_number)
        for name, symbol, attack, health, energy in types:
            games.define_type(client, AddType(
                name=name, symbol=symbol, attack=attack, health=health,
                energy=energy))
        for type_name, unit_name, x, y in units:
            games.deploy_unit(client, AddUnit(
                type_name=type_name, name=unit_name, x=x, y=y))
        carrier = (units[0][1] if units else None) if flag is _FIRST else flag
        if carrier is not None:
            games.perform(client, SetFlag(unit=carrier))
        # a player who deployed nothing has nothing to carry the flag, so
        # their setup cannot be committed - `commit=False` is how a test sets
        # up the player who never turns up
        if commit:
            assert client.clientSave()
        return client

    def publish_setup(self, player_number, types, units, flag=_FIRST):
        """Publish a setup straight to the repository, past the commit.

        A commit refuses a setup that deploys onto a square another player has
        already committed a unit to, so a clash cannot be got through the
        front door any more. What can still reach the server is a loaded
        player file, or orders written by something that is not a client -
        and that is what the resolution's own refusals exist for. This is
        that route: the same writes `publish` makes, without the checks it
        makes first.
        """
        client = self.session(player_number)
        for name, symbol, attack, health, energy in types:
            games.define_type(client, AddType(
                name=name, symbol=symbol, attack=attack, health=health,
                energy=energy))
        for type_name, unit_name, x, y in units:
            games.deploy_unit(client, AddUnit(
                type_name=type_name, name=unit_name, x=x, y=y))
        carrier = (units[0][1] if units else None) if flag is _FIRST else flag
        if carrier is not None:
            games.perform(client, SetFlag(unit=carrier))

        repository = self.repository()
        player = client.getPlayers()[player_number]
        repository.write_player(
            player_number,
            {name: {key: value for key, value in design.items()
                    if key != 'obj'}
             for name, design in player['types'].items()},
            client.getPlayerObj(player_number).budget)
        repository.write_orders(
            player_number,
            units_document(client.getBoard(),
                           client.getPlayerObj(player_number),
                           in_play_only=True))
        repository.mark_committed(player_number, client.getTurnNumber())
        return client

    # --- playing it

    def order(self, player_number, orders):
        """Order this player's units and commit. `orders` are `(unit, direction)`."""
        client = self.session(player_number)
        for unit_name, direction in orders:
            games.order_move(client, Move(unit=unit_name, direction=direction))
        assert client.clientSave()
        return client

    def resolve(self):
        """Resolve the turn, as the server does once everyone has committed."""
        server = self.session(0)
        assert server.serverSave()
        return server

    def turn(self, orders_by_player):
        """One whole turn: every player orders and commits, then the server resolves.

        `orders_by_player` maps a player number to their `(unit, direction)`
        orders; a player with none still commits, as they must.
        """
        for player_number, orders in orders_by_player.items():
            self.order(player_number, orders)
        return self.resolve()

    # --- reading it back

    def units(self, player_number=0):
        """The units a session of this role holds, keyed by name."""
        session = self.session(player_number)
        board = session.getBoard()
        if board is None:
            return {}
        return {unit.name: unit for unit in board.units}

    def rejections(self, player_number):
        return self.session(player_number).getRejected()
