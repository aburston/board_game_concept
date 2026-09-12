## Purpose

The HTTP server as a process: what `bgcapiserver` binds when it is not told,
and what it says as it starts so that a person can reach it - from the same
machine, or from a phone across the room - without reading the source.

## ADDED Requirements

### Requirement: The Server Is Local Unless Told Otherwise

The system SHALL bind the HTTP server to the loopback address alone unless the
operator names an address to bind, and SHALL accept the wildcard address as
the way to be reached from other machines on the same network.

#### Scenario: Started with no address

- **WHEN** the server is started without naming an address to bind
- **THEN** it answers only on the machine it runs on
- **AND** a request from another machine on the same network is not answered

#### Scenario: Started on the wildcard address

- **WHEN** the server is started bound to the wildcard address
- **THEN** a request from another machine on the same network is answered

### Requirement: The Server Says Where It Can Be Reached

The system SHALL print, as it starts, an address at which a browser can reach
it. When it is bound to loopback alone, that SHALL be the loopback address.
When it is bound to the wildcard address, it SHALL print the address or
addresses another machine on the network can use instead of the wildcard,
which is not an address anybody can type. When it is bound to one named
address that is not loopback, it SHALL print that address.

When the server is bound to the wildcard address and cannot tell which
address other machines would use, it SHALL say so and SHALL say where the
operator can find it out, rather than printing the wildcard or nothing.

What is printed SHALL appear before the server starts answering requests, so
that it is the first thing on the screen rather than buried under request
logs, and SHALL include the port.

#### Scenario: Bound to loopback

- **WHEN** the server starts bound to loopback alone
- **THEN** the address it prints is the loopback address with the port

#### Scenario: Bound to the wildcard address on a network

- **WHEN** the server starts bound to the wildcard address on a machine with
  an address on a network
- **THEN** it prints that network address with the port
- **AND** it does not print the wildcard address as the place to go

#### Scenario: Bound to the wildcard address with no address it can find

- **WHEN** the server starts bound to the wildcard address and no network
  address can be found for the machine
- **THEN** it says that it could not tell which address to give out
- **AND** it says where on the machine that address can be read

#### Scenario: Bound to one named address

- **WHEN** the server starts bound to a specific address the operator named
- **THEN** it prints that address with the port, and looks for no other

### Requirement: A Reachable Address Is Offered As A QR Code

The system SHALL draw, on the terminal as it starts, a QR code encoding the
address it printed, whenever that address is one another machine can reach -
so that a person joining from a phone can scan the host's screen rather than
type the address. The code SHALL be surrounded by enough blank margin for a
phone camera to read it, and SHALL encode the full address including the
scheme and the port, so that scanning it opens the page and nothing else is
needed.

The system SHALL NOT draw a QR code when the only address is loopback, since
no other device could reach it.

Where more than one reachable address is printed, the system SHALL draw one
code and SHALL say which address it is for.

#### Scenario: Reachable from other machines

- **WHEN** the server starts and prints an address another machine can reach
- **THEN** a QR code encoding that address, with its scheme and port, is drawn
  on the terminal beneath it

#### Scenario: Loopback only

- **WHEN** the server starts bound to loopback alone
- **THEN** no QR code is drawn

#### Scenario: No address could be found

- **WHEN** the server starts bound to the wildcard address and could not find
  an address to give out
- **THEN** no QR code is drawn
