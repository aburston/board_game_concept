#!/bin/bash

# find the path to this script
SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

# set the python path
export PYTHONPATH=$PYTHONPATH:$SCRIPTPATH/..

# check expect is installed
if ! expect -v >/dev/null; then
	echo "expect must be installed to run tests"
	exit 1
fi

# check dos2unix is installed
if ! dos2unix --version >/dev/null; then
	echo "dos2unix must be installed to run tests"
	exit 1
fi

# clear the test log
rm -f test.log

echo "Testing board_game_concept"
for i in *.expect; do 
	echo "Running test $i"
	echo "****************************************" >> test.log
	echo "Executing test: $i" >> test.log
	echo "****************************************" >> test.log
	expect -c "set timeout 2" -f $i 2>&1 >> test.log
	echo >> test.log
done
dos2unix test.log
echo "Test run complete, see test.log for results."

