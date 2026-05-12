# board_game_concept
Board game idea based on building and programming your own units

 * Create your own units based on simple rules
 * Program each unit to play the game
 * Run the game automatically resolving the winner
 * Win condition = last player with a functional unit
 
# server idea

 * The server runs permanently, and automatically commits whenever all the players commit
 * The players should pause after their commit and wait for the server to commit
 * Currently the server runs and waits for files to be created and written into a directory on disk by the
player client.

# web service - [TODO]
 * combine server, client and observer into different roles in the API based on login
 * create "flask" based web service that exposes all the cli based commands as a RESTful API
 * backend would still be files for now, although moving to sqlite may be a thought via a common data class

# dependencies

  * Install expect on ubuntu 24.04 using `sudo apt-get install expect`
  * Install dos2unix on ubuntu 24.04 using `sudo apt-get install dos2unix`
  * Install pip on ubuntu 24.04 using `sudo apt-get install python3-pip`
  * Install venv on ubuntu 24.04 using `sudo apt-get install python3.12-venv`
  * Then create the venv in `board_game_concept` using `python3 -m venv .venv`
  * Then activate the venv `source .venv/bin/activate`
  * https://pypi.org/project/board using `pip install board`
  * pyaml `pip install pyaml`
  * pytest using `pip install pytest`
  * To run the new pytest suite from the project root:
    * `pytest`
    * `pytest tests/test_basic.py`
  * Core library source is now located in `src/`.
  * Legacy expect-based shell tests and `test/test.sh` have been removed; the Python tests now cover the same behavior.

# Console scripts

After installation, the package exposes these console scripts:

  * `board-game-client` → runs the player client interface
  * `board-game-server` → runs the game server/admin interface
  * `board-game-observer` → runs the neutral game observer
  * `board-game-test-suite` → runs the standalone package test harness

# TODO

  * add and `initgame.py` script to do the initial setup of the game, strip that    out of the server
  * separate all the DB storage out of the `GameData.py` class and rename,
    create dedicated objects for data returned from the DB.

  
Note to check my clone... -R

