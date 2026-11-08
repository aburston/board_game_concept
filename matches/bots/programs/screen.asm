; screen: walk to the frontier row in the column in front of the Keeps on my
; side of the board, round my own units, and stand there. Written for the
; default board, where the frontier rows are 3 and 4 and the Keeps stand in
; columns 3 and 4; I strike nothing, so a step is all I need to afford
SELF                 ; r0 x, r1 y, r3 energy
MOV r6, r0
MOV r7, r1
SET r2, 1
JIF lt r3, r2, rest
SET r4, 3            ; target column: 3 from the left half, 4 from the right
SET r2, 4
JIF lt r6, r2, column
SET r4, 4
column: FLAG mine    ; r1 = my flag's row, which says which half is mine
SET r5, 3            ; target row: 3 for the north half, 4 for the south
SET r2, 4
JIF lt r1, r2, rows
SET r5, 4
rows: SUB r4, r6     ; dx
SUB r5, r7           ; dy
JIF zero r5, across
SIGN r5
MOV r2, r7
ADD r2, r5
MAP r6, r2           ; what stands in the row I would step into
SET r3, 2
JIF eq r0, r3, across  ; one of mine: try the other way
JIF pos r5, south
MOVE north
HALT
south: MOVE south
HALT
across: JIF zero r4, stay
SIGN r4
MOV r2, r6
ADD r2, r4
MAP r2, r7
SET r3, 2
JIF eq r0, r3, stay  ; one of mine both ways: wait
JIF pos r4, east
MOVE west
HALT
east: MOVE east
HALT
stay: HOLD
HALT
rest: SLEEP 1
