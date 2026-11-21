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
# health, energy, compute, program). Defining a type spends nothing, so the
# whole catalogue costs a player nothing until they deploy a unit of one of
# its types.
#
# The Wall and the Scout are here on purpose. Both are designs the rules allow
# and nobody builds - attack 0 with no energy, and attack 0 with energy - and
# a default catalogue is the cheapest way to teach that they exist.
#
# Every type with a controller carries a default program, so that a player
# who changes nothing fields an army that plays. Each is written to fit its
# type's per-turn cap of ten ticks a point of compute on every turn, which
# `tests/test_default_army.py` holds it to

# Every default program is written with the preprocessor - `#include
# <unit.h>` for the machine's names, `#define` for its own - so that it reads
# as a description of what the unit does rather than as register numbers.
# A program's parameters are `#define`d above it by the function that builds
# it, as lines the player can read and edit: `#define NEED 3` is the one
# number that differs between the types that hunt.

# a controller that goes for the nearest enemy flag by the shorter axis
# first and round its own units - a square one of its own stands on is never
# stepped onto, because a contest is fought with whoever is in the square -
# and sleeps a turn when it cannot afford both the step and the strike it
# may have to land on arriving. A hunter blocked both ways has run most of
# the program to find out, and sleeps a turn rather than pay to hold - a rest
# costs nothing, and the way may be clear next turn. Fifty-odd ticks on its
# longest path, well inside the four compute of the least thoughtful hunter
HUNTER = """\
#include <unit.h>
; hunter: walk at the nearest enemy flag, round my own units, and fight
; whatever I walk into. I set out only when I can afford a step and the
; strike that may follow it, so that I arrive able to fight; when I cannot,
; or when my own units stand both ways round, I rest a turn.
;
; NEED is a step's fare plus my attack; TARGET is what I walk at

#ifndef TARGET
#define TARGET FLAG enemy
#endif

; my registers. The sensors write r0 to r3, so what I keep lives above them
#define here_x   r6
#define here_y   r7
#define way_x    r4          ; -1 west, 0 level, 1 east: towards the flag
#define way_y    r5          ; -1 north, 0 level, 1 south
#define row_gap  FOUND_X     ; how far along the row the flag is
#define col_gap  FOUND_Y     ; how far down the column
#define look_x   r2          ; the square I am thinking of stepping onto
#define look_y   r3
#define can_step r0          ; what the look-ahead answers: 1 to go
#define heading  r0          ; the direction number of my step

        UNLESS_AFFORD(NEED, rest)
        MOV here_x, MY_X
        MOV here_y, MY_Y
        TARGET
        IF_NONE(FOUND_X, rest)              ; nothing left to hunt

        SUB row_gap, here_x
        SUB col_gap, here_y
        MOV way_x, row_gap
        SIGN way_x
        MOV way_y, col_gap
        SIGN way_y
        ABS row_gap
        ABS col_gap
        IF_BELOW(row_gap, col_gap, column_first)

row_first:
        CALL row_is_clear
        IF_NONZERO(can_step, step_along_row)
        CALL column_is_clear
        IF_NONZERO(can_step, step_down_column)
        REST                                ; my own stand both ways: wait
column_first:
        CALL column_is_clear
        IF_NONZERO(can_step, step_down_column)
        CALL row_is_clear
        IF_NONZERO(can_step, step_along_row)
        REST

step_along_row:
        ROW_STEP(way_x, heading)
        STEP(heading)
step_down_column:
        COLUMN_STEP(way_y, heading)
        STEP(heading)
rest:   REST

; may I step the next square along the row, or down the column? Not onto
; one of my own - and a way of 0 looks at my own square, so a level axis
; answers no. Anything else, an enemy included, is something to walk into
row_is_clear:
        MOV look_x, here_x
        ADD look_x, way_x
        MOV look_y, here_y
        GOTO(is_it_mine)
column_is_clear:
        MOV look_x, here_x
        MOV look_y, here_y
        ADD look_y, way_y
is_it_mine:
        LOOK_AT(look_x, look_y)
        IF_SEEN(FRIEND, mine)
        SET can_step, 1
        RET
mine:   SET can_step, 0
        RET
"""


def hunter(need, target=None):
    """The hunter for a type whose step and strike cost `need`, walking at
    `target` - a sensor line - or the nearest enemy flag."""
    defines = f'#define NEED {need}\n'
    if target is not None:
        defines += f'#define TARGET {target}\n'
    return defines + HUNTER


