; fugitive: I carry the flag. Walk along my own edge row every turn I can
; afford a step and a strike, turning at the edge of the board and away
; from an enemy my army knows of within two columns; never leave the row.
; My heading is kept in memory word 0 between turns. `3` is my fare plus
; my attack
SELF                 ; r0 x, r1 y, r3 energy
MOV r6, r0
MOV r7, r1
SUB r3, 3
JIF neg r3, rest
LOAD r4, 0           ; my heading: +1 east, -1 west, 0 not yet chosen
JIF notzero r4, have
SET r4, 1
have: EXTENT         ; r0 = the board's width
MOV r5, r6
ADD r5, r4           ; the column I would step into
JIF neg r5, turn
JIF lt r5, r0, kept
turn: SET r2, 0
SUB r2, r4
MOV r4, r2           ; the other way
kept: NEAREST enemy  ; r0, r1 = where, or -1
JIF neg r0, walk
SUB r0, r6           ; dx to the enemy
MOV r2, r0
ABS r2
SET r3, 3
JIF lt r2, r3, near
JMP walk
near: SIGN r0
JIF zero r0, walk
SET r2, 0
SUB r2, r0
MOV r4, r2           ; away from it
walk: STORE r4, 0
JIF pos r4, east
MOVE west
HALT
east: MOVE east
HALT
rest: SLEEP 1
