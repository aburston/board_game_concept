## MODIFIED Requirements

### Requirement: Simultaneous Attack Exchange

The system SHALL resolve a contested square as a single exchange: every unit
standing there attacks every other unit standing there once, with all attacks
applying at the same instant, regardless of the damage those attacks receive
in the same exchange. A unit gets one attack in the exchange and no more; to
attack again it must be ordered into the square again on a later turn.

#### Scenario: Both units strike

- **WHEN** two units contest a square
- **THEN** each deals its attack value in damage to the other
- **AND** neither is spared by having been damaged in the same exchange

#### Scenario: A unit does not attack itself

- **WHEN** attacks are resolved in a contested square
- **THEN** no unit attacks itself

#### Scenario: A unit strikes once and then stops

- **WHEN** a unit attacks in a contested square and both units survive the exchange
- **THEN** it makes no further attack that turn
- **AND** it must be ordered into the square again to attack on a later turn

## ADDED Requirements

### Requirement: An Attack Costs Its Value Once A Turn

The system SHALL charge a unit its attack value in energy once for the exchange
in which it attacks, however many opponents it strikes, and SHALL prevent the
unit from attacking when it cannot pay. The exchange SHALL be all or nothing: a
unit that cannot pay makes no attack at all, so no opponent is favoured by where
it happens to sit in the square. Because a contest is one exchange a turn, a
unit never spends more than one attack value on fighting in a single turn.

#### Scenario: Paying to attack

- **WHEN** a unit attacks
- **THEN** its energy is reduced by its attack value

#### Scenario: Paying once however many opponents there are

- **WHEN** a unit attacks in a contest against two or more opponents
- **THEN** its energy is reduced by its attack value once
- **AND** it deals its attack value in damage to every one of those opponents

#### Scenario: A whole turn's fighting costs one attack value

- **WHEN** a unit contests a square for a turn
- **THEN** it is charged its attack value at most once for that turn
- **AND** pressing the fight over several turns costs its attack value each turn

#### Scenario: Exhausted unit cannot attack

- **WHEN** a unit's energy is below its attack value
- **THEN** it deals no damage
- **AND** its energy is unchanged

#### Scenario: An exchange is all or nothing

- **WHEN** a unit that cannot pay contests a square with two or more opponents
- **THEN** it strikes none of them
- **AND** which opponents it would have struck does not depend on the order the square holds them in

### Requirement: Every Attacker Strikes Once In The Exchange

The system SHALL draw both attackers and targets from the units undestroyed
when the exchange begins, so that a unit destroyed by the exchange still lands
its own attack in it, and a unit already destroyed before the exchange neither
attacks nor is attacked.

#### Scenario: A unit destroyed in the exchange still strikes

- **WHEN** a unit is destroyed by an attack in the exchange
- **THEN** its own attack in that exchange is still applied

#### Scenario: An already destroyed unit takes no part

- **WHEN** a unit was destroyed before the exchange began
- **THEN** it neither attacks nor is attacked

## REMOVED Requirements

### Requirement: Attacking Costs Energy

**Reason**: The cost is now paid once a turn, not once a round, because a
contest is a single exchange. Replaced by "An Attack Costs Its Value Once A
Turn", which keeps the once-per-exchange charge, the all-or-nothing rule and
the inability of an exhausted unit to strike.

**Migration**: A unit is charged its attack value once for the turn's exchange
rather than once per round. A caller that summed a turn's cost over rounds now
counts a single attack value; pressing a fight across turns costs that value
each turn.

### Requirement: Combat Runs To A Decision

**Reason**: Combat no longer repeats. A contest is a single exchange, so there
is no attrition over rounds and no run-to-a-decision to guarantee — a fight
that does not destroy anything is simply undecided, which the square-ownership
requirement already covers.

**Migration**: A contest that does not destroy a unit in its one exchange ends
undecided; the movers fall back and the square is left as it was. Where a
caller relied on a stronger unit grinding a weaker one down over several rounds
in a single turn, it must now order the unit into the square across several
turns instead. Termination is trivially guaranteed: one exchange always ends.

### Requirement: Attackers Are The Units Standing At The Start Of A Round

**Reason**: There are no longer rounds to be the start of. Replaced by "Every
Attacker Strikes Once In The Exchange", which keeps the property that mattered
— every strike of the exchange lands, including that of a unit the exchange
destroys.

**Migration**: What was true of the units standing at the start of a round is
now true of the units standing at the start of the exchange, of which there is
one a turn.
