## Purpose

The one thing an army cannot hide and cannot afford to lose: a unit that
carries its player's flag, whose square everybody can see, and whose
destruction puts its owner out of the game.

## ADDED Requirements

### Requirement: One Unit Carries The Flag

The system SHALL let a player designate exactly one of their units as carrying
their flag, during setup, and SHALL fix that designation when the player
commits their setup.

Designating SHALL cost nothing: the flag is a standing, not a statistic. It
SHALL NOT change a unit's attack, health, energy or the points it cost.

While setup is still being decided the designation MAY be moved from one of
the player's units to another, and the last one made before the commit is the
one that stands. After the commit it SHALL NOT be moved, passed to another
unit, or given up.

#### Scenario: Designating a carrier

- **WHEN** a player designates one of their units during setup
- **THEN** that unit carries their flag

#### Scenario: Designating another unit before committing

- **WHEN** a player designates one unit and then another, before committing
- **THEN** only the second carries the flag
- **AND** the first carries nothing

#### Scenario: One flag per player

- **WHEN** a player has designated a carrier
- **THEN** exactly one of their units carries their flag

#### Scenario: Designating another player's unit

- **WHEN** a player designates a unit that is not theirs
- **THEN** the designation is refused
- **AND** the flag is where it was

#### Scenario: Designating after the setup is committed

- **WHEN** a player designates a carrier after committing their setup
- **THEN** the designation is refused, saying the flag is fixed for the game

#### Scenario: The flag costs nothing

- **WHEN** a unit is designated as the carrier
- **THEN** its owner's spend and remaining points are unchanged

### Requirement: A Setup Without A Flag Is Refused

The system SHALL refuse a player's setup commit unless exactly one of that
player's units carries their flag, and SHALL say which is missing.

A player who cannot be eliminated by losing a flag is playing a different game
from everyone else at the table, so this is a refusal rather than a default.

#### Scenario: Committing with a carrier

- **WHEN** a player commits a setup in which one of their units carries the flag
- **THEN** the commit is accepted

#### Scenario: Committing without a carrier

- **WHEN** a player commits a setup in which none of their units carries the flag
- **THEN** the commit is refused, saying a unit must carry the flag
- **AND** nothing of that player's setup is published

#### Scenario: Committing with no units at all

- **WHEN** a player commits a setup having deployed nothing
- **THEN** the commit is refused for the same reason

#### Scenario: Turns after the first

- **WHEN** a player commits a turn after their setup was committed
- **THEN** the commit is not refused for the flag, which is already fixed

### Requirement: A Flag's Square Is Shown To Everyone

The system SHALL show every player which square each flag is on and which
player it belongs to, whether or not they have made contact with the unit
carrying it. This is the one thing `visibility` discloses without contact.

What is disclosed SHALL be the square and the owner and nothing else. The
carrier's name, type, symbol, and its attack, health and energy SHALL stay
hidden until contact discloses them the way it discloses any unit's.

A flag SHALL be shown for as long as its carrier is standing. Once the carrier
is destroyed the flag SHALL be reported as fallen rather than placed on a
square.

#### Scenario: An enemy flag out of contact

- **WHEN** a player has made no contact with an enemy army
- **THEN** they are told which square that enemy's flag is on
- **AND** which player it belongs to

#### Scenario: What the flag does not disclose

- **WHEN** a player reads an enemy flag they are not in contact with
- **THEN** they are not told the carrier's name, type, symbol or statistics

#### Scenario: A flag that moves

- **WHEN** a flag carrier moves and the turn resolves
- **THEN** every player is shown the square it moved to

#### Scenario: The carrier met in person

- **WHEN** a player makes contact with the unit carrying an enemy flag
- **THEN** they learn its type and statistics as contact always discloses them

#### Scenario: A flag that has fallen

- **WHEN** a flag carrier has been destroyed
- **THEN** that flag is reported as fallen and is on no square

### Requirement: Losing The Flag Puts A Player Out

The system SHALL eliminate a player whose flag carrier is destroyed, in the
resolution that destroys it, whatever else that player still holds.

#### Scenario: The carrier is destroyed

- **WHEN** a turn resolves in which a player's flag carrier is destroyed
- **THEN** that player is eliminated at that resolution

#### Scenario: An army that outlives its flag

- **WHEN** a player's flag carrier is destroyed and other units of theirs are
  standing
- **THEN** that player is still eliminated

#### Scenario: The last player standing

- **WHEN** every other player has been eliminated, by flag loss or otherwise
- **THEN** the game is decided in favour of the one who is left

#### Scenario: Both flags fall together

- **WHEN** one resolution destroys the flag carriers of the last two players
- **THEN** both are eliminated
- **AND** the game is a draw

### Requirement: An Eliminated Player's Units Are Left Standing And Inert

The system SHALL leave the units of an eliminated player on the squares they
hold. Those units SHALL take no orders and SHALL strike nothing, and they
SHALL still be attacked and destroyed like any other unit.

An army without its flag is terrain: it blocks a square until somebody clears
it, and it decides nobody's game.

#### Scenario: The units stay where they are

- **WHEN** a player is eliminated by flag loss
- **THEN** their standing units remain on their squares

#### Scenario: They take no orders

- **WHEN** an eliminated player's unit is ordered
- **THEN** the order is refused
- **AND** the unit does not move

#### Scenario: They strike nothing

- **WHEN** a unit belonging to an eliminated player is contested by another
  player's unit
- **THEN** it lands no attack

#### Scenario: They can be destroyed

- **WHEN** another player's unit attacks an eliminated player's unit
- **THEN** it takes the damage and is destroyed if it runs out of health
- **AND** the square is left as any contest leaves it

#### Scenario: They do not keep their owner in the game

- **WHEN** a later turn resolves and an eliminated player's units are still
  standing
- **THEN** that player is still eliminated
- **AND** they are not waited for at the commit barrier

### Requirement: A Game Set Up Without Flags Is Played Without Them

The system SHALL keep playing a game whose setups were committed before flags
existed, under the rules that game was set up under: no unit carries a flag,
no flag is shown, and nobody is eliminated by flag loss.

#### Scenario: An older game

- **WHEN** a game whose players committed without designating a carrier is
  opened
- **THEN** it is readable and playable
- **AND** no flag is reported for any player

#### Scenario: Elimination in an older game

- **WHEN** a turn of such a game is resolved
- **THEN** a player is eliminated only by having nothing left that can act
