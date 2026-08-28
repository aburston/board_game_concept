## MODIFIED Requirements

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

Every player in a game that has begun SHALL be reported on, including one
whose carrier never reached the board because its deployment was refused. A
flag that never arrived SHALL be reported as not standing and on no square, so
that a player who is out for want of a flag can be told so.

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

#### Scenario: A flag that never arrived

- **WHEN** a player's flag carrier was refused as the first turn resolved
- **THEN** that player's flag is reported as not standing and on no square

### Requirement: Losing The Flag Puts A Player Out

The system SHALL eliminate a player whose flag carrier is destroyed, in the
resolution that destroys it, whatever else that player still holds.

A player whose flag is not standing SHALL be eliminated whether the carrier
was destroyed or never reached the board at all. A setup is refused unless one
unit carries the flag, but a deployment can still be refused as the turn
resolves — a contested square, or a budget that will not pay — and a player
left holding an army and no flag would be the one player the flag could never
be taken from.

#### Scenario: The carrier is destroyed

- **WHEN** a turn resolves in which a player's flag carrier is destroyed
- **THEN** that player is eliminated at that resolution

#### Scenario: An army that outlives its flag

- **WHEN** a player's flag carrier is destroyed and other units of theirs are
  standing
- **THEN** that player is still eliminated

#### Scenario: A carrier that never reached the board

- **WHEN** the deployment of a player's flag carrier is refused as the first
  turn resolves, and other units of theirs take the field
- **THEN** that player is eliminated at that resolution

#### Scenario: The last player standing

- **WHEN** every other player has been eliminated, by flag loss or otherwise
- **THEN** the game is decided in favour of the one who is left

#### Scenario: Both flags fall together

- **WHEN** one resolution destroys the flag carriers of the last two players
- **THEN** both are eliminated
- **AND** the game is a draw
