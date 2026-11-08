; guard: go at the nearest enemy my army knows of within two squares, when I
; can afford the step and the strike; otherwise sleep a turn behind the
; wall. `8` is my fare plus my attack
SELF                 ; r0 x, r1 y, r3 energy
MOV r6, r0
MOV r7, r1
SUB r3, 8
JIF neg r3, rest
NEAREST enemy        ; r0, r1 = where, r2 = how far, or -1
JIF neg r0, rest
SET r3, 3
JIF lt r2, r3, go    ; within two squares
JMP rest
go: SUB r0, r6       ; dx
SUB r1, r7           ; dy
MOV r4, r0
MOV r5, r1
ABS r0
ABS r1
JIF lt r0, r1, vfirst
SIGN r4
JIF zero r4, vonly
JIF pos r4, east
MOVE west
HALT
east: MOVE east
HALT
vfirst: SIGN r5
JIF zero r5, honly
JIF pos r5, south
MOVE north
HALT
south: MOVE south
HALT
vonly: SIGN r5
JIF zero r5, stay
JIF pos r5, south
MOVE north
HALT
honly: SIGN r4
JIF zero r4, stay
JIF pos r4, east
MOVE west
HALT
stay: HOLD
HALT
rest: SLEEP 1
