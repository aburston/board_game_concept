"""Registering, signing in, passwords, and tokens, over HTTP.

The routes that are about an account rather than about a game. They are the
only ones that answer without a token - registering and signing in cannot
require one - and the password-change route is the only thing an account
that must change its password may reach.

A browser gets its token in an `HttpOnly` cookie; a command-line role gets the
same string in the response and sends it as a bearer header. One token, two
carriers, and one `sessions` row behind both.
"""

from flask import jsonify, request

from ..service import accounts
from ..service.errors import AccountError
from .auth import (SESSION_COOKIE, error_response, presented_token,
                   require_account, store)


def register_routes(app):
    """Mount the account routes on this app."""

    @app.post('/accounts')
    def register():
        body = request.get_json(silent=True) or {}
        try:
            account = accounts.register(store(), body.get('username'),
                                        body.get('password'))
        except AccountError as error:
            return error_response(error)
        return jsonify({'username': account.username,
                        'kind': account.kind}), 201

    @app.post('/sessions')
    def sign_in():
        body = request.get_json(silent=True) or {}
        try:
            account, token = accounts.authenticate(
                store(), body.get('username'), body.get('password'))
        except AccountError as error:
            return error_response(error)
        payload = {
            'username': account.username,
            'kind': account.kind,
            # the caller is told it must change its password rather than
            # being refused the token: the token is what it changes it with
            'must_change_password': account.must_change,
            'token': token,
        }
        response = jsonify(payload)
        response.set_cookie(SESSION_COOKIE, token, httponly=True,
                            samesite='Lax')
        return response

    @app.delete('/sessions/current')
    def sign_out():
        accounts.end_token(store(), presented_token())
        response = jsonify({'signed_out': True})
        response.delete_cookie(SESSION_COOKIE)
        return response

    @app.get('/accounts/current')
    def whoami():
        try:
            account = require_account()
        except AccountError as error:
            return error_response(error)
        return jsonify({
            'username': account.username,
            'kind': account.kind,
            'must_change_password': account.must_change,
            'seats': [{'gameno': gameno, 'number': number}
                      for gameno, number
                      in store().seats_of_account(account.account_id)],
        })

    @app.post('/accounts/current/password')
    def change_own_password():
        # deliberately not behind `authenticated`: an account that must
        # change its password reaches this and nothing else
        body = request.get_json(silent=True) or {}
        try:
            account = require_account()
            accounts.change_password(store(), account,
                                     body.get('current'), body.get('new'))
        except AccountError as error:
            return error_response(error)
        return jsonify({'changed': True})

    @app.post('/accounts/<username>/password')
    def reset_password(username):
        body = request.get_json(silent=True) or {}
        try:
            account = require_account()
            accounts.require_usable(account)
            accounts.reset_password(store(), account, username,
                                    body.get('new'))
        except AccountError as error:
            return error_response(error)
        return jsonify({'changed': True, 'username': username})

    @app.post('/tokens')
    def mint():
        body = request.get_json(silent=True) or {}
        try:
            account = require_account()
            accounts.require_usable(account)
            token = accounts.mint_token(store(), account,
                                        label=body.get('label'))
        except AccountError as error:
            return error_response(error)
        return jsonify({'token': token, 'label': body.get('label')}), 201

    @app.get('/tokens')
    def list_tokens():
        try:
            account = require_account()
            accounts.require_usable(account)
        except AccountError as error:
            return error_response(error)
        held = store().sessions_of(account.account_id)
        # the token strings themselves are not listed back: a listing that
        # handed them out would make reading it as good as holding them
        return jsonify({'tokens': [
            {'label': row['label'], 'created_at': row['created_at'],
             'expires_at': row['expires_at']} for row in held]})

    @app.delete('/tokens/<token>')
    def revoke(token):
        try:
            account = require_account()
            accounts.require_usable(account)
        except AccountError as error:
            return error_response(error)
        held = store().read_session(token)
        if held is None or held.account_id != account.account_id:
            return jsonify({'error': 'no such token'}), 404
        accounts.end_token(store(), token)
        return jsonify({'revoked': True})