# the Scout's controller. A Scout strikes nothing, so a step onto an enemy
# is a contest it cannot win and a fare for nothing. The explorer walks at
# the nearest square its army does not know, trying four steps in turn -
# down the column towards it, along the row towards it, and a step aside
# each way - and takes the first onto a square its map calls unknown or
# empty, never onto one of its own, an enemy it knows of, or off the board.
# It remembers how near it has got to what it is looking for: twenty turns
# without getting nearer means the unknown is behind something it cannot
# pass, and it sleeps a hundred turns rather than pace for ever, which is
# what kept a game alive to the cap. Nothing left to find, it sleeps too
EXPLORER = """\
#include <unit.h>
; explorer: walk at the nearest square my army knows nothing of. I strike
; nothing, so I step only onto squares my map calls unknown or empty -
; never onto one of my own, an enemy I know of, or off the board - trying
; the column towards it, then the row, then a step aside each way. I
; remember how near I have got: twenty turns without getting nearer means
; what I am looking for is behind something I cannot pass, and I sleep a
; hundred turns rather than pace. Nothing left to find, I sleep too.
;
; NEED is a step's fare: I have no strike to pay for

; my registers. The sensors write r0 to r3, so what I keep lives above them
#define here_x   r6
#define here_y   r7
#define way_x    r4          ; -1 west, 0 level, 1 east: towards the unknown
#define way_y    r5          ; -1 north, 0 level, 1 south
#define look_x   r2          ; the square I am thinking of stepping onto
#define look_y   r3
#define count    r3          ; a number read from my memory
#define limit    r0
#define can_step r0          ; what may_step answers: 1 to go
#define heading  r0          ; the direction number of my step

; my memory, by word: how near I have ever been to an unknown square, and
; how many turns running I have failed to get nearer
#define NEAREST_YET   1
#define TURNS_STALLED 2
#define PATIENCE      20

        UNLESS_AFFORD(NEED, rest)
        MOV here_x, MY_X
        MOV here_y, MY_Y
        NEAREST unknown
        IF_NONE(FOUND_X, nothing_left)
        MOV way_x, FOUND_X
        MOV way_y, FOUND_Y

; am I nearer than I have ever been?
        LOAD count, NEAREST_YET             ; 0 before I have seen one
        IF_ZERO(count, nearer)
        IF_BELOW(FOUND_DIST, count, nearer)
        LOAD count, TURNS_STALLED           ; no: one more turn stalled
        ADD count, 1
        STORE count, TURNS_STALLED
        SET limit, PATIENCE
        IF_BELOW(limit, count, nothing_left) ; too long: it is out of reach
        GOTO(choose_a_step)
nearer: STORE FOUND_DIST, NEAREST_YET
        SET count, 0
        STORE count, TURNS_STALLED

choose_a_step:
        SUB way_x, here_x
        SUB way_y, here_y
        SIGN way_x
        SIGN way_y
        MOV look_x, here_x                  ; first: down the column
        MOV look_y, here_y
        ADD look_y, way_y
        CALL may_step
        IF_NONZERO(can_step, step_down_column)
        MOV look_x, here_x                  ; second: along the row
        ADD look_x, way_x
        MOV look_y, here_y
        CALL may_step
        IF_NONZERO(can_step, step_along_row)
        MOV look_x, here_x                  ; third: a step aside, east
        ADD look_x, 1
        MOV look_y, here_y
        CALL may_step
        IF_NONZERO(can_step, step_east)
        MOV look_x, here_x                  ; fourth: a step aside, west
        SUB look_x, 1
        MOV look_y, here_y
        CALL may_step
        IF_NONZERO(can_step, step_west)
        REST                                ; nowhere to step this turn

step_down_column:
        COLUMN_STEP(way_y, heading)
        STEP(heading)
step_along_row:
        ROW_STEP(way_x, heading)
        STEP(heading)
step_east:
        STEP(east)
step_west:
        STEP(west)
nothing_left:
        REST_LONG
rest:   REST

; may I step onto (look_x, look_y)? Yes for a square my map calls unknown
; or empty; no for one of mine, an enemy I know of, or off the board
may_step:
        LOOK_AT(look_x, look_y)
        IF_SEEN(UNKNOWN, yes)
        IF_SEEN(EMPTY, yes)
        SET can_step, 0
        RET
yes:    SET can_step, 1
        RET
"""


