## ADDED Requirements

### Requirement: Resolution Is Deterministic

The system SHALL resolve a turn as a pure function of the board and the orders
given. Resolving the same orders against the same board SHALL always produce the
same result: the same positions, the same health and energy, the same units
destroyed, the same contacts recorded, and the same events in the same order.

Resolving the same orders against boards whose units were registered in
different orders SHALL produce the same result and SHALL report the same events.
The order those events are narrated in MAY follow the board's own order of
units, which is a fact about the board rather than a choice made while
resolving; nothing about what happened SHALL depend on it.

No part of resolution SHALL consult a source of randomness — a random number
generator, a clock, a process or object identity, or anything else outside the
board and the orders. Where two things could happen, the rules SHALL decide
which, rather than leaving it to the order a collection happens to hold its
members in. This is an invariant of the game and constrains every rule added to
it.

#### Scenario: The same turn resolved twice

- **WHEN** the same orders are resolved against two boards built the same way
- **THEN** every unit finishes with the same position, health, energy and destroyed state
- **AND** the same events are reported in the same order

#### Scenario: The order units are held in is not an input

- **WHEN** the same orders are resolved against boards whose units were registered in different orders
- **THEN** the outcome is identical in every case
- **AND** the same events are reported, whatever order they are narrated in

#### Scenario: No rule is decided by collection order

- **WHEN** a rule must choose between two units — which is struck, which holds a cell, which order is refused
- **THEN** the choice follows from the rules and the state
- **AND** it does not follow from where either unit sits in a list

#### Scenario: A contest is decided by the units in it

- **WHEN** a contested cell is resolved
- **THEN** the damage each contestant takes depends only on the contestants' statistics and energy
- **AND** not on the order the cell holds them in
