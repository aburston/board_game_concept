#!/bin/bash

./client.py 001 5 5
add player 1 test1 test1@test.com password1
add player 2 test2 test2@test.com password2
commit
exit

./client.py 001 1 password1
add type scout s 1 0 50
add type warrior w 1 1 100
add unit scout s0 2 0
add unit warrior w0 2 1
commit
exit

./client.py 001 2 password2
add type scout s 1 0 50
add type warrior w 1 1 100
add unit scout s0 2 4
add unit warrior w0 2 3
commit
exit

./game.py 001

list
commit
show
list

./client.py 001 1 password1
show
move s0 s
move w0 s
list
commit
exit
