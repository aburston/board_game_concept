; the game's own hunter, as the catalogue gives it to a type that
; hunts, with `need` the fare plus the attack of the type that runs it
; hunt: walk at the nearest enemy flag, round my own units
SELF                 ; r0 x, r1 y, r3 energy
MOV r6, r0
MOV r7, r1
SUB r3, 9       ; a step and a strike
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
CALL row             ; along the row first, unless one of mine stands there
JIF zero r0, vonly
JMP goh
vfirst: CALL col     ; down the column first
JIF zero r0, honly
JMP gov
vonly: CALL col      ; the row is blocked: the column, if it is clear
JIF zero r0, stay
JMP gov
honly: CALL row      ; the column is blocked: the row, if it is clear
JIF zero r0, stay
goh: JIF pos r4, east
MOVE west
HALT
east: MOVE east
HALT
gov: JIF pos r5, south
MOVE north
HALT
south: MOVE south
HALT
stay: SLEEP 1        ; both ways stand one of mine: rest until one moves
rest: SLEEP 1
; what stands where I would step along the row, or down the column: r0 is
; 0 for one of mine - or my own square, when the step is nowhere
row: MOV r2, r6
ADD r2, r4
MOV r3, r7
JMP look
col: MOV r2, r6
MOV r3, r7
ADD r3, r5
look: MAP r2, r3
SUB r0, 2
RET
