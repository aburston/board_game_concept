; advance: step towards the enemy's edge as a line, when I can afford the
; step and the strike I may have to land on arriving, and never onto one of
; my own. Whatever the step meets, it fights. Written to fit a Pawn's cap
; of twenty ticks: `2` is my fare plus my attack. The enemy's row is kept
; in r6, which no sensor writes - SELF fills r0 to r5
FLAG enemy           ; r0, r1 = the enemy flag, or -1
JIF neg r0, stay
MOV r6, r1           ; the enemy's row
SELF                 ; r0 x, r1 y, r3 energy
SUB r3, 2
JIF neg r3, rest
SUB r6, r1           ; dy to the enemy's edge
JIF zero r6, stay
SIGN r6
MOV r2, r1
ADD r2, r6           ; the row in front of me
MAP r0, r2           ; r0 = what my army knows stands there
SUB r0, 2
JIF zero r0, stay    ; one of mine: wait for it
JIF pos r6, south
MOVE north
HALT
south: MOVE south
HALT
stay: HOLD
HALT
rest: SLEEP 1
