"""Who is asking, as opposed to what they are entitled to.

An account is one person or one program that plays. It is not a player
number: a number says what a session may see and do within one game, and an
account says who is asking, across every game. `service/identity.py` answers
the first question and has never heard of the second.

The rules a username and a password must satisfy are stated here for the same
reason `Player` states the range of a number: they arrive by more than one
door - registration, the two accounts a new store is created with, and a
password changed while the server runs - and a check at any one of those is a
check the others do not get.

Nothing here stores an account or hashes a password. What a hash is made with
is `storage/`'s to decide, and this module is what can be reasoned about
without a database.
"""


class Kind:
    """What an account is, which decides which numbers it may act as.

    Three, matching the three identities `player-numbering` describes, because
    an account exists to be one of them. The administrator and the observer are
    the numbers of every game and are held by one account each; a player is
    anybody else, and holds seats rather than numbers.
    """

    ADMINISTRATOR = 'admin'
    OBSERVER = 'observer'
    PLAYER = 'player'

    ALL = (ADMINISTRATOR, OBSERVER, PLAYER)


# the two accounts a store is created with, by the names they are known by.
# They are reserved from registration by the same constant that creates them,
# so a name cannot be reserved in one place and free in the other
ADMINISTRATOR_NAME = 'admin'
OBSERVER_NAME = 'observer'

RESERVED = (ADMINISTRATOR_NAME, OBSERVER_NAME)

# the shortest password that may be set. Length is the property that helps; a
# composition rule teaches people to write `Passw0rd!` and is not imposed
MIN_PASSWORD = 8

# the longest username, so that a name cannot be used to fill a column or a
# listing. No shape is required of it beyond not being empty
MAX_USERNAME = 32


def normalise(username):
    """The form of a username two names are compared as.

    Case-insensitively, so that `Admin` is `admin`. Without this a name
    differing only in case registers, and every listing of who holds what
    becomes a place to be deceived.
    """
    if not isinstance(username, str):
        return ''
    return username.strip().casefold()


def username_refusal(username):
    """Why this username may not be registered, or None if it may.

    The one sentence a caller reports, in the shape `domain/budget.py` uses
    for the same job: the rule is stated once and the callers say it rather
    than deciding it.
    """
    if not isinstance(username, str) or not username.strip():
        return 'a username cannot be empty'
    name = username.strip()
    if len(name) > MAX_USERNAME:
        return f'a username cannot be longer than {MAX_USERNAME} characters'
    if any(character.isspace() for character in name):
        return 'a username cannot contain spaces'
    if normalise(name) in RESERVED:
        return f'{name} is a reserved name and cannot be registered'
    return None


def password_refusal(password):
    """Why this password may not be set, or None if it may."""
    if not isinstance(password, str):
        return f'a password must be at least {MIN_PASSWORD} characters'
    if len(password) < MIN_PASSWORD:
        return f'a password must be at least {MIN_PASSWORD} characters'
    return None


class Account:
    """One account: who it is, what kind it is, and whether it may act yet.

    The password is held as whatever `storage/` hashed it into, and this class
    neither makes that hash nor checks against it. `must_change` is what keeps
    an account created with a known password from being used for anything but
    changing it.
    """

    def __init__(self, username, password_hash, kind,
                 must_change=False, account_id=None):
        assert isinstance(username, str) and username.strip(), (
            'a username cannot be empty')
        assert kind in Kind.ALL, f'an account cannot be a {kind}'

        self.username = username.strip()
        self.password_hash = password_hash
        self.kind = kind
        self.must_change = bool(must_change)
        self.account_id = account_id

    @property
    def key(self):
        """The form this account's name is compared and looked up by."""
        return normalise(self.username)

    def is_administrator(self):
        """Whether this account is the administrator of every game."""
        return self.kind == Kind.ADMINISTRATOR

    def is_observer(self):
        """Whether this account is the observer of every game."""
        return self.kind == Kind.OBSERVER

    def __eq__(self, other):
        return (isinstance(other, Account)
                and other.key == self.key
                and other.kind == self.kind)

    def __repr__(self):
        return f'Account({self.username!r}, kind={self.kind!r})'
