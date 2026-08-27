"""Which seats a game holds, and taking or giving up one.

A seat is a player number the administrator registered with `add player`.
Claiming one does not register a player and is not a way around that: the
game's own repository says which numbers exist, and this never writes to it.
"""

from flask import jsonify

from ..cli import session as session_module
from ..service import accounts
from ..service.errors import AccountError, GameDataError
from .auth import authenticated, error_response, require_account, store


def register_routes(app):
    """Mount the seat routes on this app."""

    def _repository(gameno):
        return session_module.make_repository(
            gameno, backend=app.config['BACKEND'],
            base_path=app.config['BASE_PATH'])

    @app.get('/games/<gameno>/seats')
    @authenticated
    def list_seats(gameno):
        """The seats of a game and who holds them.

        Any authenticated account may read it - a seat cannot be found before
        it is held otherwise - and it names no account's private state: a
        username and a budget, and nothing about anybody's army.
        """
        try:
            repository = _repository(gameno)
            numbers = repository.player_numbers()
        except GameDataError as error:
            return jsonify({'error': str(error)}), 404

        held = store().seats_of_game(str(gameno))
        seats = []
        for number in numbers:
            account_id = held.get(number)
            holder = (store().read_account(account_id)
                      if account_id is not None else None)
            seats.append({
                'number': number,
                'held_by': holder.username if holder else None,
                'open': holder is None,
            })
        return jsonify({'gameno': gameno, 'seats': seats})

    @app.post('/games/<gameno>/seats/<int:number>')
    def claim_seat(gameno, number):
        try:
            account = require_account()
            accounts.claim_seat(store(), _repository(gameno), account,
                                str(gameno), number)
        except AccountError as error:
            return error_response(error)
        except GameDataError as error:
            return jsonify({'error': str(error)}), 404
        return jsonify({'gameno': gameno, 'number': number,
                        'held_by': account.username}), 201

    @app.delete('/games/<gameno>/seats/<int:number>')
    def release_seat(gameno, number):
        try:
            account = require_account()
            accounts.release_seat(store(), _repository(gameno), account,
                                  str(gameno), number)
        except AccountError as error:
            return error_response(error)
        except GameDataError as error:
            return jsonify({'error': str(error)}), 404
        return jsonify({'gameno': gameno, 'number': number,
                        'held_by': None})
