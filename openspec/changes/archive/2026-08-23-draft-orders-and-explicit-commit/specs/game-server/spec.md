## ADDED Requirements

### Requirement: Setup Survives A Session

The system SHALL restore the administrator's uncommitted setup when the server
is run again for the same game, so that ending the session before committing
setup does not cost the board that was sized or the players that were
registered.

Where a restored setup action can no longer be carried out, the server SHALL
report which action was dropped and why, before taking its next command, and
SHALL continue with the rest of the setup restored. A configuration loaded from
a file SHALL be restored by reading that file again; if it can no longer be
read, that is a dropped action like any other and SHALL NOT prevent the game
from being opened.

#### Scenario: Reopening after a session ends during setup

- **WHEN** the administrator sets a board size and registers players, the session ends without committing, and the server is run again for the same game
- **THEN** `show board` shows the board at the size that was set
- **AND** `show players` lists the players that were registered
- **AND** the administrator may register more players or commit setup

#### Scenario: Reopening after committing setup

- **WHEN** the administrator commits setup and the server is run again
- **THEN** nothing uncommitted is restored
- **AND** the server resumes its unattended turn cycle

#### Scenario: A loaded file that has since gone

- **WHEN** setup is restored and a file a `load` command named can no longer be read
- **THEN** the server reports that the command was dropped and why
- **AND** the rest of the setup is restored
- **AND** the administrator may reissue the command
