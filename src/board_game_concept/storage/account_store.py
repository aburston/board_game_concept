"""Where accounts, the seats they hold, and their tokens live.

The port, in the shape `storage/repository.py` has: it reads and writes and
holds no rules. It does not know that `admin` is reserved, that a password
must be eight characters, or which numbers an account may act as - only how to
put an account somewhere and get it back. `domain/account.py` states the
rules and `service/accounts.py` applies them.

This store is not a game's. Every `GameRepository` is chosen per game and
built per request, under `games/_<gameno>/`; an account outlives every game it
plays in and there is nowhere in that tree for it. So this is one store per
server, beside the games rather than inside one.

There is one implementation and it is SQLite. The YAML backend exists so an
operator can `cat` a game, and a password hash is the one thing in this system
that should not be sitting in a readable file.
"""


class AccountStore:
    """The operations the account store has to offer.

    Subclasses implement all of them. This class says what the set is and
    fails loudly rather than silently when one is missing.
    """

    # --- the store itself

    def held(self, read=False):
        """Hold the store while the caller reads or writes it.

        Used as a context manager, and meaning what `GameRepository.held`
        means: a writer excludes every other holder, readers may hold it
        together.
        """
        raise NotImplementedError

    def ensure(self):
        """Make whatever the store needs to exist, exist.

        Including the two system accounts. A store that has just been created
        holds `admin` and `observer`, each needing its password changed; a
        store that already holds them is left exactly as it is, so that a
        restart never resets a password somebody has changed.
        """
        raise NotImplementedError

    # --- accounts

    def create_account(self, username, password_hash, kind, must_change=False):
        """Record a new account and return it, with its id.

        Refuses a username already held, compared by the case-folded form.
        """
        raise NotImplementedError

    def read_account(self, account_id):
        """The account with this id, or None."""
        raise NotImplementedError

    def read_account_by_name(self, username):
        """The account known by this name, or None.

        Looked up by the case-folded form, so that `Ada` finds `ada`.
        """
        raise NotImplementedError

    def set_password(self, account_id, password_hash):
        """Replace this account's password hash and clear `must_change`.

        The two are one operation because they are one fact: an account whose
        password has been set is an account that no longer needs setting.
        """
        raise NotImplementedError

    def accounts(self):
        """Every account, for a caller entitled to the whole list."""
        raise NotImplementedError

    # --- tokens

    def create_session(self, account_id, token, expires_at, label=None):
        """Record a token that is to be accepted until `expires_at`."""
        raise NotImplementedError

    def read_session(self, token, now=None):
        """The account this token identifies, or None.

        None where the token was never issued, has been ended, or is past the
        time it is accepted until. A token past its time is not an error to
        the caller and is not distinguished from one that never existed.
        """
        raise NotImplementedError

    def delete_session(self, token):
        """End one token."""
        raise NotImplementedError

    def delete_sessions_of(self, account_id):
        """End every token of one account."""
        raise NotImplementedError

    def sessions_of(self, account_id):
        """Every token currently held by one account."""
        raise NotImplementedError

    # --- seats

    def claim_seat(self, gameno, number, account_id):
        """Record that this account holds this seat of this game.

        Refuses a seat that is already held. The refusal comes from the store
        rather than from a read followed by a write, so that two claims
        arriving together cannot both succeed.
        """
        raise NotImplementedError

    def release_seat(self, gameno, number):
        """Give up a seat, leaving it unclaimed."""
        raise NotImplementedError

    def read_membership(self, gameno, number):
        """The id of the account holding this seat, or None."""
        raise NotImplementedError

    def holds_seat(self, gameno, number, account_id):
        """Whether this account holds this seat of this game."""
        raise NotImplementedError

    def seats_of_game(self, gameno):
        """Every held seat of one game, as {number: account_id}."""
        raise NotImplementedError

    def seats_of_account(self, account_id):
        """Every seat one account holds, as a list of (gameno, number)."""
        raise NotImplementedError
