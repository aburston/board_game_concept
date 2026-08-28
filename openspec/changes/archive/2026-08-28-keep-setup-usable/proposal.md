## Why

Three things found by playing the browser interface, all of them in setup.

Two are the interface throwing away a choice that was still being used. The
deploy chooser goes back to its first type after every placement, so laying
down five of one type means picking it five times. The board's width and
height are emptied whenever a seat is registered or removed, so a size typed
and not yet sent is lost to a form nobody touched.

The third stops a game dead. Two players deployed onto the same squares, so
every deployment was refused as contested, and the resolution that ended
setup put nothing on the board. The game judges elimination only once a unit
has reached the board, so nobody was eliminated and nothing was decided - but
setup was over, so no more units could be added either. The game cannot be
played, cannot be finished, and cannot be gone back to. A live game is in
that state now.

## What Changes

- The deploy chooser keeps the type it was left on, so several units of one
  type can be placed without choosing it again.
- The board's width and height keep what was typed while seats are added and
  removed, and go back to reading the board once a size has been accepted.
- A resolution that carries out a player's committed setup begins the game,
  whether or not any unit survived it. A first turn in which every deployment
  was refused therefore eliminates the players who have nothing standing and
  decides the game, instead of leaving it unplayable and unfinished.
- A player whose flag carrier was refused is eliminated like one whose flag
  has fallen, and every player in a game that has begun is reported on in the
  record of where the flags are. Found while fixing the above: a setup cannot
  be committed without a carrier, but a carrier can still be refused as the
  turn resolves, which left that player holding an army the flag could never
  be taken from.
- The armoury stops offering setup forms to a seat whose setup is over, and
  sends it to the board instead of refusing every command it is given.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `game-outcome`: "The Game Begins When The First Unit Reaches The Board"
  becomes a rule about the players' setups being resolved rather than about
  what survived them, so that a first turn leaving nothing standing is
  decided rather than stalled.
- `web-interface`: the armoury keeps a half-made choice across a redraw, and
  shows a seat whose setup is over that it is over.
- `flag-carrier`: a flag that never reached the board is reported, and puts
  its player out the same way a fallen one does.

## Impact

- `service/turn.py`: `has_started`, and through it elimination, the outcome
  and the turn number; `eliminated_players` and the flags record.
- `http/static/armoury.js` and `http/static/app.js`: the deploy chooser and
  the board-size fields, both held in `state`, and what the armoury draws for
  a seat past setup.
- No storage format changes and no contract changes. A game already stalled
  in this way settles at its next resolution rather than retroactively.
