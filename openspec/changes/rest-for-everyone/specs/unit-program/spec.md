## MODIFIED Requirements

### Requirement: Sleep Is How A Unit Rests

The system SHALL switch a unit's controller off for `n` turns, `n` being 1 to
100, when its program runs `SLEEP n`; no sleep SHALL last longer. A sleeping
unit SHALL give no order, spend no ticks, and recover energy under the rest
rule like every unit standing on the board. Being in a fight SHALL wake it:
the exchange is fought on the ordinary terms, and its controller runs again
on the next turn, whatever `n` remained. Nothing else SHALL wake a sleeper; a
message SHALL NOT.

#### Scenario: Sleeping and resting

- **WHEN** a unit runs `SLEEP 3` on a turn and is not attacked
- **THEN** its controller does not run on the next three turns
- **AND** it recovers 2 energy on each of them, up to the energy its type was designed with

#### Scenario: The longest sleep

- **WHEN** a unit runs `SLEEP 100` and is never attacked
- **THEN** its controller runs again on the hundred-and-first turn, so no unit is dormant for free
- **AND** sleeping again costs it the tick of another `SLEEP`

#### Scenario: Woken by a blow

- **WHEN** a sleeping unit's square is contested
- **THEN** it strikes every other unit in the square if it can pay its attack, as a waking unit would
- **AND** its controller runs on the next turn

#### Scenario: A message does not wake a sleeper

- **WHEN** a friend sends a sleeping unit a message
- **THEN** the sleeper's controller does not run until its sleep ends
- **AND** the message waits in its inbox

#### Scenario: A sleeping unit pays nothing to its meter

- **WHEN** a unit sleeps for three turns
- **THEN** its meter is unchanged by them
