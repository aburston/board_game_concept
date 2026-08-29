## 1. A fight is told to the people in it

- [x] 1.1 `for_seat` keeps an entry only where one of the seat's own units is
      named in it, and loses the `visible` parameter nothing reads any more
- [x] 1.2 Update the caller in `service/turn.py`, which no longer needs to
      work out what each seat could see for this
- [x] 1.3 Tests: a bystander in contact with both fighters is told nothing of
      their blows; a seat in a three-way is told its own and not the others';
      a fight out of sight is still silent; the observer still reads it all
- [x] 1.4 Update the tests that asserted the old "in sight" rule

## 2. The controls go where the board is

- [x] 2.1 Append the direction controls to the board card, under the board,
      and take them out of the orders tray
- [x] 2.2 Say "choose a unit" under the board when nothing is selected
- [x] 2.4 Lay the four headings out as a compass, drawn as their arrows, with
      a fifth in the centre for holding - offered whether or not there is an
      order, and saying so when there is one to take back
- [x] 2.5 Name each control for a reader that cannot see the arrow, and size
      the compass for a finger
- [x] 2.3 A source guard that the directions belong to the board card

## 3. The ring shows the energy

- [x] 3.1 Draw the ring as a proportion of the energy a unit has left against
      what its type was designed with
- [x] 3.2 Pass `energyOf` from the play screen, reading the type from what
      this seat has met, and draw a plain ring where it is not known
- [x] 3.3 A source guard, and a browser check that a spent unit and a fresh
      one are drawn differently

## 4. Finishing

- [x] 4.1 `node --check`, flake8, and the whole suite on both backends
- [x] 4.2 Drive it in a browser and shoot it
- [x] 4.3 Sync the specs and archive the change