def explorer(need=1):
    return f'#define NEED {need}\n' + EXPLORER


# a controller for the front rank: step towards the enemy's edge whenever a
# step and the strike that may follow are affordable, never onto one of my
# own, and fight whatever the step meets. Twenty-odd ticks on its longest
# path, so it fits a Pawn's cap of three hundred many times over
VANGUARD = """\
#include <unit.h>
; vanguard: step towards the enemy's edge of the board whenever I can afford
; the step and the strike that may follow it, never onto a square one of my
; own stands on, and fight whatever the step meets. Otherwise I rest a turn.
;
; NEED is a step's fare plus my attack

#define enemy_row r6         ; the row the enemy flag stands on: their edge
#define ahead     r7         ; -1 or 1: which way down the column they are
#define front     r2         ; the row of the square in front of me
#define heading   r0         ; the direction number of my step

        FLAG enemy
        IF_NONE(FOUND_X, rest)              ; no enemy flag left to go at
        MOV enemy_row, FOUND_Y
        UNLESS_AFFORD(NEED, rest)
        MOV ahead, enemy_row
        SUB ahead, MY_Y
        IF_ZERO(ahead, rest)                ; I am at their edge already
        SIGN ahead
        MOV front, MY_Y
        ADD front, ahead
        LOOK_AT(MY_X, front)
        IF_SEEN(FRIEND, rest)               ; one of mine: wait for it
        COLUMN_STEP(ahead, heading)
        STEP(heading)
rest:   REST
"""

# a controller that holds its square and sleeps as long as it may, waking
# to strike back when struck, which is combat's doing and not its own
WARDEN = """\
#include <unit.h>
; warden: hold the square and sleep as long as I may. A blow wakes me, and
; I strike back - which is combat's doing and not mine.
        REST_LONG
"""


def vanguard(need):
    return f'#define NEED {need}\n' + VANGUARD


CATALOGUE = (
    # not `#`: that is the glyph an empty square is drawn with, and a wall
    # drawn as one is a wall a player cannot see on their own board
    ('Wall',   'W', 0, 10,  0, 0, None),
    ('Scout',  'o', 0,  2, 12, 6, explorer()),
    ('Pawn',   'p', 1,  4,  2, 3, vanguard(2)),
    ('Runner', 'r', 2,  4, 10, 5, hunter(3)),
    ('Line',   'L', 3,  6, 12, 4, hunter(5)),
    ('Lance',  '!', 8,  2, 10, 4, hunter(9)),
    ('Keep',   'K', 1, 10,  5, 8, WARDEN),
    ('Heavy',  'H', 5, 10, 15, 4, hunter(8)),
)


# the sixteen units, as (depth, column, type name, unit name). Depth 1 is the
# row in front of the player's own edge and takes the units whose programs
# leave it - the Pawns, the Lines and the Heavies - so that nothing in the
# row behind stands behind a unit that never moves; depth 0 is the edge
# itself and takes the Runners and Scouts, which follow the front rank out,
# the Keeps, one of which carries the flag, and the Walls beside them, where
# what a wall cannot do - move - is what a flag's flanks want. The first
# array had the Walls in front and the Lines behind, and the programmed
# series showed what that fields: the two Heavies walk out alone and twelve
# units stand boxed in for the rest of the game.
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
    (1, 2, 'Line', 'line1'),
    (1, 3, 'Heavy', 'heavy1'),
    (1, 4, 'Heavy', 'heavy2'),
    (1, 5, 'Line', 'line2'),
    (1, 6, 'Pawn', 'pawn3'),
    (1, 7, 'Pawn', 'pawn4'),
    (0, 0, 'Runner', 'runner1'),
    (0, 1, 'Scout', 'scout1'),
    (0, 2, 'Wall', 'wall1'),
    (0, 3, 'Keep', 'keep1'),
    (0, 4, 'Keep', 'keep2'),
    (0, 5, 'Wall', 'wall2'),
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
            'compute': compute,
            'program': program,
            'obj': UnitType(name, symbol, attack, health, energy, compute,
                            program),
        }
        for name, symbol, attack, health, energy, compute, program
        in CATALOGUE
    }


def cost():
    """What the array costs to deploy.

    Derived from the tables rather than written down as a number, so the two
    cannot come apart: a type made dearer or a unit added is charged here at
    once.
    """
    designs = {name: attack + health + energy + compute
               for name, _symbol, attack, health, energy, compute, _program
               in CATALOGUE}
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
