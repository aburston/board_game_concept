"""Which games exist, and making one, over HTTP.

The two things a lobby needs that the per-game API could not answer. Both are
behind the guard `accounts-and-membership` put in front of everything else:
any authenticated account may list, and only the administrator may create.

The listing names each game's seats and who holds them, which is what a person
looking for a game to join is actually looking for. It carries nothing
private: a username and a number, and nothing about anybody's army.
"""

from flask import jsonify, request

from ..service import accounts
from ..service import registry as registry_service
from ..service.errors import AccountError, GameError, NotAuthorised
from .auth import authenticated, error_response, require_account, store


def register_routes(app):
    """Mount the registry routes on this app."""

    def _base_path():
        return app.config['BASE_PATH']

    def _backend():
        return app.config['BACKEND']

    @app.get('/games')
    @authenticated
    def list_games():
        records = registry_service.games(_backend(), _base_path())
        return jsonify({'games': [_with_seats(record) for record in records]})

    @app.post('/games')
    def create_game():
        try:
            account = require_account()
            # the password gate first: an account that must change its
            # password may do nothing else, administrator or not
            accounts.require_usable(account)
            if not account.is_administrator():
                raise NotAuthorised(
                    'only the administrator may create a game')
        except AccountError as error:
            return error_response(error)

        body = request.get_json(silent=True) or {}
        gameno = str(body.get('gameno') or '').strip()
        try:
            record = registry_service.create(gameno, _backend(), _base_path())
        except GameError as error:
            # a number already in use is a conflict rather than a bad request:
            # nothing about what was asked was malformed
            status = 409 if 'already exists' in str(error) else 400
            return jsonify({'error': str(error)}), status
        return jsonify(_with_seats(record)), 201

    def _with_seats(record):
        """One game's record, with who holds each of its seats.

        The seats come from the account store and the numbers from the game,
        so a seat is only ever one the administrator registered.
        """
        held = store().seats_of_game(str(record['gameno']))
        seats = []
        for number in record['players']:
            account_id = held.get(number)
            holder = (store().read_account(account_id)
                      if account_id is not None else None)
            seats.append({'number': number,
                          'held_by': holder.username if holder else None,
                          'open': holder is None})
        described = dict(record)
        described['seats'] = seats
        described['open_seats'] = sum(1 for seat in seats if seat['open'])
        return described
