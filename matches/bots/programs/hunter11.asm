; the game's own hunter, as the catalogue gives it to a type that
; hunts, with `need` the fare plus the attack of the type that runs it
; hunt: walk at the nearest enemy flag, round my own units
SELF                 ; r0 x, r1 y, r3 energy
MOV r6, r0
MOV r7, r1
SUB r3, 11       ; a step and a strike
JIF neg r3, rest
FLAG enemy             ; r0, r1 = where to go, or -1
JIF neg r0, rest
SUB r0, r6           ; dx
SUB r1, r7           ; dy
MOV r4, r0
MOV r5, r1
SIGN r4              ; which way along the row, or 0
SIGN r5              ; which way down the column, or 0
ABS r0
ABS r1
JIF lt r0, r1, vfirst
MOV r2, r6           ; along the row first: what stands where I would step
ADD r2, r4
MAP r2, r7           ; 2 is one of mine - or my own square, when dx is 0
SUB r0, 2
JIF zero r0, vonly
JIF pos r4, east
MOVE west
HALT
east: MOVE east
HALT
vfirst: MOV r2, r7   ; down the column first
ADD r2, r5
MAP r6, r2
SUB r0, 2
JIF zero r0, honly
JIF pos r5, south
MOVE north
HALT
south: MOVE south
HALT
vonly: MOV r2, r7    ; the row is blocked: the column, if it is clear
ADD r2, r5
MAP r6, r2
SUB r0, 2
JIF zero r0, stay
JIF pos r5, south
MOVE north
HALT
honly: MOV r2, r6    ; the column is blocked: the row, if it is clear
ADD r2, r4
MAP r2, r7
SUB r0, 2
JIF zero r0, stay
JIF pos r4, east
MOVE west
HALT
stay: SLEEP 1        ; both ways stand one of mine: rest until one moves
rest: SLEEP 1
