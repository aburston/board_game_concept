## 1. Refuse the clashing commit

- [x] 1.1 In `service/turn.py` `publish`, and only for a setup commit, read the
      squares other players' published orders already claim and refuse this
      commit if one of its deployments wants one, naming the square
- [x] 1.2 Make the check and the writes it guards run under the one held lock,
      so two commits racing are serialised rather than both accepted

## 2. Hold it to the rule

- [x] 2.1 Test: a second setup commit onto a committed square is refused, and
      that player's setup is left uncommitted with its units intact
- [x] 2.2 Test: the refused player moves the unit and commits again, and it is
      accepted
- [x] 2.3 Test: the first commit keeps the square and stays committed
- [x] 2.4 Test: a setup that clashes with nothing is accepted, and a two-player
      game - where the halves make a clash impossible - is unaffected
- [x] 2.5 Test over the served contract, so the browser and the roles get the
      same refusal

## 3. Taking a unit back, so the refusal can be acted on

- [x] 3.1 `Board.take_back`, refusing only a casualty - when it is allowed is
      the service layer's rule, not the board's
- [x] 3.2 A `remove_unit` command and service action, refused once the setup
      is committed, for another player's unit, and for one that is not there
- [x] 3.3 `remove unit <name>` in the grammar, the parser and the client role
- [x] 3.4 A take-back button beside each deployed unit in the armoury
- [x] 3.5 Tests: the square, the points and the name come back; the flag is
      left uncarried; a committed setup refuses it; it survives a reload

## 4. Taking back an order, and refusing what cannot be typed

- [x] 4.1 `UnitType.hold`, a `hold` command and service action, refused before
      the first turn and for a unit that is not the player's
- [x] 4.2 `hold <unit>` in the grammar, the parser and the client role
- [x] 4.3 A Delete key and a control on the board, offered only for a unit
      that has an order, and said in the keyboard help
- [x] 4.4 Bound every number field the interface offers to the range the rules
      enforce
- [x] 4.5 Tests: the order goes, the unit stays put and rests, and it is
      refused during setup

## 5. Write it down

- [x] 5.1 Update `GAME_RULES.md` R3.5, which says both are refused
- [x] 5.2 Note in the rules that the first commit keeps the square, and why
- [x] 5.3 R2.12 for taking a unit back, and R3.2 for taking an order back

## 6. Finishing

- [x] 6.1 flake8, and run the whole suite on both backends
- [x] 6.2 Drive it in a browser: a clashing commit refused, the unit taken
      back, and the commit accepted
- [x] 6.3 Sync the specs and archive the change
