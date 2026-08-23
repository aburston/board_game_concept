"""Playing whole games against the service layer.

The CLI surface suites drive the roles as subprocesses, which is what the
command surface is checked against. This drives the same service layer those
roles call, so a test can play a game for as many turns as it likes without
paying for a process per session.

A session here is exactly what a role holds: `Game(repository, number)`, loaded,
acted on through `service.games`, and committed. Nothing is reached around.
"""

from board_game_concept import Game, YamlGameRepository
from board_game_concept.service import games
from board_game_concept.service.commands import (AddPlayer, AddType, AddUnit,
                                                 Move, SetBoard)


class GameHarness:
    """One game, and a way to open a session on it as any role."""

    def __init__(self, base_path, gameno='harness'):
        self.base_path = str(base_path)
        self.gameno = gameno

    def repository(self):
        return YamlGameRepository(self.gameno, self.base_path)

    def session(self, player_number):
        """A loaded session for a player, or for the administrator as 0."""
        session = Game(self.repository(), player_number)
        session.load()
        return session

    # --- setting a game up

    def create(self, size_x, size_y, player_numbers):
        """Size the board and register the players, as the administrator does."""
        server = self.session(0)
        games.set_board_size(server, SetBoard(size_x=size_x, size_y=size_y))
        for number in player_numbers:
            games.add_player(server, AddPlayer(number=number))
        assert server.serverSave()
        return server

    def deploy(self, player_number, types, units):
        """Define types and deploy units, as a player does during setup.

        `types` are `(name, symbol, attack, health, energy)` tuples and `units`
        are `(type_name, unit_name, x, y)`.
        """
        client = self.session(player_number)
        for name, symbol, attack, health, energy in types:
            games.define_type(client, AddType(
                name=name, symbol=symbol, attack=attack, health=health,
                energy=energy))
        for type_name, unit_name, x, y in units:
            games.deploy_unit(client, AddUnit(
                type_name=type_name, name=unit_name, x=x, y=y))
        assert client.clientSave()
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
