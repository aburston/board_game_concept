"""What a new game and a newly registered player start with.

A game used to start empty: no board, no unit types, no units. Everything had
to be invented before anything could be played, and invented well, because the
cost of a type and the reach of a unit are not obvious until you have played a
few games. This module holds what a game starts with instead - a board size, a
catalogue of eight types, and an array of fifteen units built from that
catalogue.

Everything here is a **starting point rather than a fixture**. It is made of
ordinary setup decisions, so a player edits it with the commands they already
have: redefine a type, take a unit back, deploy it somewhere better. Nothing
in it is something a player could not have typed themselves, and nothing here
bypasses a rule - the catalogue is run through `UnitType` and the array is
deployed by `deploy_unit`, so a mistake in these tables is caught by the same
assertions a mistake at the prompt is.

The array is described by **depth from a player's own edge** rather than by
row. Depth 0 is the row at the player's edge and depth 1 the row in front of
it, so one table describes both players and neither the board's size nor which
half a seat holds has to appear in it. Columns are not mirrored, as in chess:
the two arrays are reflections and each player faces their own layout.

Both players hold units of the same names, which the rules allow - a name has
only to be unique within one player's own units - and which nothing above this
needs to tell apart, because an event says whose units it names.

Slow units stand at depth 1 and fast ones at depth 0, which inverts chess. A
unit's reach is its energy divided by its move fare, and a Heavy has five
moves in it while a strike costs five more: deployed at the back of a half it
arrives at the fighting line unable to strike. A Runner has ten moves and
strikes for two. The units that can afford to travel are the ones that can
start further back.
"""

from . import placement
from .unit import UnitType


# the board a created game is given. The administrator can resize it, and
# resize it again, until setup is committed - this is where a board starts,
# not where it has to stay
DEFAULT_SIZE_X = 8
DEFAULT_SIZE_Y = 8


# the eight types every registered player is given, as (name, symbol, attack,
# health, energy). Defining a type spends nothing, so the whole catalogue
# costs a player nothing until they deploy a unit of one of its types.
#
# The Wall and the Scout are here on purpose. Both are designs the rules allow
# and nobody builds - attack 0 with no energy, and attack 0 with energy - and
# a default catalogue is the cheapest way to teach that they exist
CATALOGUE = (
    # not `#`: that is the glyph an empty square is drawn with, and a wall
    # drawn as one is a wall a player cannot see on their own board
    ('Wall',   'W', 0, 10,  0),
    ('Scout',  'o', 0,  2, 12),
    ('Pawn',   'p', 1,  4,  2),
    ('Runner', 'r', 2,  4, 10),
    ('Line',   'L', 3,  6, 12),
    ('Lance',  '!', 8,  2, 10),
    ('Keep',   'K', 1, 10,  5),
    ('Heavy',  'H', 5, 10, 15),
)


# the sixteen units, as (depth, column, type name, unit name). Depth 1 is the
# row in front of the player's own edge and takes the units that cannot afford
# to travel; depth 0 is the edge itself and takes the ones that can, and the
# Keep that carries the flag.
#
# Both rows are **symmetric about the middle of the board**: what stands in
# column x stands in column 7 - x as well. A lopsided army reads as a mistake,
# and there is no reason for one flank to be stronger than the other before
# anybody has moved. That is what puts a pair of Keeps in the middle - eight
# columns leave no middle square for one - and it is why the Lance is in the
# catalogue but not in the opening array: four pairs a row is eight pairs, and
# eight pairs of eight different types come to 268 points
ARRAY = (
    (1, 0, 'Pawn', 'pawn1'),
    (1, 1, 'Pawn', 'pawn2'),
    (1, 2, 'Wall', 'wall1'),
    (1, 3, 'Heavy', 'heavy1'),
    (1, 4, 'Heavy', 'heavy2'),
    (1, 5, 'Wall', 'wall2'),
    (1, 6, 'Pawn', 'pawn3'),
    (1, 7, 'Pawn', 'pawn4'),
    (0, 0, 'Runner', 'runner1'),
    (0, 1, 'Scout', 'scout1'),
    (0, 2, 'Line', 'line1'),
    (0, 3, 'Keep', 'keep1'),
    (0, 4, 'Keep', 'keep2'),
    (0, 5, 'Line', 'line2'),
    (0, 6, 'Scout', 'scout2'),
    (0, 7, 'Runner', 'runner2'),
)


# the unit the flag is set on. The Keeps are the least mobile things in the
# array and stand behind the Heavies, which is where a flag wants to be. There
# are two because the array is symmetric and an eight-wide row has no middle
# square for a single one; the left of the pair carries it, so which does is
# the rules' to say rather than an accident of how a list is held
FLAG_UNIT = 'keep1'


def types():
    """The catalogue, as the records a player's types are held in.

    Built through `UnitType` like any type a player defines, so a statistic
    mistyped in the table above fails here rather than reaching a game that
    cannot be read.
    """
    return {
        name: {
            'name': name,
            'symbol': symbol,
            'attack': attack,
            'health': health,
            'energy': energy,
            'obj': UnitType(name, symbol, attack, health, energy),
        }
        for name, symbol, attack, health, energy in CATALOGUE
    }


def cost():
    """What the array costs to deploy.

    Derived from the tables rather than written down as a number, so the two
    cannot come apart: a type made dearer or a unit added is charged here at
    once.
    """
    designs = {name: attack + health + energy
               for name, _symbol, attack, health, energy in CATALOGUE}
    return sum(designs[type_name] for _depth, _x, type_name, _name in ARRAY)


def _depths():
    """How deep the array reaches, in rows."""
    return max(depth for depth, _x, _type, _name in ARRAY) + 1


def _columns():
    """How wide the array reaches, in columns."""
    return max(x for _depth, x, _type, _name in ARRAY) + 1


def rows_for(player_number, player_numbers, size_y):
    """The rows this player's array stands in, nearest their edge first.

    Depth is turned into a row here and nowhere else. The lower-numbered of
    the two players takes the top half, which `placement` also says, so their
    depth 0 is row 0; the other player's depth 0 is the last row.

    Answers None where there is no array to place - any player count but two,
    or a session that is not one of the two placing players.
    """
    placing = placement._placing(player_numbers)
    if placing is None or int(player_number) not in placing:
        return None
    if int(player_number) == placing[0]:
        return [depth for depth in range(_depths())]
    return [int(size_y) - 1 - depth for depth in range(_depths())]


def fits(player_number, player_numbers, size_x, size_y):
    """Whether this player's array can stand where it is meant to.

    Every square of it must be on the board and inside the area `placement`
    allows this player, because an array that cannot be committed as it stands
    is worse than no array: it hands a player fifteen units and a refusal.
    """
    rows = rows_for(player_number, player_numbers, size_y)
    if rows is None:
        return False
    if int(size_x) < _columns():
        return False
    allowed = placement.rows(player_number, player_numbers, size_y)
    return all(row in allowed for row in rows)


def placements(player_number, player_numbers, size_x, size_y):
    """Where this player's array stands, as (type name, unit name, x, y).

    Empty where the array does not fit, so a caller that deploys what this
    returns deploys nothing rather than part of an army.
    """
    if not fits(player_number, player_numbers, size_x, size_y):
        return []
    rows = rows_for(player_number, player_numbers, size_y)
    return [(type_name, name, x, rows[depth])
            for depth, x, type_name, name in ARRAY]
